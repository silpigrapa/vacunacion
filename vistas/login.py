"""
Pantalla de login del Sistema de Vacunación.

"""

import customtkinter as ctk
from modelos.usuario import validar_login


class FrameLogin(ctk.CTkFrame):
    def __init__(self, master, al_loguear_exitoso):
        """
        master: la ventana raíz (App) donde se monta este frame.
        al_loguear_exitoso: función callback que se llama con el usuario
        logueado (sqlite3.Row) cuando el login es correcto.
        """
        super().__init__(master)
        self.al_loguear_exitoso = al_loguear_exitoso
        self._construir_widgets()

    def _construir_widgets(self):
        contenedor = ctk.CTkFrame(self, corner_radius=12)
        contenedor.pack(padx=30, pady=30, fill="both", expand=True)

        titulo = ctk.CTkLabel(
            contenedor, text="Sistema de Vacunación",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        titulo.pack(pady=(20, 25))

        self.campo_usuario = ctk.CTkEntry(contenedor, placeholder_text="Usuario")
        self.campo_usuario.pack(pady=8, padx=20, fill="x")

        self.campo_contrasena = ctk.CTkEntry(
            contenedor, placeholder_text="Contraseña", show="*"
        )
        self.campo_contrasena.pack(pady=8, padx=20, fill="x")
        self.campo_contrasena.bind("<Return>", lambda evento: self._intentar_login())

        self.etiqueta_error = ctk.CTkLabel(contenedor, text="", text_color="red")
        self.etiqueta_error.pack(pady=(0, 5))

        boton_ingresar = ctk.CTkButton(
            contenedor, text="Ingresar", command=self._intentar_login
        )
        boton_ingresar.pack(pady=15, padx=20, fill="x")

    def _intentar_login(self):
        usuario = self.campo_usuario.get().strip()
        contrasena = self.campo_contrasena.get()

        if not usuario or not contrasena:
            self.etiqueta_error.configure(text="Completá usuario y contraseña")
            return

        usuario_encontrado = validar_login(usuario, contrasena)

        if usuario_encontrado is None:
            self.etiqueta_error.configure(text="Usuario o contraseña incorrectos")
            self.campo_contrasena.delete(0, "end")
            return

        # Login correcto: avisamos al callback, que se encarga de
        # cambiar de pantalla (no destruimos ninguna ventana acá).
        self.al_loguear_exitoso(usuario_encontrado)