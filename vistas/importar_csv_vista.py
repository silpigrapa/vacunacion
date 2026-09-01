"""
Pantalla de Importación de CSV (SISA).

Los vacunatorios que aparecen en el CSV pero no están cargados se
crean automáticamente durante la importación ( importador_csv.py),
así que esta pantalla solo necesita elegir el archivo e importar.
"""

import customtkinter as ctk
from tkinter import filedialog

from modelos.importador_csv import importar_csv


class FrameImportarCSV(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.ruta_seleccionada = None
        self._construir_widgets()

    def _construir_widgets(self):
        ctk.CTkLabel(
            self, text="Importar aplicaciones desde CSV (SISA)",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(10, 20), anchor="w", padx=10)

        fila_archivo = ctk.CTkFrame(self, fg_color="transparent")
        fila_archivo.pack(fill="x", padx=10, pady=5)

        self.boton_seleccionar = ctk.CTkButton(
            fila_archivo, text="Seleccionar archivo CSV...",
            command=self._seleccionar_archivo
        )
        self.boton_seleccionar.pack(side="left")

        self.etiqueta_archivo = ctk.CTkLabel(
            fila_archivo, text="(ningún archivo seleccionado)", text_color="gray"
        )
        self.etiqueta_archivo.pack(side="left", padx=15)

        self.boton_importar = ctk.CTkButton(
            self, text="Importar", command=self._ejecutar_importacion,
            state="disabled"
        )
        self.boton_importar.pack(padx=10, pady=15, anchor="w")

        self.etiqueta_estado = ctk.CTkLabel(self, text="", text_color="gray")
        self.etiqueta_estado.pack(padx=10, anchor="w")

        self.caja_resultado = ctk.CTkTextbox(self, height=280, state="disabled")
        self.caja_resultado.pack(fill="both", expand=True, padx=10, pady=(10, 10))

    def _seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo CSV de aplicaciones",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
        )
        if not ruta:
            return

        self.ruta_seleccionada = ruta
        self.etiqueta_archivo.configure(text=ruta, text_color=("black", "white"))
        self.boton_importar.configure(state="normal")
        self.etiqueta_estado.configure(text="")

    def _ejecutar_importacion(self):
        if not self.ruta_seleccionada:
            return

        self.boton_importar.configure(state="disabled")
        self.boton_seleccionar.configure(state="disabled")
        self.etiqueta_estado.configure(text="Procesando archivo, puede tardar unos segundos...")
        self.update_idletasks()

        try:
            resumen = importar_csv(self.ruta_seleccionada)
            self._mostrar_resumen(resumen)
            self.etiqueta_estado.configure(text="Importación finalizada.")
        except Exception as error:
            self._mostrar_error(error)
            self.etiqueta_estado.configure(text="La importación falló. Ver detalle abajo.")
        finally:
            self.boton_importar.configure(state="normal")
            self.boton_seleccionar.configure(state="normal")

    def _mostrar_resumen(self, resumen):
        creados = resumen.get("establecimientos_creados", set())

        texto = (
            f"Filas totales en el archivo:      {resumen['total_filas']}\n"
            f"Aplicaciones importadas:          {resumen['importadas']}\n"
            f"Ya importadas antes (duplicadas): {resumen['duplicadas']}\n"
            f"Vacunatorios creados automáticamente: {resumen['vacunatorios_creados']}\n"
            f"Sin lote coincidente (sin descuento de stock): {resumen['sin_lote']}\n"
            f"Lote coincidió pero sin stock:     {resumen['sin_stock']}\n"
        )

        if creados:
            texto += (
                f"\nVacunatorios creados automáticamente en esta importación "
                f"({len(creados)}) — completá su dirección real desde la "
                f"pantalla de Vacunatorios:\n"
            )
            for nombre in sorted(creados):
                texto += f"  - {nombre}\n"

        self._escribir_en_caja(texto)

    def _mostrar_error(self, error):
        self._escribir_en_caja(f"Ocurrió un error al importar el archivo:\n\n{error}")

    def _escribir_en_caja(self, texto):
        self.caja_resultado.configure(state="normal")
        self.caja_resultado.delete("1.0", "end")
        self.caja_resultado.insert("1.0", texto)
        self.caja_resultado.configure(state="disabled")