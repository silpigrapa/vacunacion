"""
Punto de entrada del Sistema de Vacunación.


"""

import customtkinter as ctk
from database.conexion import inicializar_base_de_datos
from vistas.login import FrameLogin
from vistas.ventana_principal import FramePrincipal

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("green")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Vacunación")
        self.frame_actual = None
        self.mostrar_login()

    def _cambiar_frame(self, frame_nuevo):
        if self.frame_actual is not None:
            self.frame_actual.destroy()
        self.frame_actual = frame_nuevo
        self.frame_actual.pack(fill="both", expand=True)

    def mostrar_login(self):
        self.geometry("380x320")
        self.resizable(False, False)
        frame = FrameLogin(self, al_loguear_exitoso=self.mostrar_principal)
        self._cambiar_frame(frame)

    def mostrar_principal(self, usuario_logueado):
        self.resizable(True, True)
        self.geometry("900x560")
        frame = FramePrincipal(self, usuario_logueado)
        self._cambiar_frame(frame)


if __name__ == "__main__":
    inicializar_base_de_datos()
    app = App()
    app.mainloop()