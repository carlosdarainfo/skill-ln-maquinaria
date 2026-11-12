"""Sintetiza los sonidos del Video 2 (propios, sin derechos de terceros): whooshes, clic de cámara, impacto y zoom."""
import sys, wave
import numpy as np

SR = 48000
OUT = sys.argv[1]
rng = np.random.default_rng(7)


def guardar(nombre, x):
    x = x / np.abs(x).max() * 0.95
    pcm = (x * 32767).astype(np.int16)
    with wave.open(f"{OUT}/{nombre}.wav", "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())


def pasa_bajos(x, fc):
    """Filtro de un polo con frecuencia de corte variable en el tiempo."""
    fc = np.broadcast_to(fc, x.shape)
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    y = np.zeros_like(x)
    z = 0.0
    for i in range(len(x)):
        z += a[i] * (x[i] - z)
        y[i] = z
    return y


def sierra(f, t, fase):
    return 2 * ((f * t + fase) % 1) - 1


def reverb(x, seg=3.2, mezcla=0.3):
    n = int(seg * SR)
    t = np.arange(n) / SR
    salida = []
    for c in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * 2.4)
        ir = pasa_bajos(ir, 2200.0)
        ir /= np.sqrt((ir ** 2).sum())
        L = len(x) + n
        h = np.fft.irfft(np.fft.rfft(x[:, c], L) * np.fft.rfft(ir, L), L)
        seco = np.pad(x[:, c], (0, n))
        salida.append(seco + mezcla * h)
    return np.stack(salida, 1)


def whoosh(dur=0.62, pico=0.5, direccion=1):
    """Ruido con barrido de frecuencia que cruza de un lado a otro, con un golpe grave al final."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    u = t / dur
    forma = np.exp(-((u - pico) / 0.2) ** 2)
    fc = 160 + 5200 * forma
    r = rng.standard_normal(n)
    grave = pasa_bajos(r, fc)
    ruido = (grave - pasa_bajos(grave, fc * 0.22)) * forma
    pan = np.clip(0.5 + direccion * (u - pico) * 1.8, 0, 1)
    x = np.stack([ruido * np.cos(pan * np.pi / 2), ruido * np.sin(pan * np.pi / 2)], 1)
    x /= np.abs(x).max()
    tg = np.maximum(t - dur * pico, 0)
    thump = np.sin(2 * np.pi * np.cumsum(46 + 70 * np.exp(-tg * 30)) / SR) * np.exp(-tg * 11) * (t > dur * pico)
    x += 0.2 * thump[:, None]
    return reverb(x, seg=0.9, mezcla=0.14)


def tobogan(dur=0.8):
    """Pito de émbolo que baja, como deslizarse por un tobogán."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    u = t / dur
    f = 1500 * (420 / 1500) ** (u ** 1.3) * (1 + 0.012 * np.sin(2 * np.pi * 7 * t))
    fase = 2 * np.pi * np.cumsum(f) / SR
    env = np.minimum(t / 0.04, 1) * np.minimum((dur - t) / 0.12, 1)
    s = (np.sin(fase) + 0.14 * np.sin(2 * fase) + 0.015 * rng.standard_normal(n)) * env
    return reverb(np.stack([s, s], 1), seg=0.5, mezcla=0.1)


def toctoc(golpes=(0.0, 0.14, 0.28), dur=0.55):
    """Martillazos de madera, ligeros."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for i, t0 in enumerate(golpes):
        tg = np.maximum(t - t0, 0)
        on = t >= t0
        g = 1.0 if i < 2 else 1.25
        s += on * g * (np.sin(2 * np.pi * 640 * tg) * np.exp(-tg * 38) + 0.6 * np.sin(2 * np.pi * 1180 * tg) * np.exp(-tg * 60)
                       + 0.5 * pasa_bajos(rng.standard_normal(n), 3000.0) * np.exp(-tg * 170))
    return reverb(np.stack([s, s], 1), seg=0.35, mezcla=0.08)


def ding(dur=1.1):
    """Campanita clara."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(g * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, g, d in ((1568, 1.0, 4.5), (2349, 0.5, 6.0), (3136, 0.3, 8.0), (4186, 0.12, 11.0)))
    s = s * np.minimum(t / 0.002, 1)
    return np.stack([s, s], 1)




def clic(dur=0.25):
    """Obturador de cámara: dos chasquidos secos y brillantes."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    r = rng.standard_normal(n)
    agudo = r - pasa_bajos(r, 2500.0)
    s = np.zeros(n)
    for t0, g, d in ((0.0, 1.0, 320), (0.055, 0.7, 260)):
        tg = np.maximum(t - t0, 0)
        on = t >= t0
        s += on * g * (agudo * np.exp(-tg * d) + 0.5 * np.sin(2 * np.pi * 1900 * tg) * np.exp(-tg * 180))
    return reverb(np.stack([s, s], 1), seg=0.25, mezcla=0.06)


def impacto(dur=2.2):
    """Golpe cinematográfico: caída grave con cuerpo de ruido y cola larga."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 32 + 58 * np.exp(-t * 7)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    r = rng.standard_normal(n)
    cuerpo = pasa_bajos(r, 900.0 * np.exp(-t * 6) + 120) * np.exp(-t * 9)
    s = sub + 0.9 * cuerpo / np.abs(cuerpo).max()
    s *= np.minimum(t / 0.003, 1)
    return reverb(np.stack([s, s], 1), seg=2.4, mezcla=0.22)


def zoom(dur=0.55):
    """Aspiración que sube y se corta en seco: entra al zoom de transición."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    u = t / dur
    forma = u ** 2.5
    fc = 200 + 6500 * u ** 2
    r = rng.standard_normal(n)
    g = pasa_bajos(r, fc)
    s = (g - pasa_bajos(g, fc * 0.3)) * forma
    s[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))
    return np.stack([s, s], 1)


guardar("whoosh1", whoosh(direccion=1))
guardar("whoosh2", whoosh(dur=0.56, direccion=-1))
guardar("clic", clic())
guardar("impacto", impacto())
guardar("zoom", zoom())
