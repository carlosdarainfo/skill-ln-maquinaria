"""Arma el corte de un reel de LN a partir de edicion/video.json y genera en edicion/trabajo/:
plan.json (para imagen.py), subtitulos.ass y mezcla_cruda.wav.

Uso: python montar.py "<carpeta del video>"   (normalmente lo llama renderizar.py)

Método aprobado por Carlos (Video 1, Ecopetrol): color y voz originales, sin música. Gancho como título
Montserrat Black sobre la línea divisoria con la palabra que suena en naranja; desde el clip 2, subtítulos
tipo Instagram que aparecen palabra por palabra; clics, impactos, zoom y whooshes en los cortes.
El formato de video.json está explicado en referencias/edicion-video.md y hay un ejemplo en edicion/ejemplo-video-1.json.
"""
import json, subprocess, sys, wave
import numpy as np
from PIL import ImageFont
from comun import rutas, buscar_clip, fuente_subtitulos, fuente_titulo, SONIDOS

R = rutas(sys.argv[1])
if not R["config"].is_file():
    sys.exit(f"Falta el plan: {R['config']}")
CFG = json.load(open(R["config"], encoding="utf-8"))
SR = 48000
FPS = CFG.get("fps", 30)
CORTE_Y = CFG.get("corte_y", 760)          # pantalla dividida: arriba el apoyo (0..CORTE_Y), abajo quien habla
CORTE = CFG["cortes"]
for c in CORTE:
    c.setdefault("archivo", str(c["n"]))
    c.setdefault("centro", [0.5, 0.3])
    c.setdefault("zoom", [[0, 1.0, "lin"]])
    c.setdefault("capas", [[0, "full"]])
    c["cuadros"] = int(round((c["fin"] - c["ini"]) * FPS))
    c["fin"] = round(c["ini"] + c["cuadros"] / FPS, 4)
