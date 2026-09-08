# Implementation Plan — Comparador d'Inventaris FARHOS ↔ KARDEX

**Versión:** 1.0.0 (as-built)
**Fecha:** 2026-09-08
**Spec de referencia:** `spec.md` v1.0.0
**Constitución:** `constitution.md` v1.0.0
**Commit documentado:** `52cf15c` (rama `master`)

> Este documento describe **CÓMO** está construido el sistema y por qué se eligió así.
> Los requisitos observables viven en `spec.md`.

---

## 1. Resumen técnico

Aplicación web monolítica en Flask, sin base de datos, con dos módulos: una capa web fina
(`app.py`) y un motor de proceso de datos con pandas (`procesador_inventario.py`). El estado de
una comparación se limita a la sesión firmada por cookie y a los ficheros subidos en disco. El
filtrado de resultados es íntegramente de cliente. Se despliega con Gunicorn sobre socket Unix,
supervisado por systemd y publicado por nginx en la red interna.

**Decisión rectora:** la complejidad del proyecto no está en la web ni en el despliegue, sino en la
lectura de dos formatos Excel hostiles. Todo lo demás se mantiene deliberadamente trivial.

## 2. Stack tecnológico

| Capa | Elección | Versión (entorno actual) | Motivo |
|---|---|---|---|
| Lenguaje | Python | 3.12 | Disponible en el servidor; ecosistema de datos |
| Framework web | Flask | 3.1.2 | Cuatro rutas y dos plantillas: un microframework es la talla exacta |
| Proceso de datos | pandas | 2.3.3 | `read_excel`, `merge` externo y `groupby` resuelven el núcleo del problema en pocas líneas |
| Numérico | numpy | 2.3.4 | Dependencia transitiva de pandas |
| Lectura `.xlsx` | openpyxl | 3.1.5 | Motor para el fichero de FARHOS y para escribir el Excel de salida |
| Lectura `.xls` | xlrd | 2.0.2 | El informe de KARDEX es Excel 97-2003; pandas lo exige para ese formato |
| Plantillas | Jinja2 (vía Flask) | — | Incluido |
| Servidor WSGI | Gunicorn | — | 3 workers sincrónicos, socket Unix |
| Proxy inverso | nginx | — | Publica en puerto 5001, gestiona el tamaño de subida |
| Supervisión | systemd | — | Arranque automático y logs en journald |
| UI | Bootstrap 5.3.3 vía CDN + JavaScript nativo | — | Pestañas, avisos y rejilla sin build ni herramientas de frontend |
| Estilos propios | `static/style.css` | — | Ajustes puntuales sobre Bootstrap |

**Sin framework de frontend, sin bundler, sin ORM, sin base de datos, sin sistema de migraciones.**
Coherente con el Artículo I.

## 3. Estructura del proyecto

```
diferenciesInventariKF/
├── app.py                              # Capa web: rutas, sesión, subida, render, exportación
├── procesador_inventario.py            # Motor de datos: lectura, depuración y comparación
├── templates/
│   ├── login.html                      # Formulario de contraseña
│   └── index.html                      # Carga de ficheros + resultados en pestañas + JS de filtrado
├── static/
│   └── style.css                       # Estilos complementarios
├── dadesCarregades/                    # Ficheros subidos (NO versionado, .gitignore)
├── requirements.txt                    # Dependencias declaradas
├── jmg_diferenciesInventariKF.service  # Unidad systemd (Gunicorn)
├── jmg_diferenciesInventariKF          # Server block de nginx (proxy al socket)
├── entvirt/                            # Entorno virtual (NO versionado)
└── docs/sdd/                           # Esta documentación
    ├── constitution.md
    ├── spec.md
    ├── plan.md
    └── tasks.md
```

## 4. Arquitectura

### 4.1 Vista de componentes

```
Navegador (red interna)
   │  HTTP :5001
   ▼
nginx  ──proxy_pass──►  socket Unix  ──►  Gunicorn (3 workers)
                                              │
                                              ▼
                                         app.py  (Flask)
                                          │        │
                          ┌───────────────┘        └──────────────┐
                          ▼                                       ▼
              dadesCarregades/ (disco)              procesador_inventario.py
                                                              │
                                                         pandas / openpyxl / xlrd
```

- **Frontera clara** (Artículo IV): `procesador_inventario.py` no importa Flask; `app.py` no
  contiene reglas de inventario.
