# Spec — Comparador d'Inventaris FARHOS ↔ KARDEX

**Versión:** 1.0.0 (as-built, refleja el código en `master` @ `52cf15c`)
**Fecha:** 2026-09-08
**Estado:** implementado y en producción interna
**Constitución aplicable:** `constitution.md` v1.0.0

> Este documento describe **QUÉ** hace el sistema y **POR QUÉ**, en términos observables.
> Las decisiones de implementación viven en `plan.md`.

---

## 1. Contexto y problema

La farmacia del hospital gestiona su stock en dos sistemas que no están integrados entre sí:

| Sistema | Qué es | Qué contiene |
|---|---|---|
| **FARHOS** | Sistema de gestión farmacéutica (web) | Inventario teórico completo: todos los artículos del almacén de farmacia, con lote y unidades |
| **KARDEX** | Almacén vertical automatizado | Stock físico real de los artículos que están **dentro** de la máquina, por hueco y ubicación |

Ambos sistemas se desincronizan con el uso diario (dispensaciones, devoluciones, mermas, entradas
no registradas). Detectar la divergencia exige hoy exportar dos Excel de estructura muy distinta y
cruzarlos a mano: un trabajo lento, propenso a error y que nadie repite con la frecuencia deseable.

Además, no todos los artículos de FARHOS viven en el KARDEX. Los que no están en la máquina
(«productos externos») aparecerían como diferencia total falsa si se cruzasen sin distinguirlos.

## 2. Propuesta de valor

Una aplicación web interna donde el personal de farmacia sube los dos ficheros tal como los
exportan los sistemas de origen, y obtiene en segundos:

- la tabla de diferencias de stock artículo por artículo,
- la marca de qué artículos son externos al KARDEX (y por tanto su «diferencia» no es un problema),
- las tablas intermedias depuradas, para poder auditar de dónde sale cada número,
- un Excel descargable con todo lo anterior.

**Métrica de éxito:** el cruce de inventarios pasa de una tarea manual de horas a una operación de
menos de un minuto, repetible por cualquier persona del servicio sin apoyo de IT.

## 3. Usuarios y actores

| Actor | Descripción | Necesidad |
|---|---|---|
| **Responsable de farmacia / técnico de farmacia** | Usuario único y exclusivo del sistema | Saber qué artículos descuadran y cuánto, para regularizar |
| **Administrador del sistema** | Mantenedor del servidor Linux interno | Que el servicio arranque solo y deje trazas útiles si falla |
| FARHOS *(sistema)* | Origen de datos, no interactúa | — |
| KARDEX *(sistema)* | Origen de datos, no interactúa | — |

No existen roles, ni permisos diferenciados, ni usuarios nominales. Ver §7 (autenticación).

## 4. Escenarios de usuario

### E1 — Comparación nominal *(camino principal)*
1. El usuario abre la aplicación en la red interna del hospital.
2. El sistema le pide una contraseña; el usuario la introduce y accede.
3. El usuario selecciona el fichero de FARHOS (`.xlsx`) y el de KARDEX (`.xls`) y pulsa **Processar**.
4. El sistema procesa ambos ficheros y sustituye el formulario por tres pestañas de resultados:
   *Depuració Farhos*, *Depuració Kardex* y *Comparativa d'Inventaris*.
5. El usuario abre la comparativa, marca **Mostrar només diferències** y ve solo los artículos
   descuadrados, con el recuento de registros visibles.
6. El usuario desmarca **Mostrar productes EXTERNS** para quedarse únicamente con los artículos que
   sí viven en el KARDEX.
7. El usuario pulsa **Exportar a Excel** y recibe `diferencias_inventario.xlsx`.

### E2 — Búsqueda de un artículo concreto
El usuario escribe un código o parte de una descripción en el buscador de cualquiera de las tres
pestañas; la tabla se reduce a las filas coincidentes y el contador se actualiza.