POR_N = {c["n"]: c for c in CORTE}
json.dump({"fps": FPS, "corte_y": CORTE_Y, "clips": CORTE}, open(R["trabajo"] / "plan.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

# ---------- Subtítulos ----------
SUB = CFG.get("subtitulos", {})
ADELANTO = SUB.get("adelanto", 0.03)
TAM, ANCHO_MAX = SUB.get("tamano", 50), SUB.get("ancho_max", 760)
Y_FULL, Y_DIV = SUB.get("y_completa", 1250), SUB.get("y_dividida", 1540)   # borde superior del texto
F_SUB, N_SUB = fuente_subtitulos()
F_TIT, N_TIT = fuente_titulo()
fuente = ImageFont.truetype(str(F_SUB), TAM)
GANCHO = CFG.get("gancho") or {}
G_CLIP = GANCHO.get("clip")
G_TAM = GANCHO.get("tamano", 74)
MARGEN_GANCHO = 1920 - (CORTE_Y - 22)     # borde inferior del título, 22 px sobre la línea divisoria
COLOR_G = GANCHO.get("color", "#F36F21")  # naranja Husqvarna
NARANJA = r"{\c&H" + COLOR_G[5:7] + COLOR_G[3:5] + COLOR_G[1:3] + "&}"
BLANCO = r"{\c&HFFFFFF&}"
FRASES = {int(k): v for k, v in CFG.get("frases", {}).items()}


def lineas(palabras):
    """Corta en líneas por ancho real (se fija una vez para que el texto no salte al ir apareciendo)."""
    out, cur = [], []
    for p in palabras:
        if cur and fuente.getlength(" ".join(cur + [p])) > ANCHO_MAX:
            out.append(cur)
            cur = []
        cur.append(p)
    out.append(cur)
    return out


def t_ass(t):
    cs = int(round(max(t, 0) * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


inicio, t = {}, 0.0
for c in CORTE:
    inicio[c["n"]] = t - c["ini"]     # tiempo en la línea final = inicio[n] + segundo del clip original
    t += c["cuadros"] / FPS
TOTAL = t


def modo_en(c, tl):
    m = c["capas"][0][1]
    for cap in c["capas"]:
        if cap[0] <= tl + 1e-6:
            m = cap[1]
    return m


eventos = []
for c in CORTE:
    n, off = c["n"], inicio[c["n"]]
    if n == G_CLIP:
        # Gancho: frase completa en blanco y la palabra que suena en naranja. "/" = salto de línea.
        L = GANCHO["lineas"]
        for gi, (texto, tiempos) in enumerate(L):
            toks = texto.split()
            assert len([x for x in toks if x != "/"]) == len(tiempos), ("gancho", texto)
            fin_g = L[gi + 1][1][0] if gi + 1 < len(L) else c["fin"]
            for i in range(len(tiempos)):
                a = tiempos[i] + off - ADELANTO
                b = (tiempos[i + 1] if i + 1 < len(tiempos) else fin_g) + off - ADELANTO
                txt, k = "", 0
                for tok in toks:
                    if tok == "/":
                        txt = txt.rstrip() + r"\N"
                        continue
                    txt += (NARANJA + tok + BLANCO if k == i else tok) + " "
                    k += 1
                eventos.append(f"Dialogue: 2,{t_ass(a)},{t_ass(b)},Titulo,,0,0,{MARGEN_GANCHO},,{txt.strip()}")
        continue
    for fi, (texto, tiempos) in enumerate(FRASES.get(n, [])):
        palabras = texto.split()
        assert len(palabras) == len(tiempos), f"Clip {n}: '{texto}' tiene {len(palabras)} palabras y {len(tiempos)} tiempos"
        ls = lineas(palabras)
        assert len(ls) <= 2, f"Clip {n}: '{texto}' ocupa más de 2 líneas; pártela en dos frases"
        sig = FRASES[n][fi + 1][1][0] if fi + 1 < len(FRASES[n]) else None
        fin_f = sig if sig else c["fin"]
        y = Y_DIV if modo_en(c, tiempos[0] - c["ini"] + 0.05) == "dividida" else Y_FULL
        for i in range(len(palabras)):
            a = tiempos[i] + off - ADELANTO
            b = (tiempos[i + 1] if i + 1 < len(palabras) else fin_f) + off - ADELANTO
            k, partes = 0, []
            for l in ls:
                vis = l[:max(0, i + 1 - k)]
                k += len(l)
                if vis:
                    partes.append(" ".join(vis))
            txt = r"\N".join(partes)
            eventos.append(f"Dialogue: 0,{t_ass(a)},{t_ass(b)},Sombra,,0,0,{y + 4},,{{\\blur7}}{txt}")
            eventos.append(f"Dialogue: 1,{t_ass(a)},{t_ass(b)},Sub,,0,0,{y},,{txt}")
cabecera = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{N_SUB},{TAM},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,60,60,0,1
Style: Sombra,{N_SUB},{TAM},&H8C000000,&H8C000000,&H8C000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,8,60,60,0,1
Style: Titulo,{N_TIT},{G_TAM},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,6,0,2,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
open(R["trabajo"] / "subtitulos.ass", "w", encoding="utf-8").write(cabecera + "\n".join(eventos) + "\n")


# ---------- Audio ----------
def leer(ruta, extra=(), mono=False):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ruta), *extra, "-f", "f32le", "-ac", "1" if mono else "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    return x.copy() if mono else x.reshape(-1, 2).copy()


def db(v):
    return 10 ** (v / 20)


# Voz original: sin filtros ni reducción de ruido; solo se iguala el volumen entre clips
voz = np.zeros(int(TOTAL * SR) + SR)
pos = 0
for c in CORTE:
    x = leer(buscar_clip(R["clips"], c["archivo"]), ("-map", "0:a:0"), mono=True)
    a, m = int(round(c["ini"] * SR)), int(round(c["cuadros"] / FPS * SR))
    x = x[a:a + m]
    if len(x) < m:
        x = np.pad(x, (0, m - len(x)))
    ven = 2400
    rms = np.array([np.sqrt((x[i:i + ven] ** 2).mean()) for i in range(0, len(x) - ven, ven)])
    habla = rms[rms > np.percentile(rms, 60)]
    x *= 0.10 / max(np.sqrt((habla ** 2).mean()), 1e-6)
    f = int(0.010 * SR)
    x[:f] *= np.linspace(0, 1, f)
    x[-f:] *= np.linspace(1, 0, f)
    voz[pos:pos + m] = x
    pos += m

mezcla = np.stack([voz, voz], 1)
_cache = {}


def fx(nombre):
    if nombre not in _cache:
        _cache[nombre] = leer(SONIDOS / f"{nombre}.wav")
    return _cache[nombre]


def poner(x, t0, gain=0.0):
    x = x * db(gain)
    a = int(round(t0 * SR))
    if a < 0:
        x, a = x[-a:], 0
    m = min(len(x), len(mezcla) - a)
    if m > 0:
        mezcla[a:a + m] += x[:m]


def efectos_auto():
    """Efectos por defecto según las transiciones y los cambios de encuadre (lo que se hizo en el Video 1)."""
    ef, w = [], 0
    for i, c in enumerate(CORTE[1:], 1):
        sal = CORTE[i - 1].get("salida", {}).get("tipo")
        if sal == "destello":
            ef += [{"sonido": "clic", "corte": c["n"], "adelanto": 0.012, "db": -8},
                   {"sonido": "impacto", "corte": c["n"], "db": -9}]
        elif sal == "zoom":
            ef += [{"sonido": "zoom", "corte": c["n"], "termina": True, "db": -10},
                   {"sonido": "whoosh2", "corte": c["n"], "adelanto": 0.28, "db": -16},
                   {"sonido": "impacto", "corte": c["n"], "db": -18}]
        elif sal == "barrido":
            ef.append({"sonido": "whoosh1" if w % 2 == 0 else "whoosh2", "corte": c["n"], "adelanto": 0.3, "db": -13})
            w += 1
    for c in CORTE:
        if c["n"] == G_CLIP:
            continue
        for cp in c["capas"][1:]:
            ef.append({"sonido": "clic", "en": [c["n"], c["ini"] + cp[0]], "adelanto": 0.01, "db": -12})
    return ef


EFECTOS = CFG.get("efectos", "auto")
if EFECTOS == "auto":
    EFECTOS = efectos_auto()
for e in EFECTOS:
    s = fx(e["sonido"])
    if "corte" in e:
        c = POR_N[e["corte"]]
        base = inicio[c["n"]] + c["ini"]          # instante del corte de entrada a ese clip
    else:
        n, tc = e["en"]
        base = inicio[n] + tc                     # segundo tc del clip original n
    t0 = base - (len(s) / SR if e.get("termina") else e.get("adelanto", 0))
    poner(s, t0, e.get("db", -12))
json.dump(EFECTOS, open(R["trabajo"] / "efectos_usados.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("total", round(TOTAL, 3), "s; cortes en", [round(inicio[c["n"]] + c["ini"], 3) for c in CORTE[1:]])

mezcla = mezcla[:int(round(TOTAL * SR))]
pcm = (np.clip(mezcla, -1, 1) * 32767).astype(np.int16)
with wave.open(str(R["trabajo"] / "mezcla_cruda.wav"), "wb") as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes(pcm.tobytes())
