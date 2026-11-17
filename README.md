# Sistema de Vacunación

Aplicación de escritorio para administrar vacunas, lotes, stock por
vacunatorio, transferencias y aplicaciones importadas desde archivos CSV. Está
desarrollada en Python, usa CustomTkinter para la interfaz y SQLite para
almacenar los datos localmente.

## Información académica

- **Institución:** Instituto Superior Gaspar L. Benavento
- **Asignatura:** Prácticas Profesionalizantes III
- **Docente de la cátedra:** Delfor Hernán Castro
- **Desarrolladores:**
  - Silvia Graciela Acosta
  - Daián Alejandro Valente
  - Emmanuel León Seghesso
  - Cristian Miguel Risoglio

## Requisitos

- Python 3.
- Tkinter, incluido con muchas instalaciones de Python. En Debian o Ubuntu se
  puede instalar con `sudo apt install python3-tk`.
- Git para clonar el repositorio.

## Instalación y ejecución

La aplicación se ejecuta en el equipo de escritorio y no requiere un servidor
de base de datos. Para instalarla desde una terminal:

```bash
git clone https://github.com/silpigrapa/vacunacion.git
cd vacunacion
python3 -m venv .venv
source .venv/bin/activate
python -m pip install customtkinter
python3 main.py
```

En Windows, activá el entorno virtual con `.venv\Scripts\activate` y ejecutá
la aplicación con `python main.py`. Si Tkinter no está disponible en tu
instalación de Python, instalá el componente Tcl/Tk correspondiente a tu
sistema operativo.

Al iniciar, la aplicación crea o inicializa automáticamente la base SQLite en
`database/sistema_vacunacion.db`. Para volver a abrirla, activá el entorno
virtual y ejecutá `python3 main.py` (en Windows, `python main.py`) desde la
carpeta del proyecto.

## Uso

Iniciá sesión con las credenciales habilitadas para tu instalación. Desde el
menú principal podés:

- consultar notificaciones de vencimientos y stock bajo;
- registrar vacunas y lotes, consultar stock y administrar vacunatorios;
- importar aplicaciones desde un archivo CSV exportado desde SISA;
- emitir y consultar transferencias entre vacunatorios;
- crear o restaurar copias de seguridad y verificar la integridad de los
  registros.

La guía con los pasos detallados para estas tareas está en el
[manual de uso](./MANUAL_USUARIO.md).

## Datos y copias de seguridad

La base de datos se guarda localmente en
`database/sistema_vacunacion.db`. Las copias de seguridad contienen los datos
de la aplicación y pueden incluir información personal: guardalas en una
ubicación protegida y en un dispositivo distinto del que contiene la base
activa. La aplicación no genera copias periódicas automáticamente; quien la
opera debe crear y conservar respaldos con la frecuencia adecuada.

Desde el menú lateral se puede crear una copia manual o restaurar una copia
existente. Al restaurar, el sistema valida la integridad y el esquema del
archivo seleccionado, guarda automáticamente la base actual junto a ella con
el sufijo `_pre_restauracion` antes de reemplazarla y vuelve al inicio de
sesión al terminar. No edites la base directamente.

## Integridad de los registros

La opción **Verificar integridad** comprueba la integridad física de SQLite,
las claves foráneas y algunas reglas de consistencia, como fechas, cantidades
de ampollas y dosis disponibles. La revisión es de solo lectura: informa
hallazgos, pero no modifica ni corrige registros. El alta de vacunas, lotes y
ampollas se guarda como una única transacción para evitar registros parciales
ante un error.

La aplicación también registra y alerta sobre cambios directos en la base de
datos, comprueba que los mecanismos de auditoría estén instalados y avisa
cuando el stock de una vacuna alcanza el umbral en cualquiera de los
vacunatorios. Estas alertas no identifican a quien hizo los cambios ni
protegen contra la manipulación deliberada de la propia base.

## Documentación para desarrolladores

Para conocer la arquitectura, las pruebas y el mantenimiento de la base de
datos, consultá la [documentación técnica](./DESARROLLO.md). Las pruebas se
ejecutan desde la raíz del proyecto con:

```bash
python3 -m unittest discover -s tests -v
```
