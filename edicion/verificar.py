"""Revisa que el computador tenga todo para editar videos. Uso: python verificar.py"""
import importlib, shutil, subprocess, sys
from comun import fuente_subtitulos, SONIDOS, FUENTES

ok = True


def linea(bien, texto, arreglo=""):
    global ok
    ok &= bien
    print(("  OK   " if bien else "  FALTA ") + texto + ("" if bien else f"\n         -> {arreglo}"))


print(f"Python {sys.version.split()[0]} ({sys.executable})")
linea(sys.version_info >= (3, 10), "Python 3.10 o más nuevo", "Instala Python 3.12+: winget install Python.Python.3.12")
for mod, pip in (("numpy", "numpy"), ("PIL", "pillow"), ("faster_whisper", "faster-whisper")):
    try:
        importlib.import_module(mod)
        linea(True, f"módulo {pip}")
    except Exception:
        linea(False, f"módulo {pip}", f"python -m pip install {pip}")

ff = shutil.which("ffmpeg")
linea(bool(ff), "ffmpeg en el PATH", "winget install Gyan.FFmpeg   (y cierra y abre la terminal)")
if ff:
    filtros = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    for f in ("zscale", "tonemap", "ass", "loudnorm"):
        linea(f" {f} " in filtros, f"filtro {f} de ffmpeg", "Usa la versión 'full' de ffmpeg (winget install Gyan.FFmpeg)")
    enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    linea("libx264" in enc, "codificador libx264", "Usa la versión 'full' de ffmpeg (winget install Gyan.FFmpeg)")
linea(bool(shutil.which("ffprobe")), "ffprobe en el PATH", "Viene con ffmpeg")

for s in ("clic", "impacto", "zoom", "whoosh1", "whoosh2"):
    linea((SONIDOS / f"{s}.wav").is_file(), f"sonido {s}.wav", "Regenéralos: python sonidos.py sonidos")
for f in ("Montserrat-Black.ttf", "Montserrat-SemiBold.ttf"):
    linea((FUENTES / f).is_file(), f"fuente {f}", "Vuelve a bajar la skill (git pull)")
p, nombre = fuente_subtitulos()
print(f"  INFO subtítulos con: {nombre}" + ("" if "SF" in nombre else "  (para el look exacto de Instagram instala SF Pro Text de developer.apple.com/fonts; opcional)"))
print("\nTodo listo para editar." if ok else "\nArregla lo que dice FALTA y vuelve a correr este archivo.")
