"""Transcribe los clips de un video con Whisper (faster-whisper) y saca el tiempo de cada palabra.

Uso: python transcribir.py "<carpeta del video>" [--modelo large-v3-turbo] [--todos]

- Por defecto transcribe solo los clips con nombre de número (1.MOV, 2.MOV...), que son los de quien habla.
  Con --todos transcribe también los de apoyo.
- Escribe edicion/transcripcion.json (datos) y edicion/transcripcion.md (para leer y armar el plan).
- Los tiempos de inicio de palabra se corrigen (+0,10 s) porque Whisper los marca antes de tiempo;
  así los subtítulos y los efectos caen cuando arranca la palabra. Si en el preview algo se ve
  adelantado o atrasado, se ajusta el tiempo a mano en video.json.

Nota técnica: no se le pasa la ruta del archivo a Whisper (la versión de PyAV choca con faster-whisper);
se decodifica el audio con ffmpeg a 16 kHz mono y se le pasa el arreglo de numpy.
"""
import argparse, json, subprocess
import numpy as np
from comun import rutas, videos, duracion

SR = 16000
PISTA = ("LN Maquinaria, Husqvarna, Barnes, giro cero, Girozero, motobomba, guadaña, motosierra, tractor, "
         "Cundinamarca, Boyacá, Tolima, Meta, Kawasaki, Kohler, Ecopetrol.")


def audio(ruta):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), "-map", "0:a:0", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


# Whisper marca el inicio de las palabras ~0,13 s antes de cuando se oyen. Medido contra los 61 tiempos
# afinados a mano del Video 1: corriendo +0,10 s el error medio baja de 0,13 s a 0,06 s.
CORRECCION = 0.10


def afinar(t, fin):
    return round(min(t + CORRECCION, max(fin - 0.05, t)), 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--modelo", default="large-v3-turbo")
    ap.add_argument("--todos", action="store_true")
    args = ap.parse_args()
    R = rutas(args.video)
    clips = [v for v in videos(R["clips"]) if args.todos or v.stem.isdigit()]
    if not clips:
        raise SystemExit("No hay clips con nombre de número (1.MOV, 2.MOV...). Renómbralos en orden o usa --todos.")

    from faster_whisper import WhisperModel
    print(f"Cargando Whisper {args.modelo} (la primera vez se descarga, ~1,5 GB)...", flush=True)
    modelo = WhisperModel(args.modelo, device="auto", compute_type="int8")

    datos, md = {}, ["# Transcripción", "", "Tiempos en segundos desde el inicio de cada clip (ya afinados).", ""]
    for v in clips:
        print(f"Transcribiendo {v.name}...", flush=True)
        x = audio(v)
        segs, _ = modelo.transcribe(x, language="es", word_timestamps=True, initial_prompt=PISTA, vad_filter=False)
        palabras = []
        for s in segs:
            for w in s.words or []:
                p = w.word.strip()
                if p:
                    palabras.append({"p": p, "ini": round(w.start, 2), "fin": round(w.end, 2), "prob": round(w.probability, 2)})
        for w in palabras:
            w["ini"] = afinar(w["ini"], w["fin"])
        datos[v.stem] = {"archivo": v.name, "duracion": round(duracion(v), 2), "palabras": palabras}
        md += [f"## Clip {v.stem} ({v.name}, {datos[v.stem]['duracion']} s)", "",
               "> " + " ".join(w["p"] for w in palabras), "",
               "| ini | fin | palabra | seguridad |", "|---|---|---|---|"]
        md += [f"| {w['ini']:.2f} | {w['fin']:.2f} | {w['p']} | {'⚠ ' if w['prob'] < 0.6 else ''}{w['prob']} |" for w in palabras]
        md.append("")
    (R["edicion"] / "transcripcion.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    (R["edicion"] / "transcripcion.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Listo: {R['edicion'] / 'transcripcion.md'}")


if __name__ == "__main__":
    main()
