# Skill de LN Maquinaria para Claude

Todo lo que Carlos Araujo usa con Claude en el proyecto de LN Maquinaria, empaquetado para que Mauricio lo haga desde su propio Claude:

- **Editar reels** igual que el Video 1: Whisper para el tiempo de cada palabra, gancho en naranja Husqvarna, subtítulos tipo Instagram, zooms, pantalla dividida, clics e impactos, color y voz originales. Preview primero, final 1080x1920 después.
- **Ganchos, guiones y textos** de anuncios con las palabras reales del cliente.
- **Estrategia y ofertas** solo con el método de Alex Hormozi.
- **Montar y publicar anuncios** en Meta y TikTok con Claude en Chrome (siempre con confirmación) y dar accesos a Carlos.
- **Memoria en Markdown:** Claude lee y actualiza `CONTEXTO-LN.md` y `memoria/` para no perder el hilo.

| Archivo | Para qué |
|---|---|
| `SKILL.md` | Lo que Claude lee primero: reglas y a dónde ir según la tarea |
| `INSTALAR.md` | Instalación paso a paso (Claude, Chrome, la skill, Python y ffmpeg) |
| `GUIA-DE-PROMPTS.md` | Cómo pedirle las cosas a Claude |
| `referencias/` | Edición de video, Hormozi, ganchos, anuncios, negocio y memoria |
| `edicion/` | Scripts de video: `transcribir.py`, `miniaturas.py`, `renderizar.py`, `verificar.py` |
| `plantillas/` | `CLAUDE.md` y `CONTEXTO-LN.md` para la carpeta de trabajo |

Uso interno de LN Maquinaria. Las fuentes Montserrat van bajo la licencia SIL Open Font License (`edicion/fuentes/OFL.txt`). Los sonidos se generaron con `edicion/sonidos.py` y son propios.
