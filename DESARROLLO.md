# Documentación técnica para desarrolladores

## Tecnologías y ejecución

El sistema es una aplicación de escritorio en Python, con interfaz
`CustomTkinter` y persistencia en SQLite. La base se crea dentro de
`database/sistema_vacunacion.db`; su esquema inicial está definido en
`database/sistema_vacunacion.sql`. No se requiere un servidor de base de datos.

Para iniciar la aplicación desde la raíz del repositorio:

```bash
python3 main.py
```

El punto de entrada llama a `inicializar_base_de_datos()` antes de abrir la
ventana. Para ejecutar las pruebas automatizadas:

```bash
python3 -m unittest discover -s tests -v
```

La interfaz necesita `CustomTkinter` y una instalación de Python con soporte
para Tk. El repositorio no contiene actualmente un archivo de dependencias;
si se prepara un entorno nuevo, hay que instalar las dependencias externas
que importe el código del proyecto.

## Organización del código

- `main.py`: inicio de la aplicación y navegación entre login y panel.
- `vistas/`: ventanas y componentes de interfaz.
- `modelos/`: operaciones de dominio y consultas de la aplicación.
- `database/conexion.py`: rutas, conexiones SQLite e inicialización.
- `database/sistema_vacunacion.sql`: esquema base de las tablas.
- `database/auditoria.py`: registro de escrituras externas mediante triggers.
- `database/integridad.py`: auditoría de consistencia, de solo lectura.
- `database/respaldo.py`: creación, validación y restauración de copias.
- `tests/`: pruebas automatizadas de auditoría, integridad y respaldos.

## Acceso y escrituras a la base

Los modelos deben obtener conexiones con `database.conexion.obtener_conexion()`.
Este helper activa las claves foráneas, configura el tiempo de espera para
bloqueos y devuelve filas accesibles por nombre. Las consultas deben usar
parámetros (`?`) en lugar de concatenar datos recibidos del usuario.

Cada operación de escritura debe confirmar la transacción con `commit()` y
cerrar la conexión incluso si ocurre un error. Para una operación compuesta,
usar una transacción y hacer `rollback()` ante una excepción. Por ejemplo,
`modelos/vacuna.py::registrar_ingreso_central` crea la vacuna, el lote y sus
ampollas como una sola unidad de trabajo.

El wrapper de conexión marca las escrituras de la aplicación en
`CONTEXTO_ESCRITURA_APP`. Es importante conservar el uso de
`obtener_conexion()` en las operaciones normales: conectarse directamente con
`sqlite3.connect()` omite esa marca y puede producir alertas de cambios
externos o afectar el funcionamiento de la auditoría.

## Auditoría de cambios externos

`instalar_auditoria()` crea las tablas `CONTEXTO_ESCRITURA_APP` y
`CAMBIOS_EXTERNOS`, y genera triggers `INSERT`, `UPDATE` y `DELETE` para las
tablas enumeradas en `TABLAS_AUDITADAS`. Los triggers registran fecha, tabla,
operación e identificador, no el contenido del registro.

Al iniciar, la inicialización comprueba qué elementos estaban ausentes antes
de reinstalar los mecanismos de auditoría y conserva ese aviso para mostrarlo
en el panel. Mientras el panel está abierto, se revisan cada cinco segundos
los elementos faltantes y los eventos todavía no notificados. Para agregar
una tabla al alcance, actualizar `TABLAS_AUDITADAS` y cubrir sus triggers con
pruebas.

Esta auditoría es una señal operativa, no un mecanismo resistente a
manipulación: una persona con acceso suficiente al archivo puede borrar o
modificar triggers, tablas o la base completa. No reconstruye cambios
anteriores a su instalación ni identifica a la persona que hizo una edición.
Si faltaba la tabla de eventos, no se pueden consultar los eventos previos.
Las modificaciones realizadas mientras los triggers estaban ausentes no
pueden recuperarse.

## Integridad y copias de seguridad

`auditar_integridad()` abre la base en modo de solo lectura y comprueba
integridad física de SQLite, esquema requerido, claves foráneas y reglas de
consistencia de dominio. Devuelve una lista de hallazgos; una lista vacía
significa que las comprobaciones implementadas pasaron. No repara datos.

`crear_respaldo()` utiliza la API de respaldo de SQLite para producir una copia
consistente, incluso si la base está en uso. Antes de restaurar,
`restaurar_respaldo()` valida ambas bases, guarda una copia previa y reemplaza
la base activa. La operación rechaza una copia con esquema faltante, errores
de integridad física o violaciones de claves foráneas. Cerrá otras instancias
de la aplicación antes de restaurar.

Al agregar o renombrar una tabla de aplicación, revisar también
`TABLAS_REQUERIDAS` en `database/respaldo.py` y cualquier regla relevante en
`database/integridad.py`. Cambios de esquema para bases ya existentes requieren
una migración: editar el SQL inicial no actualiza automáticamente las bases
que ya fueron creadas.

## Pruebas

Las pruebas crean bases temporales y no deben depender de la base real del
proyecto. El conjunto de cobertura actual se ejecuta con:

```bash
python3 -m unittest discover -s tests -v
```

Cuando se modifica el esquema, el acceso a datos, la auditoría o la
restauración, agregar o actualizar pruebas para la base temporal pertinente y
ejecutar el conjunto completo antes de integrar los cambios.
