# Edición de reels de LN (método aprobado por Carlos)

Es el mismo método con el que se hizo y aprobó el **Video 1** (club de Ecopetrol, tractor Husqvarna Z560X, 38 s). Los scripts están en la carpeta `edicion/` de esta skill. Antes de la primera edición en un computador, corre `python edicion/verificar.py` y arregla lo que diga FALTA (ver `INSTALAR.md`).

## El estilo (no cambiarlo sin que Mauricio o Carlos lo pidan)

- **Tono serio.** Sin canción ni música de fondo. Solo la voz original y efectos cortos: clic de obturador con destello, impacto grave, zoom (aspiración) y whooshes.
- **Color original.** Los .MOV del iPhone vienen en HDR (HLG): se pasan a SDR con tonemap *hable*, sin más ajustes. Los videos SDR se dejan como vienen. Los scripts lo detectan solos.
- **Voz original.** Solo se iguala el volumen entre clips y se normaliza a -14 LUFS. Sin reducción de ruido ni compresión.
- **Gancho (primer clip):** título en MAYÚSCULAS, Montserrat Black, blanco con borde negro, en la parte de abajo del video de arriba, justo sobre la línea divisoria. La palabra que suena va en **naranja Husqvarna #F36F21**. No va arriba en el cielo ni todo en naranja.
- **Desde el clip 2: subtítulos tipo Instagram.** Blancos, en minúsculas normales (como se habla), sombra suave, las palabras aparecen una a una, máximo 2 líneas por frase. Letra SF Pro Text Semibold si está instalada; si no, Montserrat SemiBold (viene con la skill).
- **Pantalla dividida:** el video de apoyo va arriba (franja de 760 px) y quien habla abajo, encuadrado desde arriba del plano.
- **Formato final:** 1080x1920, 30 fps, H.264 CRF 18, audio AAC 192k.

## El flujo, paso a paso

Cada video tiene su carpeta (por ejemplo `Contenido 2026/Video 2/`) con los clips crudos:
- **Quien habla:** nómbralos en orden `1.MOV`, `2.MOV`, `3.MOV`… (una toma por frase o idea).
- **Apoyo (b-roll):** cualquier nombre que diga qué es: `tractor girando.MP4`, `antes.MP4`.

Si Mauricio te da los clips con otros nombres, propón cómo renombrarlos y espera su sí.

### 1. Ver y escuchar el material

```bash
python "<skill>/edicion/transcribir.py" "<carpeta del video>"
python "<skill>/edicion/miniaturas.py" "<carpeta del video>"
```

- `edicion/transcripcion.md`: el texto de cada clip con el segundo exacto de cada palabra. Las de seguridad baja salen con ⚠: confírmalas con Mauricio (marcas, modelos, nombres).
- `edicion/miniaturas/<clip>.jpg`: una cuadrícula con un cuadro por segundo (casilla 0 = segundo 0). Ábrelas para ver encuadres y escoger qué segundo usar de cada apoyo.

### 2. Proponer el corte (antes de tocar nada)

Muéstrale a Mauricio una tabla corta: clip, desde–hasta (s), qué dice, encuadre (completa / apoyo / dividida y con qué apoyo), transición de salida. Quita muletillas, tomas repetidas y silencios: el clip arranca ~0,05 s antes de la primera palabra y termina ~0,2 s después de la última. Espera su ok.

### 3. Escribir `edicion/video.json`

Copia `edicion/ejemplo-video-1.json` como modelo. Campos:

| Campo | Qué es |
|---|---|
| `cortes[]` | Un elemento por clip de quien habla, en el orden del video. |
| `n` | Número del clip (= nombre del archivo `n.MOV`). Si el archivo se llama distinto, agrega `"archivo": "nombre"`. |
| `ini`, `fin` | Segundos del clip original que se usan. |
| `centro` | Punto [x, y] (0 a 1) de quien habla que el zoom mantiene quieto. La cara suele estar en [0.5, 0.25–0.35]. |
| `zoom` | Lista de `[t, escala, curva]`: en el segundo `t` (contado desde `ini`) la escala llega a ese valor. Curvas: `lin`, `suave`, `entra` (acelera), `sale` (frena). 1.0 = sin zoom. |
| `capas` | Lista de `[t, modo, apoyo, segundo_del_apoyo, centro_y]`. Modos: `full` (solo quien habla), `apoyo` (solo el video de apoyo en pantalla completa), `dividida` (apoyo arriba, quien habla abajo). `full` no lleva más datos. |
| `salida` | Transición al siguiente clip: `{"tipo": "destello"}`, `{"tipo": "zoom"}` o `{"tipo": "barrido", "cuadros": 9, "signo": 1}` (signo 1 o -1 = dirección). El último clip no lleva. |
| `gancho` | Solo el primer clip: `clip`, `lineas` = `[texto, [tiempo de cada palabra]]`. En el texto, `/` es salto de línea y no cuenta como palabra. |
| `frases` | Por clip (desde el 2): lista de `[frase, [tiempo de cada palabra]]`. Mismo número de tiempos que de palabras. Cada frase cabe en 2 líneas; si no, pártela. |
| `efectos` | `"auto"` (los pone solos según transiciones y cambios de capa) o una lista como la del ejemplo. |