### E3 — Nueva comparación
Tras revisar unos resultados, el usuario pulsa **Nova Comparació**: reaparece el formulario de
carga y puede subir otro par de ficheros.

### E4 — Contraseña incorrecta
El sistema no da acceso y muestra el aviso «Pwd incorrecte. Intenta-ho de nou.» en el propio
formulario de login.

### E5 — Fichero no seleccionado o formulario incompleto
El sistema avisa («Faltan fitxers en el formulari.» / «Un o ambdos fitxers no han sigut
seleccionats.») y vuelve al formulario sin procesar nada.

### E6 — Fichero con formato inesperado
El procesamiento falla de forma controlada. El usuario ve un aviso que le indica revisar el formato
de los ficheros; el detalle técnico queda en los logs del servidor.

### E7 — Exportación sin comparación previa
Si se intenta exportar sin haber procesado nada en la sesión, el sistema avisa de que primero hay
que procesar los ficheros.

### E8 — Sesión cerrada
El usuario pulsa **Tancar Sessió**; vuelve al login y cualquier acceso posterior a la aplicación o
a la exportación redirige al login.

---

## 5. Requisitos funcionales

### 5.1 Acceso

| ID | Requisito |
|---|---|
| **FR-001** | El sistema DEBE exigir autenticación por contraseña compartida antes de dar acceso a cualquier funcionalidad de comparación o exportación. |
| **FR-002** | El sistema DEBE mantener el estado de autenticación en la sesión del navegador. |
| **FR-003** | Un usuario ya autenticado que acceda al login DEBE ser redirigido a la página principal. |
| **FR-004** | El sistema DEBE ofrecer cierre de sesión explícito que invalide el acceso. |
| **FR-005** | Un acceso no autenticado a la página principal o a la exportación DEBE redirigir al login, sin filtrar información. |
| **FR-006** | Una contraseña incorrecta DEBE producir un mensaje de error en el formulario, sin distinguir causas. |

### 5.2 Carga de ficheros

| ID | Requisito |
|---|---|
| **FR-010** | El sistema DEBE aceptar exactamente dos ficheros por comparación: uno de FARHOS y uno de KARDEX. |
| **FR-011** | El formulario DEBE indicar el formato esperado de cada fichero, incluido el patrón de nombre del informe de KARDEX (`STK-Cen-ContingenciaArticulos-XXXXXXXX_XXXXXX.xls`). |
| **FR-012** | El sistema DEBE rechazar el envío si falta cualquiera de los dos ficheros. |
| **FR-013** | El sistema DEBE sanear los nombres de fichero antes de escribirlos en disco. |
| **FR-014** | El sistema DEBE limitar el tamaño de la subida y rechazar ficheros que lo excedan. |
| **FR-015** | El sistema DEBE conservar la referencia a los ficheros de la última comparación de la sesión, para poder regenerar la exportación. |

### 5.3 Depuración del inventario FARHOS

| ID | Requisito |
|---|---|
| **FR-020** | El sistema DEBE extraer de cada fila el código de artículo, su descripción y las unidades en stock. |
| **FR-021** | El código de artículo DEBE normalizarse como texto, eliminando cualquier sufijo decimal introducido por Excel (p. ej. `100.0` → `100`). |
| **FR-022** | Las filas sin código o sin stock DEBEN descartarse. |
| **FR-023** | Los valores de stock no numéricos DEBEN interpretarse como `0`, no provocar el fallo del proceso. |
| **FR-024** | El stock DEBE presentarse como entero, sin decimales. |
| **FR-025** | Los artículos repetidos (mismo código y descripción, p. ej. distintos lotes) DEBEN consolidarse en una sola fila sumando su stock. |
| **FR-026** | Si el fichero no aporta descripción, DEBE usarse el valor `Sin descripción`. |
| **FR-027** | La ausencia de las columnas esenciales (código, stock) DEBE tratarse como error de formato del fichero. |

### 5.4 Depuración del inventario KARDEX

