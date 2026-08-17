"""
Ventana principal del Sistema de Vacunación.
Se abre después de un login exitoso.
"""

import customtkinter as ctk

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class VentanaPrincipal(ctk.CTk):
    def __init__(self, usuario_logueado):
        """
        usuario_logueado: sqlite3.Row con los datos del usuario que inició sesión
        (viene desde VentanaLogin -> al_loguear_exitoso).
        """
        super().__init__()

        self.usuario_logueado = usuario_logueado

        self.title("Sistema de Vacunación - Panel principal")
        self.geometry("900x560")

        self._construir_widgets()

    def _construir_widgets(self):
        # --- Barra superior con datos del usuario logueado ---
        barra_superior = ctk.CTkFrame(self, height=50, corner_radius=0)
        barra_superior.pack(side="top", fill="x")

        texto_usuario = f"Usuario: {self.usuario_logueado['nombre']} {self.usuario_logueado['apellido']}"
        ctk.CTkLabel(barra_superior, text=texto_usuario).pack(side="left", padx=20, pady=10)

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

    # --- Callbacks del menú (por ahora placeholders, se van a completar
    #     a medida que armemos cada pantalla) ---
    def _ir_a_importar_csv(self):
        self._limpiar_area_contenido()
        ctk.CTkLabel(self.area_contenido, text="Módulo de Importación de CSV (pendiente)").pack(pady=40)

    def _ir_a_vacunas(self):
        self._limpiar_area_contenido()
        ctk.CTkLabel(self.area_contenido, text="Módulo de Vacunas (pendiente)").pack(pady=40)

    def _ir_a_aplicaciones(self):
        self._limpiar_area_contenido()
        ctk.CTkLabel(self.area_contenido, text="Módulo de Aplicación de dosis (pendiente)").pack(pady=40)

    def _ir_a_stock(self):
        self._limpiar_area_contenido()
        ctk.CTkLabel(self.area_contenido, text="Módulo de Stock (pendiente)").pack(pady=40)

    def _ir_a_transferencias(self):
        self._limpiar_area_contenido()
        ctk.CTkLabel(self.area_contenido, text="Módulo de Transferencias (pendiente)").pack(pady=40)

    def _ir_a_vacunatorios(self):
        self._limpiar_area_contenido()
        ctk.CTkLabel(self.area_contenido, text="Módulo de Vacunatorios (pendiente)").pack(pady=40)