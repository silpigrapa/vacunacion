"""
Script rápido para restablecer o crear un nuevo usuario en la base de datos.
"""
from database.conexion import inicializar_base_de_datos, obtener_conexion
from modelos.usuario import crear_usuario
from modelos.vacunatorio import (
    listar_vacunatorios,
    crear_vacunatorio,
    obtener_vacunatorio_central,
)

def registrar_nuevo():
    # Nos aseguramos de que existan las tablas
    inicializar_base_de_datos()

    # 1. Asignar siempre al vacunatorio central.
    vacunatorios = listar_vacunatorios()
    if not vacunatorios:
        print("No hay vacunatorios en la BD. Creando el central...")
        crear_vacunatorio(
            nombre="CENTRO INTEGRADOR COMUNITARIO",
            direccion="Pendiente de completar",
            es_central=True,
        )
    vacunatorio_central = obtener_vacunatorio_central()
    if vacunatorio_central is None:
        raise RuntimeError(
            "Hay vacunatorios cargados, pero ninguno está marcado como central. "
            "Marcá el Centro Integrador Comunitario como central y volvé a intentar."
        )
    id_vacunatorio = vacunatorio_central["id_vacunatorio"]
    print(f"Asignando usuario al vacunatorio central: {vacunatorio_central['nombre']}")

    # 2. Datos del nuevo usuario (cambiá usuario y contraseña si querés)
    nuevo_usuario = "admin"
    nueva_clave = "1234"
    
    # Si el usuario ya existía, primero actualizamos su clave hasheada
    from modelos.usuario import hashear_contrasena
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_usuario FROM USUARIO WHERE usuario = ?", (nuevo_usuario,))
    existe = cursor.fetchone()

    if existe:
        clave_hash = hashear_contrasena(nueva_clave)
        cursor.execute(
            """
            UPDATE USUARIO
            SET contrasena = ?, id_vacunatorio = ?
            WHERE usuario = ?
            """,
            (clave_hash, id_vacunatorio, nuevo_usuario),
        )
        conexion.commit()
        print(f"¡Contraseña actualizada correctamente para el usuario '{nuevo_usuario}'!")
    else:
        # Si no existe, lo creamos
        id_usr = crear_usuario("Administrador", "Sistema", nuevo_usuario, nueva_clave, id_vacunatorio)
        print(f"¡Usuario '{nuevo_usuario}' creado con éxito (ID: {id_usr})!")

    conexion.close()

if __name__ == "__main__":
    registrar_nuevo()