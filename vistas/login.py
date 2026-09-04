"""
Pantalla de login del Sistema de Vacunación.
"""

import customtkinter as ctk
from modelos.usuario import validar_login
from estilos import Color, Fuente, RADIO


class FrameLogin(ctk.CTkFrame):
    def __init__(self, master, al_loguear_exitoso):
        """
        master: la ventana raíz (App) donde se monta este frame.
        al_loguear_exitoso: función callback que se llama con el usuario
        logueado (sqlite3.Row) cuando el login es correcto.
        """
        super().__init__(master, fg_color=Color.FONDO_APP, corner_radius=0)
        self.al_loguear_exitoso = al_loguear_exitoso
        self._construir_widgets()

    def _construir_widgets(self):
        # Centramos la tarjeta de login en el medio de la ventana
        contenedor_externo = ctk.CTkFrame(self, fg_color="transparent")
        contenedor_externo.place(relx=0.5, rely=0.5, anchor="center")

        contenedor = ctk.CTkFrame(
            contenedor_externo,
            width=340,
            corner_radius=RADIO,
            fg_color=Color.TARJETA,
            border_width=1,
            border_color=Color.BORDE,
        )
        contenedor.pack(fill="both", expand=True)

        # --- Ícono / marca ---
        ctk.CTkLabel(
            contenedor,
            text="💉",
            font=ctk.CTkFont(size=34),
        ).pack(pady=(36, 4))

        ctk.CTkLabel(
            contenedor, text="Sistema de Vacunación",
            font=Fuente.titulo(),
            text_color=Color.TEXTO,
        ).pack(pady=(0, 2), padx=30)

        ctk.CTkLabel(
            contenedor, text="Ingresá tus credenciales para continuar",
            font=Fuente.chico(),
            text_color=Color.TEXTO_SECUNDARIO,
        ).pack(pady=(0, 22))

        self.campo_usuario = ctk.CTkEntry(
            contenedor,
            placeholder_text="Usuario",
            height=38,
            corner_radius=8,
            border_color=Color.BORDE,
        )
        self.campo_usuario.pack(pady=6, padx=30, fill="x")

        self.campo_contrasena = ctk.CTkEntry(
            contenedor,
            placeholder_text="Contraseña",
            show="*",
            height=38,
            corner_radius=8,
            border_color=Color.BORDE,
        )
        self.campo_contrasena.pack(pady=6, padx=30, fill="x")
        self.campo_contrasena.bind("<Return>", lambda evento: self._intentar_login())

        self.etiqueta_error = ctk.CTkLabel(
            contenedor, text="", text_color=Color.ERROR, font=Fuente.chico()
        )
        self.etiqueta_error.pack(pady=(8, 0))

        boton_ingresar = ctk.CTkButton(
            contenedor,
            text="Ingresar",
            command=self._intentar_login,
            height=40,
            corner_radius=8,
            fg_color=Color.PRIMARIO,
            hover_color=Color.PRIMARIO_HOVER,
            font=Fuente.texto_negrita(),
        )
        boton_ingresar.pack(pady=(14, 30), padx=30, fill="x")

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