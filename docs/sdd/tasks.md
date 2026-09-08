# Tasks — Comparador d'Inventaris FARHOS ↔ KARDEX

**Versión:** 1.0.0
**Fecha:** 2026-09-08
**Plan de referencia:** `plan.md` v1.0.0 · **Spec:** `spec.md` v1.0.0

Este documento tiene dos partes:

- **Parte A — Retrospectiva (fase 0):** el trabajo ya realizado, reconstruido a partir del código y
  del historial, con su trazabilidad a requisitos. Sirve como registro de lo construido.
- **Parte B — Pendiente (fases 1–4):** el trabajo derivado de los riesgos de `plan.md` §7 y de las
  cuestiones abiertas de `spec.md` §10.

**Convenciones**
`[X]` completado · `[ ]` pendiente · `[P]` paralelizable con las tareas marcadas igual en su fase.
Cada tarea indica **archivos**, **requisito** que satisface y **criterio de aceptación**.

---

# Parte A · Fase 0 — Sistema construido *(completada)*

## A.1 Andamiaje y despliegue

- [X] **T001 — Estructura del proyecto y entorno virtual**
  Archivos: `entvirt/`, `.gitignore`
  Criterio: `entvirt/`, `__pycache__/` y `dadesCarregades/` excluidos del control de versiones (NFR-009).

- [X] **T002 — Declaración de dependencias**
  Archivos: `requirements.txt`
  Contenido: Flask, pandas, openpyxl, xlrd, gunicorn.
  Criterio: instalación limpia funcional. *Pendiente de fijar versiones → T310.*

- [X] **T003 — Unidad systemd para Gunicorn**
  Archivos: `jmg_diferenciesInventariKF.service`
  Requisito: NFR-006
  Criterio: 3 workers sobre socket Unix con permiso `007` y grupo `www-data`; arranque automático.

- [X] **T004 — Server block de nginx**
  Archivos: `jmg_diferenciesInventariKF`
  Requisito: NFR-008
  Criterio: escucha en 5001 y hace `proxy_pass` al socket del proyecto.

## A.2 Motor de datos (`procesador_inventario.py`)

- [X] **T010 — Lectura y depuración del inventario FARHOS**
  Función: `procesar_farhos`
  Requisitos: FR-020 … FR-027
  Criterio: devuelve `codigo`/`descripcion`/`stock` consolidado por suma; código sin sufijo `.0`;
  stock entero; error de formato si faltan las columnas esenciales.

- [X] **T011 — Lectura multi-hoja y depuración del inventario KARDEX**
  Función: `procesar_kardex`
  Requisitos: FR-030 … FR-036
  Criterio: procesa todas las hojas `stockHuecos*` con encabezado en la fila 13, descarta huecos
  vacíos y encabezados intercalados, y consolida por suma dentro y entre hojas.

- [X] **T012 — Comparación de inventarios con fusión externa**
  Función: `comparar_inventarios`
  Requisitos: FR-040, FR-041, FR-043, FR-044, FR-045
  Criterio: ningún artículo se pierde; ausencias como `0`; diferencia = `Farhos − Kardex`.

- [X] **T013 — Marca de producto externo al KARDEX**
  Función: `comparar_inventarios` (columna `externo`)
  Requisito: FR-042 · Commit: `52cf15c`
  Criterio: se calcula sobre los nulos de la fusión, **antes** del relleno con ceros.

- [X] **T014 — Contrato de error uniforme del motor**
  Requisitos: NFR-007, NFR-010
  Criterio: toda excepción se captura, se traza por salida estándar y se devuelve `None`.

## A.3 Capa web (`app.py`)

- [X] **T020 — Autenticación por contraseña compartida y sesión**
  Rutas: `login`, `logout`
  Requisitos: FR-001 … FR-006
  Criterio: sin sesión no hay acceso; el usuario autenticado que va al login es redirigido.

- [X] **T021 — Subida y validación de los dos ficheros**
  Ruta: `index` (POST)
  Requisitos: FR-010, FR-012, FR-013, FR-014
  Criterio: nombres saneados con `secure_filename`; límite de 16 MB; avisos en catalán si falta
  algún fichero.

