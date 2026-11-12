"""Monta la imagen del reel de LN Maquinaria: pantalla completa, video de apoyo y pantalla dividida,
zooms cinematográficos y transiciones de Crazy Kids (destello con clic, zoom y barrido).

Uso: imagen.py <carpeta del video> <salida.mp4> <ancho> <alto> <crf> <subtitulos.ass|-> <fontsdir|->
(normalmente lo llama renderizar.py; lee edicion/trabajo/plan.json, que genera montar.py)
Color original: los clips en HDR (HLG, los .MOV del iPhone) se pasan a SDR con tonemap hable, sin más ajustes;
los que ya son SDR bt709 no se tocan. Se compone siempre a 1080x1920 y al final se escala.
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image
from comun import rutas, buscar_clip, es_hdr

VIDEO, SALIDA, OW, OH, CRF, ASS, FUENTES = sys.argv[1:8]
R = rutas(VIDEO)
W, H = 1080, 1920
PLAN = json.load(open(R["trabajo"] / "plan.json", encoding="utf-8"))
FPS, CY = PLAN["fps"], PLAN["corte_y"]
COLOR = "in_color_matrix=bt709:out_color_matrix=bt709:in_range=tv:out_range=tv"
TONEMAP = "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"


_hdr = {}


def hdr(p):
    if p not in _hdr:
        _hdr[p] = es_hdr(p)
    return _hdr[p]


def lector(ruta, ss, dur, hdr):
    """Fotogramas RGB (autorrotados) desde ss durante dur segundos."""
    vf = f"fps={FPS},{TONEMAP + ',' if hdr else ''}scale=iw:ih:{COLOR},format=rgb24"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}", "-t", f"{dur + 0.5:.3f}", "-i", ruta,
                          "-map", "0:v:0", "-vf", vf, "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:stream_side_data=rotation",
                         "-of", "json", ruta], capture_output=True, text=True)
    s = json.loads(pr.stdout)["streams"][0]
    w, h = s["width"], s["height"]
    if any(abs(sd.get("rotation", 0)) == 90 for sd in s.get("side_data_list", [])):
        w, h = h, w
    tam = w * h * 3
    ultimo = None
    try:
        while True:
            b = p.stdout.read(tam)
            if len(b) < tam:
                break
            ultimo = Image.frombuffer("RGB", (w, h), b, "raw", "RGB", 0, 1)
            yield ultimo
        while ultimo is not None:   # si el video de apoyo se acaba, se congela el último cuadro
            yield ultimo
    finally:
        p.kill()
        p.wait()


CURVAS = {
    "lin": lambda u: u,
    "suave": lambda u: u * u * (3 - 2 * u),
    "entra": lambda u: u ** 3,
    "sale": lambda u: 1 - (1 - u) ** 3,
}


def escala(c, t):
    kf = c["zoom"]
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, z0, _), (t1, z1, curva) in zip(kf, kf[1:]):
        if t <= t1:
            return z0 + (z1 - z0) * CURVAS[curva]((t - t0) / (t1 - t0))
    return kf[-1][1]


def recorte(img, ow, oh, z, cx, cy, fijo=True):
    """Recorta img para llenar ow x oh con zoom z. fijo: el punto (cx,cy) queda quieto; si no, queda centrado."""
    iw, ih = img.size
    s = max(ow / iw, oh / ih) * z
    w, h = ow / s, oh / s
    if fijo:
        x0, y0 = cx * iw - cx * w, cy * ih - cy * h
    else:
        x0, y0 = cx * iw - w / 2, cy * ih - h / 2
    x0 = min(max(x0, 0), iw - w)
    y0 = min(max(y0, 0), ih - h)
    return np.asarray(img.resize((ow, oh), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h)), dtype=np.float32)


def capa(c, t):
    actual = c["capas"][0]
    for cp in c["capas"]:
        if cp[0] <= t + 1e-6:
            actual = cp
    return actual


def componer(c, hab, apoyo, n):
    """Fotograma n del clip c. Si el zoom cambia rápido, promedia sub-cuadros (desenfoque de movimiento)."""
    t0, t1 = n / FPS, (n + 1) / FPS
    cp = capa(c, t0)
    zs = [escala(c, t0 + (t1 - t0) * (k + 0.5) / 8) for k in range(8)]
    if max(zs) / min(zs) < 1.006:
        zs = [zs[4]]
    cx, cy = c["centro"]
    acum = np.zeros((H, W, 3), np.float32)
    for z in zs:
        if cp[1] == "full":
            f = recorte(hab, W, H, z, cx, cy)
        elif cp[1] == "apoyo":
            f = recorte(apoyo, W, H, z, 0.5, cp[4], fijo=False)
        else:
            arriba = recorte(apoyo, W, CY, 1.0 + 0.06 * min(1.0, (t0 - cp[0]) / 3.0), 0.5, cp[4], fijo=False)
            abajo = recorte(hab, W, H - CY, z, cx, cy)
            f = np.concatenate([arriba, abajo], axis=0)
        acum += f
    return acum / len(zs)


def suave(u):
    return u * u * u * (u * (6 * u - 15) + 10)


def barrido(a, b, f0, f1, signo, sub=14):
    tira = np.concatenate([a, b] if signo > 0 else [b, a], axis=1)
    acum = np.zeros_like(a)
    for k in range(sub):
        u = suave(f0 + (f1 - f0) * (k + 0.5) / sub)
        x = int(round(u * W)) if signo > 0 else int(round((1 - u) * W))
        acum += tira[:, x: x + W]
    return acum / sub


def destello(f, fuerza):
    return f + (255 - f) * fuerza


class Clip:
    """Lectores sincronizados de quien habla y de los videos de apoyo de un clip."""

    def __init__(self, c):
        self.c = c
        dur = c["cuadros"] / FPS
        p = buscar_clip(R["clips"], c.get("archivo", c["n"]))
        self.hab = lector(str(p), c["ini"], dur, hdr(p))
        self.apoyos = {}
        for cp in c["capas"]:
            if len(cp) > 2:
                p = buscar_clip(R["clips"], cp[2])
                self.apoyos[cp[0]] = lector(str(p), cp[3], dur - cp[0], hdr(p))

    def cuadro(self, n):
        h = next(self.hab)
        cp = capa(self.c, n / FPS)
        a = next(self.apoyos[cp[0]]) if cp[0] in self.apoyos else None
        return componer(self.c, h, a, n)

    def cerrar(self):
        for g in [self.hab, *self.apoyos.values()]:
            g.close()


def primero(c):
    k = Clip(c)
    f = k.cuadro(0)
    k.cerrar()
    return f


vf = []
if ASS != "-":
    ruta = ASS.replace("\\", "/").replace(":", r"\:")
    vf.append(f"ass='{ruta}'" + (f":fontsdir='{FUENTES.replace(chr(92), '/').replace(':', chr(92) + ':')}'" if FUENTES != "-" else ""))
vf.append(f"scale={OW}:{OH}:flags=lanczos:{COLOR}")
vf.append("format=yuv420p")
enc = subprocess.Popen(
    ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
     "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "medium", "-crf", CRF, "-pix_fmt", "yuv420p",
     "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", SALIDA],
    stdin=subprocess.PIPE,
)

DESTELLO_SALE, DESTELLO_ENTRA, DESTELLO_CAPA = [0.25, 0.6], [0.85, 0.45, 0.18, 0.05], [0.55, 0.22, 0.06]
total, ultimo = 0, None
clips = PLAN["clips"]
for i, c in enumerate(clips):
    entrada = clips[i - 1].get("salida") if i else None
    salida = c.get("salida")
    siguiente = primero(clips[i + 1]) if salida and salida["tipo"] == "barrido" else None
    cambios = [round(cp[0] * FPS) for cp in c["capas"][1:]]
    k = Clip(c)
    f = None
    for n in range(c["cuadros"]):
        f = k.cuadro(n)
        out = f
        resto = c["cuadros"] - 1 - n
        if salida and salida["tipo"] == "destello" and resto < len(DESTELLO_SALE):
            out = destello(f, DESTELLO_SALE[len(DESTELLO_SALE) - 1 - resto])
        elif entrada and entrada["tipo"] == "destello" and n < len(DESTELLO_ENTRA):
            out = destello(f, DESTELLO_ENTRA[n])
        elif salida and salida["tipo"] == "barrido" and n >= c["cuadros"] - salida["cuadros"] // 2:
            N = salida["cuadros"]
            j = n - (c["cuadros"] - N // 2)
            out = barrido(f, siguiente, j / N, (j + 1) / N, salida["signo"])
        elif entrada and entrada["tipo"] == "barrido" and n < entrada["cuadros"] - entrada["cuadros"] // 2:
            N = entrada["cuadros"]
            j = N // 2 + n
            out = barrido(ultimo, f, j / N, (j + 1) / N, entrada["signo"])
        else:
            for cn in cambios:   # cambio de encuadre dentro del clip: destello corto (va con clic)
                if 0 <= n - cn < len(DESTELLO_CAPA):
                    out = destello(f, DESTELLO_CAPA[n - cn])
        enc.stdin.write(np.clip(out + 0.5, 0, 255).astype(np.uint8).tobytes())
    k.cerrar()
    ultimo = f
    total += c["cuadros"]
    print(f"clip {c['n']} listo", flush=True)
enc.stdin.close()
enc.wait()
print("listo:", total, "fotogramas =", round(total / FPS, 3), "s", flush=True)
