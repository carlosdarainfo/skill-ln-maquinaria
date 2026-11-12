"""Renderiza un reel de LN: montar (corte, subtítulos, mezcla) -> volumen a -14 LUFS (solo ganancia) -> imagen -> unir.

Uso:
  python renderizar.py "<carpeta del video>"            preview liviano 540x960 -> edicion/preview.mp4
  python renderizar.py "<carpeta del video>" --final    final 1080x1920, 30 fps -> Final/<nombre>.mp4
      [--nombre ln-maquinaria-video-2]                  nombre del archivo final (por defecto, el de la carpeta)

Siempre se aprueba primero el preview y después se saca el final.
"""
import argparse, json, re, subprocess, sys, time
from pathlib import Path
from comun import rutas, preparar_fuentes, ruta_filtro

AQUI = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--final", action="store_true")
ap.add_argument("--nombre")
args = ap.parse_args()
R = rutas(args.video)
T = R["trabajo"]
if args.final:
    W, H, CRF, AK = 1080, 1920, "18", "192"
    R["final"].mkdir(exist_ok=True)
    nombre = args.nombre or re.sub(r"[^a-z0-9]+", "-", f"ln-maquinaria-{R['clips'].name}".lower()).strip("-")
    OUT = R["final"] / f"{nombre}.mp4"
else:
    W, H, CRF, AK = 540, 960, "28", "96"
    OUT = R["edicion"] / "preview.mp4"
t0 = time.time()


def correr(cmd, **kw):
    r = subprocess.run(cmd, **kw)
    if r.returncode:
        sys.exit(f"Falló: {' '.join(map(str, cmd[:3]))}...")
    return r


print("1/4 Montando corte, subtítulos y audio...", flush=True)
correr([sys.executable, str(AQUI / "montar.py"), str(R["clips"])])

print("2/4 Normalizando el volumen a -14 LUFS...", flush=True)
cruda, mezcla = T / "mezcla_cruda.wav", T / "mezcla.wav"
med = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(cruda), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                      "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8").stderr
m = json.loads(med[med.rindex("{"):med.rindex("}") + 1])
af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
      f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
correr(["ffmpeg", "-v", "error", "-y", "-i", str(cruda), "-af", af, "-c:a", "pcm_s16le", str(mezcla)])

print(f"3/4 Componiendo la imagen ({W}x{H})... esto es lo que más tarda", flush=True)
fuentes = preparar_fuentes(T)
solo = T / "video_solo.mp4"
correr([sys.executable, str(AQUI / "imagen.py"), str(R["clips"]), str(solo), str(W), str(H), CRF, str(T / "subtitulos.ass"), str(fuentes)])

print("4/4 Uniendo imagen y audio...", flush=True)
correr(["ffmpeg", "-v", "error", "-y", "-i", str(solo), "-i", str(mezcla), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1",
        "-c:a", "aac", "-b:a", f"{AK}k", "-movflags", "+faststart", str(OUT)])
print(f"Listo en {time.time() - t0:.0f} s: {OUT}")