- [X] **T022 — Orquestación del procesamiento y render de resultados**
  Ruta: `index` (POST)
  Requisitos: FR-050, FR-051, NFR-011
  Criterio: tres tablas HTML generadas con escapado por defecto; ante `None`, aviso al usuario y
  vuelta al formulario.

- [X] **T023 — Memoria de la última comparación en sesión**
  Requisito: FR-015
  Criterio: `last_farhos_path` y `last_kardex_path` disponibles para la exportación.

- [X] **T024 — Exportación a Excel de tres hojas**
  Ruta: `export_excel` · Commit: `cd7567c`
  Requisitos: FR-060 … FR-065
  Criterio: escritura en memoria con `BytesIO`; hojas *Depuracion Farhos*, *Depuracion Kardex* y
  *Diferencias Inventario*; descarga como `diferencias_inventario.xlsx`; avisos si no hay
  comparación previa o si la generación falla.

## A.4 Interfaz

- [X] **T030 — Plantilla de login**
  Archivos: `templates/login.html`
  Requisitos: FR-006, NFR-004
  Criterio: formulario en catalán con mensaje de error integrado.

- [X] **T031 — Plantilla principal: carga y resultados en pestañas**
  Archivos: `templates/index.html`
  Requisitos: FR-011, FR-050, FR-051, FR-058
  Criterio: formulario con `accept` por tipo de fichero y patrón de nombre de KARDEX indicado;
  tres pestañas Bootstrap; mensajes flash descartables por categoría.

- [X] **T032 — Búsqueda de texto y contadores de registros**
  Archivos: `templates/index.html` (`filterTable`)
  Requisitos: FR-052, FR-053
  Criterio: búsqueda insensible a mayúsculas sobre todas las columnas; contador por pestaña
  inicializado al cargar la página.

- [X] **T033 — Filtro de «solo diferencias»**
  Requisito: FR-054 · Commit: `cd7567c`
  Criterio: oculta las filas con diferencia `0`; el índice de columna se localiza por el texto del
  encabezado, no por posición.

- [X] **T034 — Filtros de productos externos y de productos KARDEX**
  Requisitos: FR-055, FR-056 · Commit: `52cf15c`
  Criterio: casillas independientes, combinables entre sí, con el filtro de diferencias y con la
  búsqueda de texto.

- [X] **T035 — Nueva comparación sin recargar**
  Requisito: FR-057
  Criterio: alterna la visibilidad de las secciones de carga y resultados.

- [X] **T036 — Descarga de la exportación con captura de error**
  Requisito: FR-065
  Criterio: `fetch` + `blob` + enlace sintético; un error del servidor se muestra al usuario.

- [X] **T037 — Estilos complementarios**
  Archivos: `static/style.css`
  Requisito: NFR-005
  Criterio: tipografía, tarjetas, tablas con franjas y desplazamiento horizontal sobre Bootstrap.

## A.5 Documentación

- [X] **T040 — Documentación SDD del sistema construido**
  Archivos: `docs/sdd/constitution.md`, `spec.md`, `plan.md`, `tasks.md`
  Criterio: principios, requisitos, arquitectura y backlog trazables al código en `52cf15c`.

---

# Parte B · Trabajo pendiente

## Fase 1 — Cerrar desviaciones de la constitución *(prioridad alta)*

Estas tareas eliminan desviaciones registradas en `constitution.md` §Gobernanza.

- [ ] **T100 — Externalizar la contraseña y la clave de sesión** `[P]`
  Archivos: `app.py`, `requirements.txt`, `jmg_diferenciesInventariKF.service`, `docs/sdd/plan.md`
  Riesgo: **R-01** · Artículo VI.3
  Trabajo: leer contraseña y `secret_key` de variables de entorno (definidas en la unidad systemd o
  en un fichero de entorno fuera del repositorio), con fallo explícito de arranque si no están.
  Criterio de aceptación: ningún secreto aparece en el código fuente; el servicio arranca con las
  variables definidas y falla con un mensaje claro si faltan; la tabla de desviaciones de la
  constitución se actualiza.

