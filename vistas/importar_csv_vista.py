"""
Pantalla de Importación de CSV (aplicaciones de SISA).

Incluye un paso previo de "detección de vacunatorios faltantes": antes
de importar, escanea el archivo y compara los nombres de la columna
'Establecimiento' contra los VACUNATORIO ya cargados, permitiendo
revisar y crear manualmente (con casillas) los que el usuario decida,
con el nombre exacto del CSV, para que el matching funcione a la
primera. Los establecimientos NO se crean automáticamente durante la
importación: solo los que el usuario elige acá.
"""

import customtkinter as ctk
from tkinter import filedialog

from modelos.importador_csv import importar_csv, obtener_establecimientos_del_csv
from modelos.vacunatorio import crear_vacunatorio, listar_vacunatorios


class FrameImportarCSV(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.ruta_seleccionada = None
        self.casillas_faltantes = {}  # nombre_establecimiento -> CTkCheckBox
        self._construir_widgets()

    def _construir_widgets(self):
        ctk.CTkLabel(
            self, text="Importar aplicaciones desde CSV (SISA)",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(10, 20), anchor="w", padx=10)

        # --- Selección de archivo ---
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

        # --- Botones de detección e importación ---
        fila_botones = ctk.CTkFrame(self, fg_color="transparent")
        fila_botones.pack(fill="x", padx=10, pady=(15, 5))

        self.boton_detectar = ctk.CTkButton(
            fila_botones, text="Detectar vacunatorios faltantes",
            command=self._detectar_faltantes, state="disabled"
        )
        self.boton_detectar.pack(side="left")

        self.boton_importar = ctk.CTkButton(
            fila_botones, text="Importar", command=self._ejecutar_importacion,
            state="disabled"
        )
        self.boton_importar.pack(side="left", padx=10)

        self.etiqueta_estado = ctk.CTkLabel(self, text="", text_color="gray")
        self.etiqueta_estado.pack(padx=10, anchor="w")

        # --- Zona de vacunatorios faltantes (se llena dinámicamente) ---
        self.marco_faltantes = ctk.CTkFrame(self, fg_color="transparent")
        self.marco_faltantes.pack(fill="x", padx=10, pady=(5, 5))

        # --- Resultado de la importación ---
        self.caja_resultado = ctk.CTkTextbox(self, height=240, state="disabled")
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
        self.boton_detectar.configure(state="normal")
        self.etiqueta_estado.configure(text="")
        self._limpiar_marco_faltantes()

    def _limpiar_marco_faltantes(self):
        for widget in self.marco_faltantes.winfo_children():
            widget.destroy()
        self.casillas_faltantes = {}

    def _detectar_faltantes(self):
        if not self.ruta_seleccionada:
            return

        self.etiqueta_estado.configure(text="Analizando archivo...")
        self.update_idletasks()

        try:
            establecimientos_csv = obtener_establecimientos_del_csv(self.ruta_seleccionada)
        except Exception as error:
            self.etiqueta_estado.configure(text=f"No se pudo analizar el archivo: {error}")
            return

        nombres_cargados = {v["nombre"] for v in listar_vacunatorios()}
        faltantes = sorted(establecimientos_csv - nombres_cargados)

        self._limpiar_marco_faltantes()

        if not faltantes:
            self.etiqueta_estado.configure(
                text="Todos los establecimientos del archivo ya tienen un vacunatorio cargado."
            )
            return

        self.etiqueta_estado.configure(
            text=f"Se encontraron {len(faltantes)} establecimientos sin vacunatorio cargado. "
                 f"Elegí cuáles crear:"
        )

        marco_scroll = ctk.CTkScrollableFrame(self.marco_faltantes, height=180)
        marco_scroll.pack(fill="x", pady=(5, 5))

        for nombre in faltantes:
            casilla = ctk.CTkCheckBox(marco_scroll, text=nombre)
            # Sin tildar por defecto: se revisa manualmente cuál cargar.
            casilla.pack(anchor="w", pady=2, padx=5)
            self.casillas_faltantes[nombre] = casilla

        ctk.CTkButton(
            self.marco_faltantes, text="Crear vacunatorios seleccionados",
            command=self._crear_vacunatorios_seleccionados,
        ).pack(anchor="w", pady=(5, 0))

    def _crear_vacunatorios_seleccionados(self):
        seleccionados = [
            nombre for nombre, casilla in self.casillas_faltantes.items()
            if casilla.get() == 1
        ]

        if not seleccionados:
            self.etiqueta_estado.configure(text="No seleccionaste ningún establecimiento.")
            return

        for nombre in seleccionados:
            crear_vacunatorio(
                nombre=nombre,
                direccion="Pendiente de completar",
                telefono=None,
                es_central=False,
            )

        self.etiqueta_estado.configure(
            text=(
                f"Se crearon {len(seleccionados)} vacunatorios (con dirección pendiente "
                f"de completar). Ya podés importar el archivo."
            )
        )
        self._limpiar_marco_faltantes()

    def _ejecutar_importacion(self):
        if not self.ruta_seleccionada:
            return

        self.boton_importar.configure(state="disabled")
        self.boton_seleccionar.configure(state="disabled")
        self.boton_detectar.configure(state="disabled")
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
            self.boton_detectar.configure(state="normal")

    def _mostrar_resumen(self, resumen):
        establecimientos = resumen.get("establecimientos_no_encontrados", set())

        texto = (
            f"Filas totales en el archivo:      {resumen['total_filas']}\n"
            f"Aplicaciones importadas:          {resumen['importadas']}\n"
            f"Ya importadas antes (duplicadas): {resumen['duplicadas']}\n"
            f"Sin vacunatorio coincidente (descartadas): {resumen['sin_vacunatorio']}\n"
            f"Sin lote coincidente (sin descuento de stock): {resumen['sin_lote']}\n"
            f"Lote coincidió pero sin stock:     {resumen['sin_stock']}\n"
        )

        if establecimientos:
            texto += (
                f"\nEstablecimientos del archivo que todavía no tienen vacunatorio "
                f"cargado ({len(establecimientos)}):\n"
            )
            for nombre in sorted(establecimientos):
                texto += f"  - {nombre}\n"
            texto += "\nUsá 'Detectar vacunatorios faltantes' para revisarlos y cargar los que correspondan.\n"

        self._escribir_en_caja(texto)

    def _mostrar_error(self, error):
        self._escribir_en_caja(f"Ocurrió un error al importar el archivo:\n\n{error}")

    def _escribir_en_caja(self, texto):
        self.caja_resultado.configure(state="normal")
        self.caja_resultado.delete("1.0", "end")
        self.caja_resultado.insert("1.0", texto)
        self.caja_resultado.configure(state="disabled")