| ID | Requisito |
|---|---|
| **FR-030** | El sistema DEBE procesar **todas** las hojas de datos del informe, no solo la primera. |
| **FR-031** | El sistema DEBE identificar las hojas de datos por convención de nombre (prefijo `stockHuecos`) e ignorar el resto. |
| **FR-032** | El sistema DEBE descartar las filas de cabecera, subtotales, repeticiones de encabezado y huecos sin artículo. |
| **FR-033** | Las filas sin código de artículo DEBEN descartarse. |
| **FR-034** | Los artículos repetidos, tanto dentro de una hoja como entre hojas distintas, DEBEN consolidarse sumando su stock. |
| **FR-035** | El stock DEBE presentarse como entero; los valores no numéricos como `0`. |
| **FR-036** | Si ninguna hoja aporta datos válidos, DEBE tratarse como error de formato del fichero. |

### 5.5 Comparación

| ID | Requisito |
|---|---|
| **FR-040** | La comparación DEBE incluir todos los artículos presentes en cualquiera de los dos inventarios (fusión externa completa por código). |
| **FR-041** | Un artículo presente en un solo inventario DEBE mostrar stock `0` en el otro, nunca vacío. |
| **FR-042** | El sistema DEBE marcar como **externo** todo artículo que exista en FARHOS y no exista en el KARDEX. |
| **FR-043** | La descripción mostrada DEBE ser la de FARHOS cuando exista y, en su defecto, la de KARDEX. |
| **FR-044** | La diferencia DEBE calcularse como `Stock FARHOS − Stock KARDEX`. |
| **FR-045** | El resultado DEBE presentar las columnas: código, descripción, externo, Stock Farhos, Stock Kardex, Diferencia. |

### 5.6 Presentación de resultados

| ID | Requisito |
|---|---|
| **FR-050** | El sistema DEBE mostrar tres vistas en pestañas: depuración FARHOS, depuración KARDEX y comparativa. |
| **FR-051** | Al mostrar resultados, el formulario de carga DEBE ocultarse para no confundir al usuario. |
| **FR-052** | Cada vista DEBE ofrecer un buscador de texto libre que filtre las filas por coincidencia en cualquier columna, sin distinguir mayúsculas. |
| **FR-053** | Cada vista DEBE mostrar el número de registros visibles tras los filtros aplicados, y actualizarlo en cada cambio de filtro. |
| **FR-054** | La comparativa DEBE ofrecer un filtro para mostrar solo las filas con diferencia distinta de `0`. |
| **FR-055** | La comparativa DEBE ofrecer filtros independientes para mostrar u ocultar los productos externos y los productos del KARDEX. |
| **FR-056** | Los filtros DEBEN ser combinables entre sí y con la búsqueda de texto. |
| **FR-057** | El sistema DEBE ofrecer una acción **Nova Comparació** que devuelva al formulario de carga. |
| **FR-058** | Los mensajes del sistema DEBEN mostrarse como avisos descartables, diferenciando éxito de error. |

### 5.7 Exportación

| ID | Requisito |
|---|---|
| **FR-060** | El sistema DEBE permitir descargar los resultados de la última comparación de la sesión en un único fichero Excel. |
| **FR-061** | El Excel DEBE contener tres hojas: depuración FARHOS, depuración KARDEX y diferencias de inventario. |
| **FR-062** | El contenido exportado DEBE coincidir con el mostrado en pantalla (mismos datos sin filtrar). |
| **FR-063** | El fichero DEBE descargarse con el nombre `diferencias_inventario.xlsx`. |
| **FR-064** | Un intento de exportación sin comparación previa en la sesión DEBE producir un aviso y no un error. |
| **FR-065** | Un fallo durante la exportación DEBE informarse al usuario sin dejar la aplicación en estado inutilizable. |

---

## 6. Contratos de datos *(Artículo II de la constitución)*

Estos contratos son la dependencia más frágil del sistema. Cualquier cambio aguas arriba rompe el
procesamiento y **debe reflejarse aquí**.