- [ ] **T101 — Alinear el límite de tamaño de subida** `[P]`
  Archivos: `app.py` o `jmg_diferenciesInventariKF`
  Riesgo: **R-03** · Artículo VII.4 · Requisito FR-014, NFR-002
  Trabajo: fijar el mismo límite en Flask y en nginx (recomendado: 50 MB en ambos, dado que el
  informe de KARDEX ya alcanza 1,4 MB y puede crecer).
  Criterio: un fichero que excede el límite produce un aviso comprensible, no un error crudo.

- [ ] **T102 — Manejar el rechazo por tamaño con un mensaje en catalán**
  Archivos: `app.py`, `templates/index.html`
  Depende de: T101 · Requisito FR-014, Artículo V.2
  Trabajo: gestionar el error de carga excesiva devolviendo al formulario con un aviso.
  Criterio: subir un fichero sobredimensionado devuelve al formulario con mensaje, sin traza.

- [ ] **T103 — Corregir el docstring de la diferencia** `[P]`
  Archivos: `procesador_inventario.py`
  Riesgo: **R-13** · Requisito FR-044
  Trabajo: el docstring de `comparar_inventarios` dice «Kardex − Farhos»; el cálculo correcto y
  vinculante es `Farhos − Kardex`.
  Criterio: docstring, código, interfaz y `spec.md` coinciden en el signo.

- [ ] **T104 — Retirar el código muerto del enfoque posicional** `[P]`
  Archivos: `procesador_inventario.py`
  Trabajo: eliminar el bloque comentado que construía las columnas por índices posicionales,
  sustituido por el mapeo por nombre. La decisión histórica queda registrada en `plan.md` §5.2.
  Criterio: el módulo no contiene bloques de código comentado; el comportamiento no cambia.

- [ ] **T105 — Sustituir `print` por `logging`**
  Archivos: `procesador_inventario.py`, `app.py`
  Riesgo: **R-15** · Requisito NFR-007
  Trabajo: logger por módulo con nivel y contexto (origen del fichero, causa); eliminar las trazas
  de depuración de `df.head()`.
  Criterio: `journalctl -u jmg_diferenciesInventariKF` muestra líneas con nivel y mensaje útil; no
  se vuelcan datos de inventario en los logs.

- [ ] **T106 — Aislar el arranque de desarrollo del de producción** `[P]`
  Archivos: `app.py`
  Riesgo: **R-10** · Artículo VII.2
  Trabajo: que `debug` dependa de una variable de entorno en lugar de estar fijado a `True`.
  Criterio: un arranque manual accidental no activa la consola de depuración por defecto.

## Fase 2 — Verificabilidad *(prioridad alta)*

Cierra la desviación del Artículo VIII.1 y es prerrequisito de la fase 3.

- [ ] **T200 — Ficheros de prueba mínimos y anonimizados**
  Archivos: `tests/fixtures/`
  Artículo VIII.1
  Trabajo: construir un `.xlsx` de FARHOS y un `.xls` de KARDEX pequeños que reproduzcan las
  anomalías reales documentadas en `spec.md` §6: fila de título, código como flotante, lotes
  repetidos, filas de continuación sin código, varias hojas `stockHuecos`, encabezado en la fila 13,
  encabezados intercalados y huecos vacíos.
  Criterio: los ficheros no contienen datos reales del hospital y pueden versionarse.

- [ ] **T201 — Pruebas de `procesar_farhos`** `[P]`
  Archivos: `tests/test_procesador_farhos.py`
  Depende de: T200 · Requisitos FR-020 … FR-027
  Criterio: una prueba por requisito, incluidos el descarte de la fila de título, la normalización
  del sufijo `.0`, la consolidación de lotes y el error por columnas ausentes.

- [ ] **T202 — Pruebas de `procesar_kardex`** `[P]`
  Archivos: `tests/test_procesador_kardex.py`
  Depende de: T200 · Requisitos FR-030 … FR-036
  Criterio: cubre la selección de hojas por prefijo, el descarte de encabezados intercalados y de
  huecos vacíos, y la consolidación entre hojas.

- [ ] **T203 — Pruebas de `comparar_inventarios`** `[P]`
  Archivos: `tests/test_comparacion.py`
  Depende de: T200 · Requisitos FR-040 … FR-045
  Criterio: cubre artículo solo en FARHOS (externo), solo en KARDEX, presente en ambos con y sin
  diferencia, el signo de la diferencia y la propagación de `None`.

