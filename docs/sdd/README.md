# Documentación SDD — Comparador d'Inventaris FARHOS ↔ KARDEX

Documentación *Spec Driven Development* de la aplicación Flask que concilia el inventario del
sistema de gestión farmacéutica **FARHOS** con el stock físico del almacén automatizado **KARDEX**.

**Estado:** as-built · refleja el código en `master` @ `52cf15c`
**Fecha:** 2026-09-08

---

## Los cuatro documentos

| Documento | Responde a | Cuándo leerlo |
|---|---|---|
| **[constitution.md](constitution.md)** | ¿Qué principios no se negocian? | Antes de proponer cualquier cambio de fondo |
| **[spec.md](spec.md)** | ¿QUÉ hace el sistema y POR QUÉ? | Para entender el comportamiento esperado sin leer código |
| **[plan.md](plan.md)** | ¿CÓMO está construido y qué se decidió? | Antes de tocar el código o el despliegue |
| **[tasks.md](tasks.md)** | ¿QUÉ está hecho y qué queda? | Al planificar el próximo trabajo |

### `constitution.md` — Principios rectores
8 artículos no negociables: herramienta de un solo caso de uso, contratos de datos explícitos,
corrección de datos por encima de la comodidad, separación proceso/presentación, interfaz en
catalán, seguridad proporcionada al entorno interno pero honesta sobre sus límites, despliegue
reproducible y cambios verificables. Incluye la tabla de **desviaciones vigentes aceptadas**.

### `spec.md` — Especificación funcional
Contexto del problema, actores, 8 escenarios de usuario, **65 requisitos funcionales**
(`FR-001`…`FR-065`) y **12 no funcionales** (`NFR-001`…`NFR-012`). Su sección más importante es
**§6 Contratos de datos**: la estructura real de los ficheros de FARHOS y KARDEX, verificada sobre
los ficheros del servidor. Cierra con fuera de ámbito, supuestos y 5 cuestiones abiertas.

### `plan.md` — Plan de implementación
Stack con versiones, arquitectura de componentes, los dos flujos principales (comparación y
exportación), diseño paso a paso del motor de datos mapeado a requisitos, **15 riesgos y deuda
técnica** (`R-01`…`R-15`), estrategia de verificación, despliegue y operación, y la tabla de
trazabilidad requisito → código.

### `tasks.md` — Tareas
**Parte A:** las 40 tareas ya construidas (`T001`…`T040`), reconstruidas del código y del historial.
**Parte B:** backlog en 4 fases — cerrar desviaciones constitucionales, verificabilidad, corrección
de datos, operación y robustez. Con trazabilidad riesgo → tarea y orden de ejecución recomendado.

---

## Cadena de trazabilidad

```
constitution.md   principios
       │
       ▼
    spec.md       FR-nnn / NFR-nnn ──────────┐
       │                                     │
       ▼                                     ▼
    plan.md       decisiones · R-nn      §10 trazabilidad requisito → código
       │
       ▼
   tasks.md       T-nnn ← trazado desde cada R-nn y cada cuestión abierta
```

Cada requisito del spec apunta a su ubicación en el código (`plan.md` §10). Cada riesgo y cada
cuestión abierta apuntan a la tarea que los resuelve (`tasks.md` §Trazabilidad).

## Cómo mantener esta documentación

1. **Cambio en la lectura de ficheros** → actualizar `spec.md` §6 (Contratos de datos) *en el mismo
   cambio*. Es obligación del Artículo II.3 de la constitución.
2. **Nuevo comportamiento observable** → nuevo `FR-nnn` en `spec.md` antes de implementarlo.
3. **Nueva decisión técnica o deuda asumida** → `plan.md` §7 (Riesgos) con su `R-nn`, y su tarea
   correspondiente en `tasks.md`.
4. **Cambio de un principio** → enmienda de `constitution.md` con subida de versión y justificación
   en el mensaje de commit.
5. **Trabajo completado** → marcar la tarea en `tasks.md` y actualizar la tabla de desviaciones de
   la constitución si la cierra.

## Referencia rápida del sistema

| | |
|---|---|
| **Entradas** | Export de FARHOS (`.xlsx`) + informe de contingencia de KARDEX (`.xls`, multi-hoja) |
| **Salida** | Comparativa por artículo con marca de producto externo, y Excel de 3 hojas |
| **Convención de diferencia** | `Stock Farhos − Stock Kardex` |
| **Motor de datos** | `procesador_inventario.py` — no importa Flask |
| **Capa web** | `app.py` — 4 rutas: `/login`, `/logout`, `/`, `/export_excel` |
| **Producción** | Gunicorn (3 workers, socket Unix) + systemd + nginx en puerto 5001, red interna |
| **Logs** | `journalctl -u jmg_diferenciesInventariKF -f` |
| **Desarrollo local** | `entvirt/bin/python app.py` → `http://localhost:3000` |

## Puntos de atención conocidos

Los dos hallazgos de mayor impacto registrados en la documentación:

- **`R-07` / `Q1`** — La consolidación agrupa por `(codigo, descripcion)` pero la fusión es solo por
  `codigo`: un mismo código con descripciones distintas en los dos orígenes multiplica filas en la
  comparativa e infla el recuento de diferencias. → tarea `T300`.
- **`R-13`** — El docstring de `comparar_inventarios` indica «Kardex − Farhos» mientras el código y
  la interfaz calculan `Farhos − Kardex` (la convención correcta). → tarea `T103`.

El listado completo está en `plan.md` §7.