### 6.1 Fichero de origen FARHOS

| Aspecto | Contrato |
|---|---|
| Formato | Excel `.xlsx` (export de FARHOS Web) |
| Nombre habitual | `ExportacionInventarios_<timestamp>.xlsx` |
| Estructura | Una sola hoja; **la primera fila es un título** y no forma parte de los datos |
| Fila de encabezado | Segunda fila del fichero |
| Columnas observadas | `Cód.Almacen`, `Almacen`, `Cód.Esp`, `Especialidad`, `Status`, `Lote`, `Unidades`, `Envases` |
| Columnas **requeridas** | `Cód.Esp` → código · `Unidades` → stock |
| Columna opcional | `Especialidad` → descripción (si falta, `Sin descripción`) |
| Granularidad | Una fila por artículo **y lote** ⇒ el mismo código aparece repetido |
| Anomalía conocida | Existen filas de continuación en las que la descripción del artículo aparece desplazada a la columna `Cód.Almacen` y las columnas de código quedan vacías; se descartan por no tener código válido |
| Tipos | `Cód.Esp` llega como flotante (`100.0`) y requiere normalización a texto; `Unidades` llega como numérico |
| Volumen de referencia | ~3.150 filas |

### 6.2 Fichero de origen KARDEX

| Aspecto | Contrato |
|---|---|
| Formato | Excel `.xls` (formato antiguo, requiere `xlrd`) |
| Nombre habitual | `STK-Cen-ContingenciaArticulos-AAAAMMDD_HHMMSS.xls` |
| Hojas | Varias, nombradas `stockHuecos`, `stockHuecos 2`, `stockHuecos 3`, … · **solo se procesan las que empiezan por `stockHuecos`** |
| Fila de encabezado | **Fila 13** del fichero (12 filas de cabecera de informe por encima) |
| Columnas relevantes | `Cod.` → código · `Descripción` → descripción · `Stock` → stock |
| Otras columnas presentes | `Ubicación`, `Cap.`, `Bloq.`, `Hueco`, `Lote`, `Fecha`, más varias sin nombre (`Unnamed: N`) fruto de celdas combinadas |
| Filas a descartar | Huecos vacíos (sin stock), filas donde la celda de stock repite literalmente el texto `Stock` (encabezados intercalados a lo largo del informe) y filas sin código |
| Granularidad | Una fila por **hueco físico** ⇒ un mismo artículo aparece en varios huecos, y en varias hojas |
| Volumen de referencia | ~550 filas por hoja |

### 6.3 Modelo canónico interno

Ambos orígenes se reducen al mismo modelo antes de compararse:

```
InventarioDepurado
  codigo      : texto      # clave de negocio, normalizada
  descripcion : texto
  stock       : entero     # consolidado por suma
```
Clave de agrupación: (`codigo`, `descripcion`).

### 6.4 Modelo de salida

```
Comparativa
  codigo       : texto
  descripcion  : texto     # FARHOS, o KARDEX si no hay de FARHOS
  externo      : booleano  # existe en FARHOS y no en KARDEX
  Stock Farhos : entero
  Stock Kardex : entero
  Diferencia   : entero    # Stock Farhos − Stock Kardex
```

**Interpretación operativa:**
- `Diferencia > 0` → FARHOS cree tener más de lo que hay en la máquina.
- `Diferencia < 0` → hay más stock físico en la máquina del que FARHOS registra.
- `externo = true` → artículo que no se almacena en el KARDEX; su diferencia **no indica
  descuadre** y por eso el usuario puede filtrarlo.

---

## 7. Requisitos no funcionales