- [ ] **T204 — Pruebas de las rutas web**
  Archivos: `tests/test_app.py`
  Requisitos: FR-001 … FR-005, FR-012, FR-064
  Trabajo: con el cliente de pruebas de Flask, verificar las redirecciones sin sesión, el login
  correcto e incorrecto, el envío sin ficheros y la exportación sin comparación previa.
  Criterio: las pruebas no requieren servidor ni ficheros reales.

- [ ] **T205 — Declarar las dependencias de prueba**
  Archivos: `requirements-dev.txt`
  Criterio: `pytest` instalable sin contaminar `requirements.txt` de producción.

## Fase 3 — Corrección de datos *(prioridad media; requiere fase 2)*

- [ ] **T300 — Resolver la multiplicación de filas por descripciones divergentes**
  Archivos: `procesador_inventario.py`
  Riesgo: **R-07** · Cuestión abierta **Q1**
  Trabajo: decidir y documentar la clave de consolidación. Opción recomendada: agrupar por `codigo`
  y quedarse con una descripción representativa, de modo que el código sea clave única antes de la
  fusión y el `outer join` no pueda multiplicar filas.
  Criterio: ningún código aparece dos veces en la comparativa; las pruebas de T201–T203 incluyen el
  caso de un código con dos descripciones; la decisión queda escrita en `spec.md` §6.3.

- [ ] **T301 — Categorizar los artículos presentes solo en KARDEX**
  Archivos: `procesador_inventario.py`, `templates/index.html`, `docs/sdd/spec.md`
  Cuestión abierta **Q2**
  Trabajo: valorar con el usuario de farmacia si un artículo que está en la máquina y no en FARHOS
  merece marca y filtro propios, igual que los externos.
  Criterio: decisión tomada y registrada; si es afirmativa, implementada con su filtro y su
  requisito nuevo en el spec.

- [ ] **T302 — Diagnóstico específico de errores de formato**
  Archivos: `procesador_inventario.py`, `app.py`
  Riesgo: **R-14** · Artículo II.4
  Trabajo: distinguir las causas de fallo (hoja no encontrada, columna ausente, fichero ilegible) y
  traducirlas a mensajes en catalán que digan qué revisar del fichero.
  Criterio: subir un fichero de FARHOS en el campo de KARDEX produce un mensaje que identifica el
  problema, no el aviso genérico.

- [ ] **T303 — Validar el origen de cada fichero antes de procesar**
  Archivos: `procesador_inventario.py` o `app.py`
  Cuestión abierta **Q4**
  Depende de: T302
  Trabajo: comprobación ligera de que cada fichero es del origen esperado (presencia de las hojas
  `stockHuecos*` para KARDEX, de las columnas esperadas para FARHOS) antes del procesamiento.
  Criterio: los ficheros intercambiados se detectan y se avisa al usuario.

- [ ] **T304 — Corregir el renombrado sobre proyección de columnas**
  Archivos: `procesador_inventario.py`
  Riesgo: **R-12**
  Trabajo: evitar el `rename(inplace=True)` sobre una proyección; construir el resultado final en
  una sola operación.
  Criterio: el procesamiento no emite `SettingWithCopyWarning`; las pruebas de T203 siguen pasando.

- [ ] **T310 — Fijar las versiones de las dependencias** `[P]`
  Archivos: `requirements.txt`
  Riesgo: **R-09** · Artículo VII.3
  Trabajo: fijar las versiones actualmente en uso (Flask 3.1.2, pandas 2.3.3, openpyxl 3.1.5,
  xlrd 2.0.2, numpy 2.3.4, gunicorn).
  Criterio: una instalación limpia reproduce el entorno verificado.

## Fase 4 — Operación y robustez *(prioridad baja)*

- [ ] **T400 — Política de retención de los ficheros subidos**
  Archivos: `app.py` (y, si procede, una unidad `systemd-tmpfiles` o temporizador)
  Riesgo: **R-04** · Cuestión abierta **Q3** · Artículo VI.4
  Trabajo: decidir la retención (p. ej. purgar los ficheros de más de N días) teniendo en cuenta la
  dependencia de la exportación descrita en `plan.md` §4.3 y el riesgo R-05.
  Criterio: `dadesCarregades/` no crece indefinidamente y la exportación sigue funcionando durante
  la vida de una sesión de trabajo.

