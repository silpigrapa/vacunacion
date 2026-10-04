"""
Script rápido para restablecer o crear un nuevo usuario en la base de datos.
"""
from database.conexion import inicializar_base_de_datos, obtener_conexion
from modelos.usuario import crear_usuario
from modelos.vacunatorio import listar_vacunatorios, crear_vacunatorio

def registrar_nuevo():
    # Nos aseguramos de que existan las tablas
    inicializar_base_de_datos()

    # 1. Verificar si hay al menos un vacunatorio en la BD
    vacunatorios = listar_vacunatorios()
    
    if not vacunatorios:
        print("No hay vacunatorios en la BD. Creando uno por defecto...")
        id_vacunatorio = crear_vacunatorio(
            nombre="Centro Central CIC", 
            direccion="Av. Principal 123", 
            telefono="4444-1111", 
            es_central=True
        )
    else:
        # Asignamos al primer vacunatorio registrado (normalmente el central)
        id_vacunatorio = vacunatorios[0]["id_vacunatorio"]
        print(f"Asignando usuario al vacunatorio: {vacunatorios[0]['nombre']}")

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
            "UPDATE USUARIO SET contrasena = ? WHERE usuario = ?",
            (clave_hash, nuevo_usuario)
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