Los tiempos de palabra se copian de `transcripcion.md` (son segundos del clip original, no del video final). Ojo: Whisper suele marcar **la primera palabra de cada clip** hasta 0,2–0,3 s antes de cuando se oye; usa para ella el `fin` de esa palabra menos ~0,25 s, o revísala en el preview.

**Recetas que funcionaron en el Video 1:**
- Zoom lento de fondo: de 1.0 a 1.06–1.12 a lo largo del clip con curva `suave`.
- Golpe de zoom en una palabra clave ("giro cero", "Kawasaki", "garantía"): sube a 1.2–1.25 en 0,13 s con `sale`, sostiene y vuelve. Va con un `clic`.
- Transición `zoom`: el clip que sale sube a 1.9 en 0,25 s con `entra`; el que entra empieza en 1.9 y baja con `sale` en 0,25 s.
- Cambio a pantalla dividida cuando se nombra algo que se puede mostrar (la cancha, el operario).
- Alternar transiciones: destello → zoom → barrido → destello… no repetir la misma dos veces seguidas.
- Cierre (llamado a la acción) con un `impacto` en la última palabra ("mensaje").

**Efectos manuales** (si no usas `"auto"`): `{"sonido": "clic", "corte": 3, "adelanto": 0.012, "db": -8}` suena en el corte de entrada al clip 3; `{"sonido": "clic", "en": [4, 2.88], "adelanto": 0.01, "db": -12}` suena en el segundo 2,88 del clip 4 original; `"termina": true` hace que el sonido termine justo en el corte (para `zoom`). Sonidos: `clic`, `impacto`, `zoom`, `whoosh1`, `whoosh2`. Volúmenes típicos: clic -8 a -12 dB, impacto -7 a -18, whoosh -13 a -16, zoom -10.

### 4. Preview liviano

```bash
python "<skill>/edicion/renderizar.py" "<carpeta del video>"
```

Sale `edicion/preview.mp4` (540x960). Tarda unos minutos: córrelo en segundo plano si puedes. Ábrelo o compártelo con Mauricio (si tu Claude puede publicar un artifact, súbelo ahí con el MP4 como archivo aparte). Pregunta qué cambiar y ajusta solo `video.json`.

### 5. Final

Cuando Mauricio diga que está aprobado:

```bash
python "<skill>/edicion/renderizar.py" "<carpeta del video>" --final --nombre ln-maquinaria-video-2-<tema>
```

Sale en `<carpeta del video>/Final/`. Dale la ruta de la carpeta. Recuerda que Carlos aprueba la pieza antes de pautarla.

### 6. Guardar

En `CONTEXTO-LN.md`: qué video se hizo, ruta del final, qué pidió cambiar Mauricio (si es una preferencia nueva, guárdala también en `memoria/`).

## Si algo falla

- `No encuentro el clip 'X'`: el nombre en `video.json` no coincide con el archivo. Revisa mayúsculas y extensión.
- `tiene N palabras y M tiempos`: una frase de `frases` o del gancho tiene distinto número de palabras que de tiempos. Ojo con los signos sueltos (¿ ? ,) pegados a una palabra: cuentan como parte de ella.
- `ocupa más de 2 líneas`: parte la frase en dos.
- Error de PyAV / `metadata_errors` con Whisper: usa `transcribir.py` (ya decodifica con ffmpeg y le pasa el audio en memoria).
- La letra de los subtítulos sale en Arial: falta la fuente; corre `verificar.py`.
- `zscale` no existe: ffmpeg no es la versión completa (ver `INSTALAR.md`).
- Los sonidos se pueden regenerar con `python edicion/sonidos.py edicion/sonidos` (son propios, sin derechos de terceros).
