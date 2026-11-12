"""Utilidades compartidas por los scripts de edición de LN Maquinaria.

Estructura de un video:
    <carpeta del video>/            clips crudos: 1.MOV, 2.MOV ... (quien habla) y los de apoyo (cualquier nombre)
    <carpeta del video>/edicion/    video.json (el plan), transcripcion.json/.md, miniaturas/, preview.mp4
    <carpeta del video>/edicion/trabajo/   archivos temporales del render
    <carpeta del video>/Final/      el MP4 final 1080x1920
"""
import json, os, shutil, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SONIDOS = AQUI / "sonidos"
FUENTES = AQUI / "fuentes"
EXT_VIDEO = {".mov", ".mp4", ".m4v", ".mkv", ".avi", ".webm"}

# Consola de Windows: que las tildes no rompan los print
for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8")
    except Exception:
        pass


def rutas(video_dir):
    v = Path(video_dir).resolve()
    if not v.is_dir():
        sys.exit(f"No existe la carpeta del video: {v}")
    r = {"clips": v, "edicion": v / "edicion", "trabajo": v / "edicion" / "trabajo",
         "config": v / "edicion" / "video.json", "final": v / "Final"}
    r["edicion"].mkdir(exist_ok=True)
    r["trabajo"].mkdir(exist_ok=True)
    return r


def videos(carpeta):
    return sorted([p for p in Path(carpeta).iterdir() if p.is_file() and p.suffix.lower() in EXT_VIDEO],
                  key=lambda p: (0, int(p.stem)) if p.stem.isdigit() else (1, p.stem.lower()))


def buscar_clip(carpeta, nombre):
    """Encuentra un clip por nombre exacto o por nombre sin extensión (sin importar mayúsculas)."""
    nombre = str(nombre)
    p = Path(carpeta) / nombre
    if p.is_file():
        return p
    for v in videos(carpeta):
        if v.stem.lower() == Path(nombre).stem.lower():
            return v
    sys.exit(f"No encuentro el clip '{nombre}' en {carpeta}")


def probe(ruta):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,color_transfer:stream_side_data=rotation:format=duration",
                          "-of", "json", str(ruta)], capture_output=True, text=True, encoding="utf-8").stdout
    return json.loads(out)


def es_hdr(ruta):
    """Los .MOV del iPhone vienen en HDR (HLG). Se detecta por la curva de transferencia."""
    s = probe(ruta).get("streams", [{}])[0]
    return s.get("color_transfer") in ("arib-std-b67", "smpte2084")


def duracion(ruta):
    return float(probe(ruta).get("format", {}).get("duration", 0))


def _carpetas_fuentes():
    c = [FUENTES]
    if os.name == "nt":
        c += [Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts", Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"]
    else:
        c += [Path.home() / "Library/Fonts", Path("/Library/Fonts"), Path("/System/Library/Fonts"), Path.home() / ".fonts", Path("/usr/share/fonts")]
    return [x for x in c if x.is_dir()]


def _buscar_fuente(archivos):
    for d in _carpetas_fuentes():
        for a in archivos:
            p = d / a
            if p.is_file():
                return p
    return None


def fuente_subtitulos():
    """Subtítulos tipo Instagram: SF Pro Text Semibold si está instalada; si no, Montserrat SemiBold (incluida).
    Devuelve (ruta del archivo, nombre para el .ass). Ojo: para SF Pro, libass necesita el nombre PostScript."""
    p = _buscar_fuente(["SF-Pro-Text-Semibold.otf", "SFProText-Semibold.otf"])
    if p:
        return p, "SFProText-Semibold"
    return FUENTES / "Montserrat-SemiBold.ttf", "Montserrat SemiBold"


def fuente_titulo():
    return FUENTES / "Montserrat-Black.ttf", "Montserrat Black"


def preparar_fuentes(trabajo):
    """Copia las fuentes usadas a trabajo/fuentes para pasárselas a ffmpeg (no hace falta instalarlas)."""
    d = Path(trabajo) / "fuentes"
    d.mkdir(exist_ok=True)
    for p, _ in (fuente_subtitulos(), fuente_titulo()):
        shutil.copy2(p, d / p.name)
    return d


def ruta_filtro(p):
    """Ruta escapada para usar dentro de un filtro de ffmpeg (ass=...)."""
    return str(p).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