- **Sin estado compartido entre workers**: cada petición es autónoma; el único estado es la cookie
  de sesión y los ficheros en disco. Por eso 3 workers sincrónicos son suficientes y seguros.

### 4.2 Flujo de la comparación (`POST /`)

```
1. Comprobar sesión ───────────────► si no, redirect a /login
2. Validar presencia de ambos ficheros ─► si falta, flash + redirect
3. secure_filename() sobre ambos nombres
4. Guardar en dadesCarregades/
5. Registrar rutas en session['last_farhos_path'] / ['last_kardex_path']
6. procesar_farhos(path)   ──► DataFrame | None
7. procesar_kardex(path)   ──► DataFrame | None
8. comparar_inventarios(f, k) ──► DataFrame | None
9. Si None ──► flash de error + redirect
   Si OK   ──► DataFrame.to_html() × 3  ──►  render index.html (resultados=True)
```

### 4.3 Flujo de la exportación (`POST /export_excel`)

```
1. Comprobar sesión
2. Comprobar que la sesión guarda las rutas de la última comparación
3. RE-PROCESAR los dos ficheros desde disco
4. pd.ExcelWriter sobre io.BytesIO ──► 3 hojas
5. send_file(as_attachment=True, download_name='diferencias_inventario.xlsx')
```

**Decisión — reprocesar en vez de cachear:** la exportación vuelve a leer y procesar los ficheros
en lugar de guardar los `DataFrame` en sesión o en memoria del worker. Motivos:
- la cookie de sesión no puede transportar miles de filas;
- una caché en memoria del proceso no es compartida entre los 3 workers de Gunicorn;
- el coste de reprocesar es de segundos y el uso es esporádico (NFR-001, NFR-003).

**Coste asumido:** los ficheros deben seguir existiendo en disco. Si se purgan, la exportación
falla (ver §7 R-05).

### 4.4 Rutas HTTP

| Ruta | Métodos | Autenticación | Responsabilidad |
|---|---|---|---|
| `/login` | GET, POST | No | Mostrar y validar el formulario de contraseña |
| `/logout` | GET | — | Vaciar la marca de sesión y volver al login |
| `/` | GET | Sí | GET: formulario de carga · POST: procesar y renderizar resultados |
| `/export_excel` | POST | Sí | Regenerar y servir el Excel de la última comparación |

Sin blueprints: cuatro rutas no justifican la indirección (Artículo I).

## 5. Diseño del motor de datos

### 5.1 `procesar_farhos(file_path) -> DataFrame | None`

| Paso | Implementación | Requisito |
|---|---|---|
| Lectura | `read_excel(skiprows=1)` — la primera fila del export es un título | §6.1 del spec |
| Normalización de columnas | Mapa `Cód.Esp→codigo`, `Especialidad→descripcion`, `Unidades→stock` | FR-020 |
| Validación | Si falta `codigo` o `stock` ⇒ `ValueError` | FR-027 |
| Descripción por defecto | Si falta la columna, se crea con `Sin descripción` | FR-026 |
| Proyección | Se retiene solo `codigo`, `descripcion`, `stock` | FR-020 |
| Código a texto | `astype(str)` + eliminación del sufijo `.0` por expresión regular `\.0$` | FR-021 |
| Descarte | `dropna(subset=['codigo','stock'])` | FR-022 |
| Stock numérico | `to_numeric(errors='coerce').fillna(0)` | FR-023 |
| Stock entero | `astype('Int64')` (entero nullable de pandas) | FR-024 |
| Consolidación | `groupby(['codigo','descripcion']).sum()` — colapsa los lotes | FR-025 |

**Nota de diseño — orden de las operaciones:** el `astype(str)` se aplica *antes* de limpiar el
sufijo decimal porque el código llega de Excel como flotante. Invertir el orden rompe FR-021.

### 5.2 `procesar_kardex(file_path) -> DataFrame | None`

| Paso | Implementación | Requisito |
|---|---|---|
| Apertura | `pd.ExcelFile` para enumerar hojas | FR-030 |
| Selección de hojas | `name.startswith('stockHuecos')` | FR-031 |
| Lectura por hoja | `read_excel(header=12)` — el encabezado real está en la fila 13 | §6.2 del spec |
| Normalización | Mapa `Cod.→codigo`, `Descripción→descripcion`, `Stock→stock` | FR-030 |
| Filtro de ruido | Se retienen las filas con `stock` no nulo y distinto del literal `"Stock"` | FR-032 |
| Descarte por código | `''→NA` y `dropna(subset=['codigo'])` | FR-033 |
| Hoja vacía | Se salta sin fallar | FR-030 |
| Unión | `concat` de todas las hojas | FR-030 |
| Sin datos | Si ninguna hoja aportó filas ⇒ `ValueError` | FR-036 |
| Tipos | `to_numeric` → `fillna(0)` → `astype('Int64')`; código a texto | FR-035 |
| Consolidación | `groupby(['codigo','descripcion']).sum()` — colapsa huecos y hojas | FR-034 |

