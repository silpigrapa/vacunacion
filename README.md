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