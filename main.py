"""
Punto de entrada del Sistema de Vacunación.
"""

from database.conexion import inicializar_base_de_datos
from vistas.login import VentanaLogin
from vistas.ventana_principal import VentanaPrincipal


def abrir_ventana_principal(usuario_logueado):
    """
    Se llama automáticamente desde VentanaLogin cuando el login es exitoso.
    """
    app_principal = VentanaPrincipal(usuario_logueado)
    app_principal.mainloop()


if __name__ == "__main__":
    inicializar_base_de_datos()

    ventana_login = VentanaLogin(al_loguear_exitoso=abrir_ventana_principal)
    ventana_login.mainloop()