**Decisión — filtrar por la columna de stock y no por número de fila:** el informe de KARDEX
intercala repeticiones del encabezado a lo largo del listado. Un `skiprows` fijo no las elimina;
el predicado «la celda de stock no es el texto *Stock*» sí, y es robusto a que aparezcan en
posiciones distintas.

**Deuda visible:** el módulo conserva comentado un enfoque anterior que construía las columnas
combinando índices posicionales (`1+2` para el código, `3+4` para la descripción, `5+6` para el
stock), sustituido por el mapeo por nombre de columna. Se mantiene como documentación histórica del
intento fallido; su retirada está en `tasks.md`.

### 5.3 `comparar_inventarios(df_farhos, df_kardex) -> DataFrame | None`

| Paso | Implementación | Requisito |
|---|---|---|
| Guarda | Si cualquiera de los dos es `None` ⇒ `None` (propagación de error) | FR-040 |
| Fusión | `merge(on='codigo', how='outer', suffixes=('_farhos','_kardex'))` | FR-040 |
| Marca de externo | `externo = stock_kardex.isna()` — **antes** de rellenar con ceros | FR-042 |
| Relleno | `fillna(0)` en ambos stocks | FR-041 |
| Descripción | `descripcion_farhos.fillna(descripcion_kardex)` | FR-043 |
| Diferencia | `stock_farhos − stock_kardex` | FR-044 |
| Proyección y nombres | Columnas finales y renombrado a etiquetas de presentación | FR-045 |

**Punto crítico de orden:** `externo` se calcula sobre los `NaN` de la fusión. Si se rellenase con
ceros antes, la información de «no existe» se perdería de forma irrecuperable. Es el único orden
posible y debe preservarse en cualquier refactor.

**Discrepancia documentada:** el docstring de la función dice «Kardex − Farhos», mientras el código
y la interfaz calculan `Farhos − Kardex`. La convención vinculante es la del Artículo III.3 y
FR-044 (`Farhos − Kardex`); el docstring es el que está mal. Corrección en `tasks.md`.

### 5.4 Contrato de error

Las tres funciones devuelven `None` ante cualquier excepción y registran la causa por salida
estándar (`print`), que Gunicorn dirige a journald. `app.py` traduce ese `None` en un aviso en
catalán para el usuario (FR-E6, NFR-007, NFR-010).

**Decisión:** propagación por valor de retorno en lugar de excepciones tipadas. Es suficiente para
tres funciones y un único consumidor; a cambio, la capa web no puede distinguir *qué* falló para dar
un mensaje específico. Mejora prevista en `tasks.md`.

## 6. Diseño de la interfaz

### 6.1 Render de tablas

Los `DataFrame` se convierten con `to_html(classes='table table-striped', index=False)` y se
insertan en la plantilla con el filtro `| safe`.

**El escapado no se pierde:** `DataFrame.to_html` escapa el contenido de las celdas por defecto
(`escape=True`), de modo que `| safe` marca como confiable el *marcado de tabla generado por
pandas*, no el texto procedente del Excel. Es lo que satisface NFR-011. **Cualquier cambio que
introduzca `escape=False` en `to_html` abre una vía de inyección de HTML desde una celda del
fichero de origen** y queda prohibido por el Artículo VI.6.

### 6.2 Filtrado de cliente (`filterTable`)

Una única función JavaScript sirve a las tres pestañas:

1. Localiza la tabla dentro del panel de la pestaña indicada.
2. **Busca los índices de columna por el texto del encabezado** (`Diferencia`, `externo`) en lugar
   de asumir posiciones fijas: así el filtro sobrevive a un cambio de orden de columnas.
3. Recorre las filas aplicando, en cascada, el filtro de texto, el de diferencia distinta de cero y
   el de externo/KARDEX.
4. Oculta o muestra cada fila y acumula el recuento de visibles.
5. Escribe el recuento en el contador de la pestaña correspondiente.

