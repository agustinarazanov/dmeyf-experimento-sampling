# Método de trabajo

Vale para todos los experimentos del repo. Cada experimento vive en `experimentos/<nombre>/`. Depende solo de `comun/`
y de su propia carpeta, y se puede borrar sin romper a los demás. Si un cambio toca `comun/`, el mensaje del commit lo
dice y cada experimento activo anota en su bitácora si lo afecta.

## Etapas

Hipótesis, diseño, código, corridas, análisis, informe. Cada etapa:

1. Arranca en una sesión nueva de Claude Code, a partir de los artefactos de `openspec/` y de la bitácora del
   experimento.
2. Termina con una revisión en sesión limpia (una sesión nueva, un subagente `general-purpose` o un integrante que no la
   ejecutó), usando la lista de `docs/revision.md`. No se cierra con un ✗ abierto.
3. Se cierra en `docs/bitacora.md` del experimento con el formato de cierre: fecha, sesión, revisor, hallazgos,
   correcciones, tokens y devolución del tutor.

## Modelo por etapa

- Opus: hipótesis, diseño, revisiones e informe.
- Sonnet: código, tablas y tareas mecánicas.
- Fable: solo si una decisión de diseño lo amerita.

## Tokens

- Salidas largas a archivo, nunca al chat. Leerlas con `head`, `tail` o un resumen.
- Subagentes solo para búsquedas o revisiones sin contexto.
- Lo repetido va a scripts. Las corridas las hace la VM, no una conversación.
- `/clear` al cerrar cada etapa.
- Las etapas que no necesitan a una persona se corren con `scripts/etapa.sh` en vez de a mano.
- `comun/tokens.py` escribe el `ledger/tokens.csv` de cada experimento. Clasifica cada sesión según la etapa que declara
  la bitácora de algún experimento (o su `ledger/sesiones/costos.csv`); la que nadie declara va a `sampling_1` y si dos
  la declaran falla.
- Objetivo: menos de 100.000 tokens de contexto por turno. La línea de base de octubre ronda los 400.000.

## Agregar un experimento

1. Copiar `plantilla/` a `experimentos/<nombre>/`.
2. Completar `docs/hipotesis.md` (citando las reglas de `control`) y abrir la bitácora con la etapa hipótesis.
3. Declarar `## Dependencias` en `docs/diseno.md`: de qué experimentos lee (`control` como mínimo).
4. Registrar sus brazos y estudios en `comun/brazos.py` (brazo → dueño, método, tasa, estudio; estudio → dueño) y
   anunciarlo en el commit. `python -m comun.brazos --verificar` compara las dependencias declaradas con las que
   implica el registro, busca ciclos y lista qué se rompe si falta una carpeta.
5. Sumarlo a la tabla de experimentos del `README.md`.

Los pasos completos, con ejemplos, están en § Agregar una hipótesis.
