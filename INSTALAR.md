# Instalar la skill de LN en el computador de Mauricio

Tiempo: unos 30 minutos la primera vez (la mayor parte es descarga). Se hace una sola vez.

## 1. Claude

1. Instalar la app de escritorio de Claude (claude.ai/download) e iniciar sesión con la cuenta de Mauricio. Para editar videos hace falta la pestaña **Code** (Claude Code), que viene en la app y necesita un plan pago (Pro o Max).
2. En Windows, Claude Code usa **Git para Windows**. Si la app lo pide, instalarlo (git-scm.com o `winget install Git.Git`).
3. Crear la carpeta de trabajo, por ejemplo `Escritorio\LN Maquinaria`, y abrirla en la pestaña Code.

## 2. Claude en Chrome

1. En Chrome, instalar la extensión **Claude** desde la Chrome Web Store (la oficial, de Anthropic) e iniciar sesión con la misma cuenta.
2. Conectarla con la app de escritorio siguiendo lo que pide la extensión o la app (las pantallas cambian; leer lo que aparece).
3. Probar: en la pestaña Code pedirle "abre facebook.com/ads/library en Chrome". Si Chrome abre una pestaña nueva, quedó conectado.
4. Mauricio inicia sesión en Meta Business y TikTok **él mismo** en ese Chrome.

## 3. Instalar la skill

Pegarle esto a Claude en la pestaña Code (con la dirección del repositorio que da Carlos):

> Clona el repositorio `<URL-DEL-REPOSITORIO>` en la carpeta de skills de mi usuario (`%USERPROFILE%\.claude\skills\ln-maquinaria` en Windows, `~/.claude/skills/ln-maquinaria` en Mac). Después copia `plantillas/CLAUDE.md` y `plantillas/CONTEXTO-LN.md` a mi carpeta de trabajo de LN, crea la carpeta `memoria/` con un `MEMORIA.md` vacío y corre `python edicion/verificar.py` de la skill. Dime qué falta.

Si el repositorio es privado, Mauricio necesita una cuenta de GitHub con acceso (Carlos lo invita) y aceptar el inicio de sesión de GitHub cuando aparezca.

**Para actualizar** cuando Carlos mejore la skill: "actualiza la skill de LN" (Claude hace `git pull` en esa carpeta).

## 4. Herramientas para editar video

`verificar.py` dice qué falta. Lo normal en un Windows nuevo:

```bash
winget install Python.Python.3.12
```

```bash
winget install Gyan.FFmpeg
```

Cerrar y volver a abrir la terminal (o la app), y luego:

```bash
python -m pip install faster-whisper numpy pillow
```

Volver a correr `python edicion/verificar.py` hasta que diga "Todo listo para editar".

- La primera transcripción descarga el modelo de Whisper (~1,5 GB). Es una sola vez.
- **Fuente de los subtítulos:** con Montserrat SemiBold (incluida) ya funciona. Para el look idéntico a Instagram, instalar **SF Pro Text** desde developer.apple.com/fonts (opcional).
- En Mac: `brew install ffmpeg python` y lo mismo de pip.

## 5. Usarla también en el chat normal (opcional)

Para ganchos, guiones y estrategia desde claude.ai o el celular: en claude.ai → Configuración → Capacidades → Skills, subir esta carpeta comprimida en .zip. Ahí no se editan videos (eso solo en la pestaña Code del computador).

## 6. Prueba final

En la pestaña Code, dentro de la carpeta de LN:

> ¿Dónde quedamos con LN? Dame 5 ganchos para el tractor giro cero.

Claude debería leer `CONTEXTO-LN.md`, usar el método de Hormozi y, al final, guardar lo hecho en el contexto.
