"""Saca una hoja de miniaturas por clip (un cuadro cada 1 s, en orden) para que Claude vea el material
y decida encuadres, centros de zoom y qué segundo usar de cada video de apoyo.

Uso: python miniaturas.py "<carpeta del video>" [--cada 1]
Resultado: edicion/miniaturas/<clip>.jpg  (cuadrícula de 6 columnas; la casilla k es el segundo k*cada)
"""
import argparse, math, subprocess
from comun import rutas, videos, es_hdr, duracion

TONEMAP = "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--cada", type=float, default=1.0)
args = ap.parse_args()
R = rutas(args.video)
out = R["edicion"] / "miniaturas"
out.mkdir(exist_ok=True)
for v in videos(R["clips"]):
    n = max(1, math.ceil(duracion(v) / args.cada))
    filas = math.ceil(n / 6)
    vf = f"fps=1/{args.cada}," + (TONEMAP + "," if es_hdr(v) else "") + f"scale=240:-2,tile=6x{filas}:padding=4:color=white"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-vf", vf, "-frames:v", "1", "-q:v", "4", str(out / f"{v.stem}.jpg")], check=True)
    print(f"{v.name}: {n} cuadros (uno cada {args.cada:g} s) -> miniaturas/{v.stem}.jpg")
