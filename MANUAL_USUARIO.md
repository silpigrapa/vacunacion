# Manual de uso del Sistema de Vacunación

## Iniciar sesión

Abrí el sistema y escribí tu usuario y contraseña en la pantalla de ingreso.
También podés presionar **Enter** después de escribir la contraseña. Si las
credenciales no coinciden, revisá que estén bien escritas y volvé a intentarlo.
Si no tenés credenciales o no podés ingresar, contactá a la persona responsable
de administrar el sistema.

Al ingresar, la barra superior muestra el nombre de la persona que inició
sesión. La pantalla principal contiene el menú de módulos y muestra las
notificaciones disponibles.

## Consultar notificaciones

En la pantalla principal se muestran avisos de lotes próximos a vencer o
vencidos y de vacunas cuyo stock llegó al umbral configurado. Usá **Actualizar**
para volver a consultar la información. Los umbrales se pueden cambiar desde
esta pantalla. El stock bajo se revisa por separado en todos los vacunatorios:
si cualquiera llega al umbral, el aviso indica el centro correspondiente. El
umbral se configura una vez por vacuna y se aplica a cada vacunatorio; el aviso
se genera cuando quedan esa cantidad de ampollas o menos. También podés ocultar
o volver a mostrar las notificaciones.

## Gestionar vacunas y registrar ingresos

En **Vacunas**, la pestaña **Cargar Vacunas** permite registrar la llegada de
un lote al vacunatorio central. Completá el nombre de la vacuna, el fabricante
(si corresponde), las dosis requeridas por paciente y las dosis por ampolla.
Luego indicá el número de lote, la fecha de vencimiento y la cantidad de
ampollas recibidas. La fecha se elige en el calendario. Presioná **Guardar
llegada** para registrar los datos; **Limpiar** borra lo ingresado en el
formulario.

Si el nombre de la vacuna ya existe, el sistema usa la vacuna del catálogo.
Si todavía no existe, la crea. Revisá el nombre antes de guardar para evitar
duplicados escritos de manera diferente.

En la pestaña **Listado**, las subpestañas **Catálogo** y **Lotes ingresados**
permiten consultar las vacunas y los lotes registrados. El botón **Actualizar**
vuelve a cargar los datos.

## Consultar el stock

Abrí **Stock / Ampollas** y seleccioná un vacunatorio o **Todos** para filtrar
la información. **Actualizar** vuelve a cargar los resultados. Las tarjetas
resumen vacunas, ampollas y dosis vigentes, además de las dosis vencidas por
separado. Las pestañas permiten consultar
el stock por vacuna, comparar una vacuna entre vacunatorios (se muestran por
separado las ampollas y las dosis vigentes) y ver el detalle de las ampollas,
su lote, vencimiento, dosis restantes y estado. Los totales de stock disponible
no cuentan lotes vencidos; estos siguen apareciendo como vencidos en el detalle.

La pantalla de stock es de consulta. Para registrar una llegada usá
**Vacunas**; para mover ampollas entre vacunatorios usá **Transferencias**.

## Administrar vacunatorios

En **Vacunatorios** podés crear, editar o eliminar vacunatorios y completar su
nombre, dirección y teléfono. El vacunatorio central es el punto de ingreso
inicial de los lotes y se marca al crear el primero si todavía no hay uno.
Completá las direcciones pendientes, especialmente las de establecimientos
creados durante una importación.

Antes de eliminar un vacunatorio, revisá la confirmación y el mensaje que
muestre el sistema. Si no se puede eliminar por sus relaciones con otros
registros, conservá el vacunatorio y consultá a la persona responsable.

## Importar aplicaciones desde un archivo CSV

1. Entrá en **Importar aplicaciones (CSV)** y seleccioná el archivo exportado
   desde SISA.
2. Presioná **Detectar vacunatorios faltantes** para comparar los
   establecimientos del archivo con los vacunatorios cargados.
3. Revisá la lista. Si corresponde, marcá los establecimientos que querés
   crear y presioná **Crear vacunatorios seleccionados**. Se crean con la
   dirección pendiente de completar; luego podés actualizarla en
   **Vacunatorios**.
4. Presioná **Importar** y esperá a que termine. Consultá el resumen o el
   detalle de error que aparece en pantalla.

La importación guarda los nombres de vacunas detectados en el archivo como
opciones para el formulario de **Vacunas**. Revisá el resultado de la
importación y corregí cualquier dato pendiente antes de continuar con la carga
habitual.

## Emitir y consultar transferencias

En **Transferencias**, presioná **Nueva Transferencia (Emitir Remito)**.
Completá el número de remito, elegí el vacunatorio de destino, seleccioná las
ampollas disponibles para enviar y, si hace falta, agregá observaciones.
Presioná **Emitir Remito y Transferir** para confirmar el movimiento.

La tabla superior muestra los remitos relacionados con el vacunatorio de la
persona que inició sesión. Seleccioná un remito para ver abajo las ampollas
incluidas, sus lotes, vencimientos, dosis y estado.

## Crear una copia de seguridad

Desde el menú, elegí **Crear copia de seguridad**, indicá la carpeta y el
nombre del archivo y guardalo en un lugar protegido. Las copias contienen los
datos de la aplicación; evitá compartirlas y conservá una copia en un
dispositivo distinto del que contiene la base activa. El sistema no crea
copias periódicas automáticamente.

## Restaurar una copia

Usá **Restaurar copia** solo cuando sea necesario volver a una copia anterior.
Seleccioná el archivo y leé la confirmación: se reemplazarán los datos actuales.
La aplicación guarda una copia automática de la base actual antes de
reemplazarla. Cerrá cualquier otra instancia del sistema antes de confirmar.
Al finalizar, volverás a la pantalla de inicio de sesión.

Si la copia no pasa las validaciones, no se restaura; elegí otra copia o
contactá a la persona responsable. No borres la base actual ni la copia previa
generada por la restauración hasta confirmar que los datos restaurados son los
correctos.

## Verificar integridad y atender alertas

La opción **Verificar integridad** revisa la base y muestra los problemas que
encuentra. La revisión no corrige registros. Si aparecen hallazgos, no edites
la base directamente para intentar repararlos: guardá el mensaje y consultá a
la persona responsable del sistema.

El sistema también avisa si detecta cambios hechos directamente en la base de
datos o si faltan mecanismos de auditoría. Ante cualquiera de esas alertas,
anotá el mensaje y la fecha, no continúes modificando los datos hasta consultar
con la persona responsable y verificá la integridad. La alerta permite
detectar ciertos cambios, pero no identifica quién los hizo ni puede recuperar
modificaciones que no quedaron registradas.

## Buenas prácticas

- Verificá vacuna, lote, vencimiento y cantidades antes de guardar.
- Revisá el destinatario y las ampollas antes de emitir una transferencia.
- Creá copias de seguridad con regularidad y protegé los archivos.
- No compartas la contraseña ni los archivos de respaldo.
- Ante errores o alertas, guardá el texto del mensaje y pedí asistencia; no
  manipules directamente el archivo de la base de datos.