Se invoca en `window.onload` para inicializar los tres contadores, y en cada `onkeyup` u `onchange`.

**Decisión — filtrar en cliente y no en servidor:** los datos ya están íntegros en la página
(millares de filas, no millones). Filtrar en servidor exigiría endpoints, estado y un viaje de red
por cada pulsación de tecla, sin ganancia perceptible. Coherente con el Artículo IV.4.

**Acoplamiento asumido:** el JavaScript depende del texto literal de los encabezados `Diferencia`
y `externo` tal como los emite `comparar_inventarios`. Renombrar esas columnas en Python rompe los
filtros de forma silenciosa. Está anotado como riesgo R-06.

### 6.3 Alternancia carga / resultados

Un mismo `index.html` sirve los dos estados. Con `resultados=True` el bloque de carga se oculta por
estilo en línea y se renderiza la sección de resultados; el botón **Nova Comparació** invierte la
visibilidad por JavaScript, sin recargar la página (FR-051, FR-057).

### 6.4 Descarga de la exportación

El botón hace `fetch('/export_excel', {method:'POST'})`, recibe el `blob`, construye una URL de
objeto y dispara un enlace sintético con `download`. Se eligió sobre un envío de formulario clásico
para poder capturar un error del servidor y mostrarlo, en vez de dejar al navegador con una
descarga fallida.

## 7. Riesgos, deuda técnica y desviaciones

| ID | Riesgo / deuda | Impacto | Estado |
|---|---|---|---|
| **R-01** | Contraseña (`"1234"`) y clave de sesión (`'supersecretkey'`) fijadas en el código fuente | Cualquiera con acceso al repositorio puede entrar y firmar cookies de sesión válidas | Desviación aceptada del Artículo VI.3 · corrección fase 1 |
| **R-02** | Los formularios no llevan protección CSRF | Una página maliciosa podría inducir subidas o exportaciones desde una sesión abierta; mitigado por ser red interna y monousuario | Abierto |
| **R-03** | Discrepancia de límite de subida: 16 MB en Flask (`MAX_CONTENT_LENGTH`) frente a 50 M en nginx | Un fichero de 20 MB pasa nginx y Flask lo rechaza con un error crudo, sin aviso en catalán | Desviación aceptada del Artículo VII.4 · corrección fase 1 |
| **R-04** | Los ficheros subidos se acumulan en `dadesCarregades/` sin purga, y un nombre repetido sobrescribe el anterior | Crecimiento de disco; dos usuarios simultáneos con el mismo nombre de fichero se pisan mutuamente | Abierto (Q3 del spec) |
| **R-05** | La exportación depende de que los ficheros sigan en disco y de que la sesión conserve sus rutas | Tras un borrado manual o un reinicio con purga, exportar falla | Aceptado (consecuencia de §4.3) |
| **R-06** | El JavaScript de filtrado depende del texto literal de los encabezados `Diferencia` y `externo` | Un renombrado en Python desactiva los filtros sin error visible | Documentado |
| **R-07** | Un mismo código con descripciones distintas produce varias filas depuradas; la fusión por código puede multiplicarlas en la comparativa | Recuento de diferencias inflado y filas duplicadas en el informe | Abierto (Q1 del spec) |
| **R-08** | No existe ninguna prueba automatizada | Cualquier refactor del motor de datos es una apuesta | Desviación aceptada del Artículo VIII.1 · corrección fase 2 |
| **R-09** | `requirements.txt` sin versiones fijadas | Una reinstalación futura puede traer una versión incompatible de pandas o xlrd | Abierto |
| **R-10** | `app.run(debug=True)` en el punto de entrada del módulo | Inofensivo en producción (Gunicorn importa `app` y no ejecuta ese bloque), pero un arranque manual accidental expondría la consola de depuración | Documentado |
| **R-11** | Bootstrap se carga desde CDN externo | Sin salida a Internet, la interfaz pierde estilos y las pestañas dejan de funcionar | Abierto (supuesto §9.3 del spec) |
| **R-12** | Un renombrado con `inplace=True` se aplica sobre una proyección de columnas del `DataFrame` | Puede emitir `SettingWithCopyWarning` y, en versiones futuras de pandas, dejar de tener efecto | Abierto |
| **R-13** | El docstring de `comparar_inventarios` contradice el signo real de la diferencia | Riesgo de que un cambio futuro «corrija» el código hacia el signo equivocado | Corrección fase 1 |
| **R-14** | Diagnóstico limitado: el usuario recibe siempre el mismo mensaje genérico ante cualquier fallo de formato | Alarga el diagnóstico cuando cambia un formato de origen | Abierto |
| **R-15** | Trazas por `print()` en lugar de `logging`, sin nivel ni marca de tiempo propia | Logs pobres para diagnosticar incidencias pasadas | Abierto |

