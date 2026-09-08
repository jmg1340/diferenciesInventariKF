# Constitution — Comparador d'Inventaris FARHOS ↔ KARDEX

**Versión:** 1.0.0
**Ratificada:** 2026-09-08
**Última enmienda:** 2026-09-08
**Ámbito:** repositorio `diferenciesInventariKF` (aplicación Flask de conciliación de inventarios de farmacia hospitalaria).

Este documento define los principios no negociables del proyecto. `spec.md` describe *qué* hace
el sistema, `plan.md` *cómo* está construido y `tasks.md` *en qué orden* se ejecuta el trabajo.
Cuando exista conflicto entre documentos, manda esta constitución.

---

## Preámbulo

La aplicación existe para un único propósito: permitir que el personal de farmacia del hospital
detecte, de forma rápida y sin intervención de IT, las divergencias de stock entre el sistema de
gestión farmacéutica **FARHOS** y el almacén automatizado **KARDEX**. Todo lo que no sirva
directamente a ese propósito es fuera de ámbito.

---

## Artículo I — Herramienta operativa, no plataforma

1. El sistema es una **utilidad de un solo caso de uso**: subir dos ficheros, ver diferencias,
   exportar a Excel.
2. **No se introduce persistencia de negocio** (base de datos, histórico de comparaciones,
   maestros de artículos) sin una necesidad operativa demostrada y documentada en `spec.md`.
3. El estado de una comparación vive en la sesión del usuario y en los ficheros subidos. Nada más.
4. Prohibido añadir dependencias de infraestructura nuevas (colas, caches, servicios externos)
   para resolver problemas que un fichero Excel y una petición HTTP ya resuelven.

**Rationale:** el coste de mantenimiento debe permanecer cercano a cero. La aplicación la mantiene
una sola persona y se usa de forma puntual, no continua.

## Artículo II — Los ficheros de origen son contratos frágiles y explícitos

1. Los formatos de entrada (export de FARHOS, informe de contingencia de KARDEX) son **generados
   por sistemas de terceros** que pueden cambiar sin previo aviso.
2. Toda dependencia sobre la forma del fichero —número de filas de cabecera a saltar, nombre exacto
   de columna, prefijo del nombre de hoja— **debe estar declarada en `spec.md`** como parte del
   contrato de datos, nunca solo implícita en el código.
3. Cualquier cambio en la lógica de lectura obliga a actualizar la sección «Contratos de datos» de
   `spec.md` en el mismo cambio.
4. Un fichero que no cumple el contrato debe producir **un mensaje comprensible para el usuario de
   farmacia**, no una traza técnica ni una tabla vacía silenciosa.

**Rationale:** la causa más probable de avería no es un bug propio, sino un cambio de formato
aguas arriba. La documentación del contrato es la herramienta de diagnóstico.

## Artículo III — Corrección de los datos por encima de la comodidad

1. **Ningún dato se inventa.** Un artículo ausente en un inventario se representa con stock `0` y
   se marca explícitamente (columna `externo`), nunca se omite ni se rellena por interpolación.
2. La comparación usa **fusión externa completa** (`outer join`): un artículo presente en
   cualquiera de los dos orígenes aparece en el resultado.
3. La convención de signo de la diferencia es **`Stock FARHOS − Stock KARDEX`**, única y estable.
   Un cambio de signo es un cambio incompatible y requiere enmienda de esta constitución.
4. Los stocks se tratan como **enteros** (`Int64`); los códigos de artículo como **cadenas**
   normalizadas sin sufijo decimal. No se comparan códigos como números.
5. Los duplicados se **consolidan por suma**, nunca se descartan.

**Rationale:** el resultado se usa para decisiones de regularización de stock de medicamentos y
material sanitario. Un dato inventado o un artículo perdido tiene consecuencias reales.

## Artículo IV — Separación entre proceso y presentación

1. `procesador_inventario.py` contiene **toda** la lógica de lectura, depuración y comparación, y
   **no importa Flask** ni conoce el concepto de petición HTTP, sesión o usuario.
2. `app.py` contiene **solo** enrutado, autenticación, gestión de ficheros subidos y renderizado.
   No contiene reglas de negocio sobre inventarios.
3. Las funciones de proceso son **puras respecto a su entrada**: reciben una ruta de fichero y
   devuelven un `DataFrame`, o `None` en caso de error.
4. El filtrado y la búsqueda de resultados son **de cliente** (JavaScript sobre la tabla ya
   renderizada). No se añaden endpoints de servidor para filtrar lo que ya está en el navegador.