- [ ] **T401 — Evitar la colisión de nombres de ficheros subidos**
  Archivos: `app.py`
  Riesgo: **R-04**
  Trabajo: prefijar el nombre saneado con un identificador único por subida, de modo que dos
  cargas del mismo nombre no se sobrescriban.
  Criterio: dos comparaciones consecutivas con ficheros homónimos no interfieren entre sí.

- [ ] **T402 — Protección CSRF en los formularios**
  Archivos: `app.py`, `templates/*.html`, `requirements.txt`
  Riesgo: **R-02**
  Trabajo: token CSRF en el login, la subida y la exportación.
  Criterio: una petición sin token válido es rechazada; el flujo normal no se altera.

- [ ] **T403 — Servir Bootstrap localmente**
  Archivos: `static/`, `templates/*.html`
  Riesgo: **R-11** · Supuesto §9.3 del spec
  Trabajo: alojar el CSS y el JS de Bootstrap en `static/` para que la interfaz no dependa de
  salida a Internet.
  Criterio: la aplicación se ve y funciona correctamente con el servidor sin acceso externo.

- [ ] **T404 — Exportar la vista filtrada**
  Archivos: `templates/index.html`, `app.py`
  Cuestión abierta **Q5**
  Trabajo: valorar con el usuario si la exportación debe reflejar los filtros activos en pantalla
  además del conjunto completo.
  Criterio: decisión registrada en `spec.md`; si es afirmativa, requisito nuevo e implementación
  que preserve FR-062 para el conjunto completo.

- [ ] **T405 — Aviso de coherencia temporal entre ficheros**
  Archivos: `templates/index.html`
  Supuesto §9.1 del spec
  Trabajo: recordar en el formulario que los dos ficheros deben corresponder al mismo momento, y
  mostrar en los resultados la marca de tiempo del informe de KARDEX si se puede extraer del
  nombre del fichero.
  Criterio: el usuario puede confirmar de un vistazo qué está comparando.

---

## Trazabilidad de riesgos → tareas

| Riesgo (`plan.md` §7) | Tarea |
|---|---|
| R-01 secretos en el código | T100 |
| R-02 sin CSRF | T402 |
| R-03 límites de subida incoherentes | T101, T102 |
| R-04 ficheros acumulados y colisiones | T400, T401 |
| R-05 exportación dependiente del disco | considerada en T400 |
| R-06 acoplamiento JS ↔ encabezados | documentado en `plan.md` §6.2 |
| R-07 multiplicación de filas | T300 |
| R-08 sin pruebas | T200 … T205 |
| R-09 dependencias sin fijar | T310 |
| R-10 `debug=True` en el código | T106 |
| R-11 dependencia del CDN | T403 |
| R-12 renombrado sobre proyección | T304 |
| R-13 docstring con el signo invertido | T103 |
| R-14 diagnóstico genérico | T302, T303 |
| R-15 trazas por `print` | T105 |

## Trazabilidad de cuestiones abiertas → tareas

| Cuestión (`spec.md` §10) | Tarea |
|---|---|
| Q1 clave de consolidación | T300 |
| Q2 artículos solo en KARDEX | T301 |
| Q3 retención de ficheros | T400 |
| Q4 validación del origen del fichero | T303 |
| Q5 exportar la vista filtrada | T404 |

## Orden de ejecución recomendado

```
Fase 1  T100 · T101 · T103 · T104 · T106     (paralelas)
        T102  (tras T101)
        T105
Fase 2  T200 → T201 · T202 · T203 · T204     (las tres primeras en paralelo)
        T205  (en cualquier momento)
Fase 3  T310 (independiente)
        T300 → T304                          (con la red de pruebas de la fase 2)
        T302 → T303
        T301  (requiere decisión del usuario)
Fase 4  T400 → T401 · T402 · T403 · T405
        T404  (requiere decisión del usuario)
```

Las fases 3 y 4 no deben abordarse antes de la fase 2: modificar el motor de datos sin pruebas
contradice el Artículo VIII.1.