## 8. Estrategia de verificación

Estado actual: **verificación manual** contra los ficheros reales de ejemplo del servidor
(Artículo VIII.1). El procedimiento es:

1. Ejecutar `procesar_farhos` y `procesar_kardex` sobre un par de ficheros conocidos y comprobar
   número de filas y suma total de stock.
2. Ejecutar la comparación y comprobar que el recuento de externos coincide con lo esperado y que
   la suma de diferencias cuadra.
3. En la interfaz, comprobar los tres contadores de registros y cada combinación de filtros.
4. Exportar y confirmar que las tres hojas del Excel coinciden con las tres pestañas.

Estado objetivo (fase 2 de `tasks.md`): pruebas automatizadas sobre el motor de datos, con
ficheros de prueba mínimos y anonimizados en el repositorio, cubriendo cada requisito de las
secciones 5.3, 5.4 y 5.5 del spec. La frontera del Artículo IV es precisamente lo que hace esto
posible sin infraestructura de test web.

## 9. Despliegue

### 9.1 Cadena de producción

```
systemd (jmg_diferenciesInventariKF.service)
  └── Gunicorn · 3 workers · --bind unix:diferenciesInventariKF.sock · -m 007 · app:app
        usuario jordi · grupo www-data
        PATH del entorno virtual entvirt/bin
nginx (jmg_diferenciesInventariKF)
  └── listen 5001 · server_name 192.168.8.252 · client_max_body_size 50M
      proxy_pass al socket Unix del proyecto
```

El permiso `007` del socket y el grupo `www-data` son lo que permite a nginx escribir en él sin
abrir un puerto TCP local.

### 9.2 Puesta en marcha

```bash
python3 -m venv entvirt
entvirt/bin/pip install -r requirements.txt
sudo cp jmg_diferenciesInventariKF.service /etc/systemd/system/
sudo systemctl enable --now jmg_diferenciesInventariKF
sudo cp jmg_diferenciesInventariKF /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/jmg_diferenciesInventariKF /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 9.3 Operación

| Acción | Comando |
|---|---|
| Estado del servicio | `systemctl status jmg_diferenciesInventariKF` |
| Logs (incluye los `print` del motor) | `journalctl -u jmg_diferenciesInventariKF -f` |
| Recargar tras un cambio de código | `sudo systemctl restart jmg_diferenciesInventariKF` |
| Desarrollo local | `entvirt/bin/python app.py` → `http://localhost:3000` |

## 10. Trazabilidad requisito → implementación

| Requisitos | Ubicación |
|---|---|
| FR-001 … FR-006 | `app.py` — rutas `login` / `logout`, guardas de sesión · `templates/login.html` |
| FR-010 … FR-015 | `app.py` — rama `POST` de `index` · `templates/index.html` (formulario) |
| FR-020 … FR-027 | `procesador_inventario.py` — `procesar_farhos` |
| FR-030 … FR-036 | `procesador_inventario.py` — `procesar_kardex` |
| FR-040 … FR-045 | `procesador_inventario.py` — `comparar_inventarios` |
| FR-050 … FR-053 | `templates/index.html` — pestañas, buscadores, contadores, `filterTable` |
| FR-054 … FR-056 | `templates/index.html` — casillas de filtro y cascada de `filterTable` |
| FR-057, FR-058 | `templates/index.html` — botón *Nova Comparació* y bloque de mensajes flash |
| FR-060 … FR-065 | `app.py` — ruta `export_excel` · `templates/index.html` (descarga por `fetch`) |
| NFR-001 … NFR-003 | Diseño síncrono + 3 workers de Gunicorn (§9.1) |
| NFR-004, NFR-005 | Plantillas en catalán + Bootstrap responsive + `table-responsive` |
| NFR-006 | Unidad systemd con `WantedBy=multi-user.target` |
| NFR-007, NFR-010 | Bloques `try/except` del motor + traducción a flash en `app.py` |
| NFR-008, NFR-009 | nginx en red interna + `.gitignore` de `dadesCarregades/` |
| NFR-011 | Escapado por defecto de `to_html` (§6.1) |
| NFR-012 | Separación de módulos (Artículo IV, §4.1) |
