"""
Panel principal del Sistema de Vacunación.

Implementado como CTkFrame  
"""

from datetime import datetime
from pathlib import Path
import sqlite3
from tkinter import filedialog, messagebox

import customtkinter as ctk

from database.conexion import RUTA_BD
from database.respaldo import crear_respaldo, restaurar_respaldo
from vistas.transferencias import VistaTransferencias
from vistas.vacunas import FrameVacunas
from vistas.importar_csv_vista import FrameImportarCSV
from vistas.vacunatorios_vista import FrameVacunatorios
from vistas.stock_vista import FrameStock
from vistas.notificaciones_vista import FrameNotificaciones


class FramePrincipal(ctk.CTkFrame):
    def __init__(self, master, usuario_logueado):
        """
        master: la ventana raíz (App) donde se monta este frame.
        usuario_logueado: sqlite3.Row con los datos del usuario que
        inició sesión.
        """
        super().__init__(master)
        self.usuario_logueado = usuario_logueado
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
            ("Crear copia de seguridad", self._crear_copia_seguridad),
            ("Restaurar copia", self._restaurar_copia),
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
        
        ###Notificaciones!!
        frame = FrameNotificaciones(self.area_contenido, self.usuario_logueado)
        frame.pack(fill="both", expand=True)



    # --- Callbacks del menú ---
    def _ir_a_transferencias(self):
        """Módulo de Transferencias e Historial de Remitos."""
        self._limpiar_area_contenido()
        vista = VistaTransferencias(self.area_contenido, self.usuario_logueado)
        vista.pack(fill="both", expand=True)

    def _ir_a_vacunas(self):
        self._limpiar_area_contenido()
        frame_vacunas = FrameVacunas(self.area_contenido, usuario_logueado=self.usuario_logueado)
        frame_vacunas.pack(fill="both", expand=True)

    def _ir_a_importar_csv(self):
        self._limpiar_area_contenido()
        frame = FrameImportarCSV(self.area_contenido)
        frame.pack(fill="both", expand=True)

    # --- Placeholders para los módulos que faltan desarrollar ---
    def _ir_a_stock(self):
        self._limpiar_area_contenido()
        frame = FrameStock(self.area_contenido)
        frame.pack(fill="both", expand=True)

    def _ir_a_vacunatorios(self):
        self._limpiar_area_contenido()
        frame = FrameVacunatorios(self.area_contenido)
        frame.pack(fill="both", expand=True)

    def _crear_copia_seguridad(self):
        nombre = f"sistema_vacunacion_{datetime.now():%Y%m%d_%H%M%S}.sqlite3"
        ruta = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            title="Crear copia de seguridad",
            initialdir=str(Path(RUTA_BD).parent),
            initialfile=nombre,
            defaultextension=".sqlite3",
            filetypes=[("Base SQLite", "*.sqlite3 *.db"), ("Todos los archivos", "*")],
        )
        if not ruta:
            return

        destino = Path(ruta)
        if destino.exists() and not messagebox.askyesno(
            "Sobrescribir copia",
            f"El archivo ya existe:\n{destino}\n\n¿Querés reemplazarlo?",
            parent=self.winfo_toplevel(),
        ):
            return

        try:
            creado = crear_respaldo(destino)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as error:
            messagebox.showerror(
                "No se pudo crear la copia",
                str(error),
                parent=self.winfo_toplevel(),
            )
            return

        messagebox.showinfo(
            "Copia creada",
            f"La copia de seguridad se guardó en:\n{creado}\n\n"
            "El archivo puede contener datos personales; guardalo en un lugar seguro.",
            parent=self.winfo_toplevel(),
        )

    def _restaurar_copia(self):
        ruta = filedialog.askopenfilename(
            parent=self.winfo_toplevel(),
            title="Seleccionar copia para restaurar",
            initialdir=str(Path(RUTA_BD).parent),
            filetypes=[("Bases SQLite", "*.sqlite3 *.db"), ("Todos los archivos", "*")],
        )
        if not ruta:
            return

        if not messagebox.askyesno(
            "Confirmar restauración",
            "La restauración reemplazará todos los datos actuales por los de la "
            "copia seleccionada. Se guardará automáticamente una copia de la "
            "base actual antes de continuar. Cerrá otras instancias del sistema "
            "antes de restaurar.\n\n¿Querés restaurar esta copia?",
            icon="warning",
            parent=self.winfo_toplevel(),
        ):
            return

        try:
            respaldo_previo = restaurar_respaldo(ruta)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as error:
            messagebox.showerror(
                "No se pudo restaurar la copia",
                str(error),
                parent=self.winfo_toplevel(),
            )
            return

        messagebox.showinfo(
            "Restauración completada",
            f"Se restauró la copia seleccionada.\n"
            f"La base anterior quedó respaldada en:\n{respaldo_previo}\n\n"
            "Volverás al inicio de sesión para cargar los datos restaurados.",
            parent=self.winfo_toplevel(),
        )
        self.winfo_toplevel().mostrar_login()