**Rationale:** permite validar la lógica de conciliación con un script y dos ficheros, sin
levantar el servidor. Es la única forma barata de probar este sistema.

## Artículo V — La interfaz habla el idioma del usuario

1. La interfaz de usuario está en **catalán**. Es un requisito funcional, no una preferencia.
2. Los mensajes de error visibles indican **qué hacer**, no qué falló internamente.
3. Los detalles técnicos van a los logs del servidor (`journald` vía Gunicorn), nunca a la pantalla.
4. La tabla de resultados debe mostrar siempre **el recuento de registros visibles**: el usuario
   necesita saber cuántas filas está mirando tras aplicar filtros.

## Artículo VI — Seguridad proporcionada al entorno, y honesta sobre sus límites

1. La aplicación se despliega **exclusivamente en la red interna del hospital**, tras un proxy
   inverso. No se expone a Internet.
2. El acceso está protegido por **una contraseña compartida**. Este mecanismo es deliberadamente
   simple y se reconoce como insuficiente para cualquier despliegue fuera de la red interna.
3. **Deuda de seguridad reconocida y documentada** (ver `plan.md` §Riesgos): la contraseña y la
   clave de sesión están fijadas en el código fuente. Mientras no se corrija, el repositorio debe
   tratarse como sensible y no publicarse.
4. Los ficheros subidos contienen datos de stock hospitalario. **No se versionan en git** —
   `dadesCarregades/` permanece en `.gitignore` de forma permanente.
5. Todo nombre de fichero subido pasa por saneamiento (`secure_filename`) antes de tocar el disco.
6. El contenido procedente de los Excel se renderiza **siempre escapado**. Ninguna celda de un
   fichero de origen se inyecta como HTML sin escapar.

**Rationale:** el artículo es honesto por diseño. Documentar la debilidad es lo que permite que la
decisión de asumirla sea consciente y revisable, en lugar de un olvido.

## Artículo VII — Despliegue reproducible y aburrido

1. Ejecución en producción mediante **Gunicorn** sobre socket Unix, gestionado por **systemd**, y
   publicado por **nginx** como proxy inverso.
2. El servidor de desarrollo de Flask (`app.run(debug=True)`) es **solo para desarrollo local** y
   nunca es el proceso de producción.
3. El entorno virtual (`entvirt/`) no se versiona; `requirements.txt` es la única fuente de verdad
   de las dependencias.
4. Los límites de tamaño de subida deben ser **coherentes entre nginx y Flask**. Una discrepancia
   produce errores incomprensibles para el usuario y se considera defecto.

## Artículo VIII — Cambios verificables

1. Todo cambio en la lógica de `procesador_inventario.py` debe verificarse contra **ficheros reales
   de ejemplo** antes de darse por bueno.
2. Los resultados intermedios (depuración FARHOS y depuración KARDEX) se exponen en la interfaz y
   en el Excel exportado como **mecanismo de auditoría**: permiten al usuario comprobar por qué
   sale una diferencia. No se eliminan.
3. La exportación a Excel debe producir **exactamente los mismos datos** que la pantalla, en tres
   hojas: depuración FARHOS, depuración KARDEX, comparativa.

---

## Gobernanza

- **Enmiendas:** cualquier modificación de un artículo requiere actualizar la versión de este
  documento y justificar el cambio en el mensaje de commit.
- **Versionado:** semántico. *Mayor* = se retira o invierte un principio; *menor* = se añade un
  principio o se amplía uno existente; *parche* = aclaración sin cambio de fondo.
- **Prevalencia:** ante duda entre esta constitución y una práctica establecida en el código, manda
  la constitución; el código se considera desviación a corregir o a documentar como excepción
  explícita en `plan.md`.
- **Revisión de conformidad:** al abrir cualquier trabajo descrito en `tasks.md`, comprobar que no
  contradice los Artículos I–VIII.

### Desviaciones vigentes aceptadas

| Artículo | Desviación en el código actual | Estado |
|---|---|---|
| VI.3 | `PASSWORD = "1234"` y `app.secret_key = 'supersecretkey'` en `app.py` | Aceptada temporalmente; corrección en `tasks.md` fase 1 |
| VII.4 | `MAX_CONTENT_LENGTH` = 16 MB en Flask vs `client_max_body_size` = 50 M en nginx | Aceptada; corrección en `tasks.md` fase 1 |
| VIII.1 | No existe suite de pruebas automatizada; la verificación es manual | Aceptada; corrección en `tasks.md` fase 2 |