| ID | Requisito |
|---|---|
| **NFR-001 · Rendimiento** | Una comparación de ~3.000 filas de FARHOS contra ~1.500 de KARDEX debe resolverse en tiempo interactivo (segundos), en una sola petición HTTP síncrona. |
| **NFR-002 · Capacidad** | Debe soportar ficheros de al menos el tamaño de los informes reales actuales (KARDEX hasta ~1,4 MB, FARHOS hasta ~250 KB), con margen. |
| **NFR-003 · Concurrencia** | Uso esporádico y prácticamente monousuario. No se requiere soportar carga concurrente significativa. |
| **NFR-004 · Idioma** | Interfaz en catalán (Artículo V). |
| **NFR-005 · Navegador** | Debe funcionar en navegador de escritorio moderno; diseño adaptable mediante rejilla responsive y tablas con desplazamiento horizontal. |
| **NFR-006 · Disponibilidad** | El servicio debe arrancar automáticamente con el sistema y reponerse tras reinicio del servidor. |
| **NFR-007 · Observabilidad** | Los errores de procesamiento deben quedar registrados en los logs del servicio, identificando el origen (FARHOS o KARDEX) y la causa. |
| **NFR-008 · Red** | Accesible solo desde la red interna, a través del proxy inverso. |
| **NFR-009 · Confidencialidad** | Los ficheros subidos y los resultados no se versionan ni salen del servidor. |
| **NFR-010 · Robustez de entrada** | Un fichero mal formado no debe tumbar el servicio; el fallo se acota al procesamiento de esa petición. |
| **NFR-011 · Escapado de salida** | Todo texto procedente de los Excel se renderiza escapado; ninguna celda puede inyectar HTML o script en la página. |
| **NFR-012 · Mantenibilidad** | La lógica de negocio debe poder ejecutarse y verificarse sin levantar el servidor web (Artículo IV). |

---

## 8. Fuera de ámbito

Explícitamente **no** forma parte del sistema:

- Conexión directa (API, base de datos) a FARHOS o al KARDEX: la entrada es siempre manual por fichero.
- Histórico de comparaciones, tendencias o comparación entre fechas.
- Escritura o corrección de stock en ninguno de los dos sistemas de origen: la herramienta es de
  solo lectura y solo diagnóstico.
- Usuarios nominales, roles, permisos, auditoría de accesos.
- Multi-almacén o multi-centro: se compara un almacén de farmacia.
- Notificaciones, informes programados, envío por correo.
- Uso desde fuera de la red interna del hospital.
- Aplicación móvil o instalable.

## 9. Supuestos

1. Los dos ficheros que se comparan corresponden **al mismo almacén y a un instante equivalente**;
   la coherencia temporal es responsabilidad del usuario, el sistema no la valida.
2. El código de artículo (`Cód.Esp` en FARHOS, `Cod.` en KARDEX) es **la misma clave de negocio**
   en ambos sistemas.
3. El servidor tiene acceso a Internet o el navegador puede alcanzar el CDN de Bootstrap para
   cargar los estilos y el JavaScript de la interfaz.
4. El usuario tiene Excel o equivalente para abrir el fichero exportado.
5. La red interna es de confianza y la contraseña compartida no circula fuera del servicio.

## 10. Cuestiones abiertas

| # | Cuestión | Impacto |
|---|---|---|
| Q1 | Un mismo código con **descripciones distintas** en un origen genera varias filas depuradas; al fusionar por código puede multiplicar filas en la comparativa. ¿Debe la clave de consolidación ser solo el código? | Corrección del recuento de diferencias |
| Q2 | Un artículo presente en KARDEX y ausente en FARHOS no se marca de ninguna forma especial (no es «externo»). ¿Necesita categoría propia? | Interpretación del informe |
| Q3 | Los ficheros subidos se acumulan en el servidor sin política de borrado. ¿Retención y purga? | Espacio en disco, confidencialidad |
| Q4 | ¿Debe validarse que el fichero de FARHOS es realmente de FARHOS y el de KARDEX de KARDEX, para evitar que el usuario los intercambie? | Prevención de error de usuario |
| Q5 | ¿Interesa exportar también la vista **filtrada** que el usuario tiene en pantalla, y no solo el conjunto completo? | Utilidad de la exportación |
