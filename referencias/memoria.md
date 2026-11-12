# Cómo recordar todo (memoria en Markdown)

Claude no recuerda solo de una conversación a otra. Por eso todo lo importante se escribe en archivos Markdown dentro de la **carpeta de trabajo de LN** de Mauricio. Así cualquier conversación nueva arranca sabiendo dónde quedamos.

```
<carpeta de trabajo de LN>/
  CLAUDE.md            ← instrucciones que Claude lee solo al abrir la carpeta (copiado de plantillas/CLAUDE.md)
  CONTEXTO-LN.md       ← el documento vivo: dónde quedamos y qué sigue
  memoria/
    MEMORIA.md         ← índice: una línea por archivo
    palabras-del-cliente.md
    preferencias-de-mauricio.md
    campana-z560x.md
    ...
  Contenido/Video 1/, Video 2/ ...  ← un video por carpeta
```

## Al empezar cada conversación
1. Lee `CONTEXTO-LN.md` completo.
2. Lee `memoria/MEMORIA.md` y abre solo lo que tenga que ver con la tarea.
3. Si lo que dicen está viejo o se contradice con lo que Mauricio dice hoy, pregunta cuál vale y corrige el archivo.

## Al terminar cada tarea (sin que te lo pidan)
Actualiza `CONTEXTO-LN.md`:
- Cambia la fecha de "Última actualización".
- En "Dónde quedamos": el estado de hoy en 3–6 líneas.
- En "Próximos pasos": casillas `- [ ]` con lo que sigue y quién lo hace. Marca `- [x]` lo terminado.
- En "Historial": una línea con fecha y qué se hizo (y la ruta de lo que se creó).

## Qué va en `memoria/`
Un archivo por tema, con un título y la fecha. Guarda:
- **Decisiones** ("la campaña va solo en Marketplace", "no publicamos precios") con el porqué.
- **Datos del negocio** que Mauricio confirme (precio, margen, unidades, modelo, presupuesto, KPIs).
- **Preferencias de Mauricio o de Carlos** sobre cómo trabajar o cómo deben quedar las piezas (por ejemplo, "los subtítulos sin mayúsculas"). Incluye el porqué.
- **Palabras del cliente** sacadas de los chats de Liliana.
- **Resultados** de campañas (semana, gasto, mensajes, ventas, % de cierre).

Formato de cada archivo:

```markdown
# Título corto
Actualizado: AAAA-MM-DD

El dato o la decisión.

**Por qué:** …
**Cómo usarlo:** …
```

Y en `memoria/MEMORIA.md`, una línea por archivo: `- [Título](archivo.md) — de qué trata en pocas palabras`.

## Reglas
- Fechas siempre completas (2026-11-20), nunca "el jueves" o "ayer".
- Antes de crear un archivo, mira si ya hay uno del mismo tema y actualízalo.
- Si algo resultó falso, corrígelo o bórralo.
- **Nunca guardes contraseñas, códigos ni datos de tarjetas.**
- Si Mauricio dice "acuérdate de…", "guarda esto" o "de ahora en adelante…", guárdalo en ese momento y confírmale dónde.
