"""
Panel principal del Sistema de Vacunación.
I"""

import customtkinter as ctk
from vistas.transferencias import VistaTransferencias


class FramePrincipal(ctk.CTkFrame):
    def __init__(self, master, usuario_logueado):
        """
        master: la ventana raíz (App) donde se monta este frame.
        usuario_logueado: sqlite3.Row con los datos del usuario que
        inició sesión.
        """
        super().__init__(master)
        self.usuario_logueado = usuario_logueado
<<<<<<< HEAD

        self.title("Sistema de Vacunación - Panel principal")
        self.geometry("950x620")

=======
>>>>>>> 2c0ef3611495c9eee5814d7241c3b2eee8c96ba5
        self._construir_widgets()

    def _construir_widgets(self):
        # --- Barra superior con datos del usuario logueado ---
        barra_superior = ctk.CTkFrame(self, height=50, corner_radius=0)
        barra_superior.pack(side="top", fill="x")

        texto_usuario = f"Usuario: {self.usuario_logueado['nombre']} {self.usuario_logueado['apellido']}"
        ctk.CTkLabel(
            barra_superior, 
            text=texto_usuario,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=20, pady=10)

        # --- Menú lateral ---
        menu_lateral = ctk.CTkFrame(self, width=200, corner_radius=0)
        menu_lateral.pack(side="left", fill="y")

        opciones = [
            ("Vacunas", self._ir_a_vacunas),
            ("Importar aplicaciones (CSV)", self._ir_a_importar_csv),
            ("Stock / Ampollas", self._ir_a_stock),
            ("Transferencias", self._ir_a_transferencias),
            ("Vacunatorios", self._ir_a_vacunatorios),
        ]

        for texto, accion in opciones:
            boton = ctk.CTkButton(menu_lateral, text=texto, command=accion, anchor="w")
            boton.pack(fill="x", padx=10, pady=6)

        # --- Área central donde se van a mostrar los distintos módulos ---
        self.area_contenido = ctk.CTkFrame(self)
        self.area_contenido.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self._mostrar_bienvenida()

    def _limpiar_area_contenido(self):
        for widget in self.area_contenido.winfo_children():
            widget.destroy()

    def _mostrar_bienvenida(self):
        self._limpiar_area_contenido()
        ctk.CTkLabel(
            self.area_contenido,
            text="Seleccioná una opción del menú",
            font=ctk.CTkFont(size=16),
        ).pack(pady=40)

<<<<<<< HEAD
    # --- Callbacks del menú ---
    def _ir_a_transferencias(self):
        """Módulo de Transferencias e Historial de Remitos."""
        self._limpiar_area_contenido()
        vista = VistaTransferencias(self.area_contenido, self.usuario_logueado)
        vista.pack(fill="both", expand=True)

    # --- Placeholders para los módulos que iremos desarrollando ---
=======
    # --- Callbacks del menú (placeholders, se completan a medida
    #     que armemos cada pantalla) ---
>>>>>>> 2c0ef3611495c9eee5814d7241c3b2eee8c96ba5
    def _ir_a_importar_csv(self):
        self._limpiar_area_contenido()
        ctk.CTkLabel(self.area_contenido, text="Módulo de Importación de CSV (pendiente)").pack(pady=40)

    def _ir_a_vacunas(self):
        self._limpiar_area_contenido()
        ctk.CTkLabel(self.area_contenido, text="Módulo de Vacunas (pendiente)").pack(pady=40)

    def _ir_a_stock(self):
        self._limpiar_area_contenido()
        ctk.CTkLabel(self.area_contenido, text="Módulo de Stock (pendiente)").pack(pady=40)

    def _ir_a_vacunatorios(self):
        self._limpiar_area_contenido()
        ctk.CTkLabel(self.area_contenido, text="Módulo de Vacunatorios (pendiente)").pack(pady=40)