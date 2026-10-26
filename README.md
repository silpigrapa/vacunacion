# vacunacion

## Copias de seguridad

Desde el menú lateral de la aplicación se puede crear una copia manual de la
base de datos SQLite o restaurar una copia existente. Al restaurar, el sistema
valida la integridad y el esquema del archivo seleccionado y guarda
automáticamente la base actual junto a ella, con el sufijo
`_pre_restauracion`, antes de reemplazarla. La aplicación vuelve al inicio de
sesión al terminar.

Las copias incluyen los datos de la aplicación y pueden contener información
personal. Es conveniente guardarlas en una ubicación protegida y en un
dispositivo diferente del que contiene la base original. La aplicación no
programa copias periódicas:
es responsabilidad de quien la opera crear y conservar respaldos con la
frecuencia adecuada.

## Integridad de los registros

La opción **Verificar integridad** del menú comprueba la integridad física de
SQLite, las claves foráneas y algunas reglas de consistencia del sistema, como
fechas, cantidades de ampollas y dosis disponibles. La revisión es de solo
lectura: informa hallazgos, pero no modifica ni corrige registros. El alta de
vacunas, lotes y ampollas se guarda como una única transacción para evitar
registros parciales ante un error.

La aplicación registra y alerta automáticamente sobre inserciones,
modificaciones y eliminaciones hechas directamente en la base. La revisión se
realiza al abrir el panel principal y cada cinco segundos mientras está
abierto. El registro conserva la fecha, tabla, operación e identificador del
registro, pero no los valores personales. Los cambios externos realizados
antes de habilitar esta función no se pueden recuperar; tampoco es una defensa
contra alguien que altere deliberadamente o reemplace la propia base y sus
triggers de auditoría. Al iniciar y cada cinco segundos, la aplicación también
comprueba que existan las tablas y los triggers de auditoría; si detecta que
faltaban, avisa y reinstala los mecanismos ausentes al iniciar. No puede
recuperar ni confirmar cambios realizados mientras estuvieron deshabilitados.