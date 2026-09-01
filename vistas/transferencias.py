"""
Vista del Módulo de Transferencias del Sistema de Vacunación.
Permite visualizar el historial de envíos entre centros, ver el detalle
de ampollas de un remito y registrar una nueva transferencia.
"""

import customtkinter as ctk
from datetime import datetime
from tkinter import ttk, messagebox
from modelos.transferencia import (
    listar_transferencias,
    obtener_detalle_transferencia,
    registrar_transferencia
)
from modelos.vacunatorio import listar_vacunatorios
from database.conexion import obtener_conexion


class VistaTransferencias(ctk.CTkFrame):
    def __init__(self, parent, usuario_logueado):
        super().__init__(parent)

        self.usuario_logueado = usuario_logueado

        # Configurar expansión de grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._construir_interfaz()
        self.cargar_transferencias()

    def _construir_interfaz(self):
        # --- Cabecera ---
        marco_cabecera = ctk.CTkFrame(self, fg_color="transparent")
        marco_cabecera.grid(row=0, column=0, padx=15, pady=10, sticky="ew")

        ctk.CTkLabel(
            marco_cabecera,
            text="Gestión de Transferencias y Remitos",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")

        btn_nueva = ctk.CTkButton(
            marco_cabecera,
            text="+ Nueva Transferencia",
            command=self._abrir_modal_nueva_transferencia
        )
        btn_nueva.pack(side="right")

        # --- Contenido Principal (Dividido en 2 secciones: Historial y Detalle) ---
        panel_principal = ctk.CTkFrame(self)
        panel_principal.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        panel_principal.grid_columnconfigure(0, weight=1)
        panel_principal.grid_rowconfigure(0, weight=1)
        panel_principal.grid_rowconfigure(1, weight=1)

        # 1. Tabla de Historial de Remitos
        frame_historial = ctk.CTkFrame(panel_principal)
        frame_historial.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        frame_historial.grid_columnconfigure(0, weight=1)
        frame_historial.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            frame_historial,
            text="Historial de Remitos Emitidos/Recibidos",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Estilo para Treeview de Tkinter integrado en CustomTkinter
        estilo = ttk.Style()
        estilo.theme_use("default")
        estilo.configure("Treeview", rowheight=25, font=("Arial", 10))
        estilo.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        columnas_transf = ("id", "remito", "fecha", "origen", "destino", "usuario", "obs")
        self.tabla_transf = ttk.Treeview(
            frame_historial, columns=columnas_transf, show="headings", selectmode="browse"
        )
        self.tabla_transf.heading("id", text="ID")
        self.tabla_transf.heading("remito", text="N° Remito")
        self.tabla_transf.heading("fecha", text="Fecha")
        self.tabla_transf.heading("origen", text="Origen")
        self.tabla_transf.heading("destino", text="Destino")
        self.tabla_transf.heading("usuario", text="Usuario")
        self.tabla_transf.heading("obs", text="Observaciones")

        self.tabla_transf.column("id", width=40, anchor="center")
        self.tabla_transf.column("remito", width=110, anchor="center")
        self.tabla_transf.column("fecha", width=130, anchor="center")
        self.tabla_transf.column("origen", width=160, anchor="w")
        self.tabla_transf.column("destino", width=160, anchor="w")
        self.tabla_transf.column("usuario", width=140, anchor="w")
        self.tabla_transf.column("obs", width=180, anchor="w")

        scroll_transf = ttk.Scrollbar(frame_historial, orient="vertical", command=self.tabla_transf.yview)
        self.tabla_transf.configure(yscrollcommand=scroll_transf.set)

        self.tabla_transf.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=5)
        scroll_transf.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=5)

        self.tabla_transf.bind("<<TreeviewSelect>>", self._al_seleccionar_transferencia)

        # 2. Tabla de Detalle de Ampollas enviadas
        frame_detalle = ctk.CTkFrame(panel_principal)
        frame_detalle.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        frame_detalle.grid_columnconfigure(0, weight=1)
        frame_detalle.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            frame_detalle,
            text="Detalle de Ampollas del Remito Seleccionado",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        columnas_det = ("id_ampolla", "vacuna", "lote", "vencimiento", "dosis", "estado")
        self.tabla_detalle = ttk.Treeview(
            frame_detalle, columns=columnas_det, show="headings", selectmode="browse"
        )
        self.tabla_detalle.heading("id_ampolla", text="ID Ampolla")
        self.tabla_detalle.heading("vacuna", text="Vacuna")
        self.tabla_detalle.heading("lote", text="N° Lote")
        self.tabla_detalle.heading("vencimiento", text="Vencimiento")
        self.tabla_detalle.heading("dosis", text="Dosis Disponibles")
        self.tabla_detalle.heading("estado", text="Estado Ampolla")

        self.tabla_detalle.column("id_ampolla", width=80, anchor="center")
        self.tabla_detalle.column("vacuna", width=200, anchor="w")
        self.tabla_detalle.column("lote", width=120, anchor="center")
        self.tabla_detalle.column("vencimiento", width=110, anchor="center")
        self.tabla_detalle.column("dosis", width=120, anchor="center")
        self.tabla_detalle.column("estado", width=120, anchor="center")

        scroll_det = ttk.Scrollbar(frame_detalle, orient="vertical", command=self.tabla_detalle.yview)
        self.tabla_detalle.configure(yscrollcommand=scroll_det.set)

        self.tabla_detalle.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=5)
        scroll_det.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=5)

    def cargar_transferencias(self):
        """Carga la lista de transferencias desde la base de datos."""
        for item in self.tabla_transf.get_children():
            self.tabla_transf.delete(item)

        # Limpiar detalle también
        for item in self.tabla_detalle.get_children():
            self.tabla_detalle.delete(item)

        # Filtrar por vacunatorio del usuario actual
        id_vac = self.usuario_logueado["id_vacunatorio"]
        transferencias = listar_transferencias(id_vacunatorio=id_vac)

        for t in transferencias:
            self.tabla_transf.insert(
                "",
                "end",
                values=(
                    t["id_transferencia"],
                    t["numero_remito"],
                    t["fecha"],
                    t["origen"],
                    t["destino"],
                    t["usuario"],
                    t["observaciones"] or "-",
                ),
            )

    def _al_seleccionar_transferencia(self, event):
        """Carga el detalle de ampollas cuando el usuario selecciona un remito."""
        seleccion = self.tabla_transf.selection()
        if not seleccion:
            return

        item = self.tabla_transf.item(seleccion[0])
        id_transferencia = item["values"][0]

        for elem in self.tabla_detalle.get_children():
            self.tabla_detalle.delete(elem)

        detalles = obtener_detalle_transferencia(id_transferencia)
        for d in detalles:
            estado_ampolla = "Abierta" if d["fecha_apertura"] else "Cerrada"
            self.tabla_detalle.insert(
                "",
                "end",
                values=(
                    d["id_ampolla"],
                    d["vacuna_nombre"],
                    d["numero_lote"],
                    d["fecha_vencimiento"],
                    d["dosis_disponibles"],
                    estado_ampolla,
                ),
            )

    def _abrir_modal_nueva_transferencia(self):
        """Abre un diálogo/modal para registrar un nuevo remito."""
        VentanaNuevaTransferencia(self, self.usuario_logueado, self.cargar_transferencias)


class VentanaNuevaTransferencia(ctk.CTkToplevel):
    def __init__(self, parent, usuario_logueado, al_guardar_callback):
        super().__init__(parent)

        self.usuario_logueado = usuario_logueado
        self.al_guardar_callback = al_guardar_callback

        self.title("Registrar Nueva Transferencia")
        self.geometry("620x520")
        self.grab_set()  # Modal

        self.ampollas_seleccionadas = []

        self._construir_formulario()

    def _construir_formulario(self):
        # Generar un nro de remito automático
        nro_remito_sugerido = f"REM-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Datos básicos
        lbl_remito = ctk.CTkLabel(self, text="Número de Remito:")
        lbl_remito.pack(anchor="w", padx=20, pady=(15, 2))
        self.txt_remito = ctk.CTkEntry(self)
        self.txt_remito.insert(0, nro_remito_sugerido)
        self.txt_remito.pack(fill="x", padx=20)

        # Destino
        lbl_destino = ctk.CTkLabel(self, text="Vacunatorio Destino:")
        lbl_destino.pack(anchor="w", padx=20, pady=(10, 2))

        # Cargar vacunatorios excluyendo el de origen
        self.vacunatorios = listar_vacunatorios()
        opciones_dest = [
            v["nombre"] for v in self.vacunatorios 
            if v["id_vacunatorio"] != self.usuario_logueado["id_vacunatorio"]
        ]

        self.combo_destino = ctk.CTkComboBox(self, values=opciones_dest or ["No hay otros vacunatorios"])
        self.combo_destino.pack(fill="x", padx=20)

        # Selección de ampollas disponibles en origen
        lbl_ampollas = ctk.CTkLabel(self, text="Ampollas a Transferir (Disponibles en el centro actual):")
        lbl_ampollas.pack(anchor="w", padx=20, pady=(10, 2))

        # Lista multiselección para ampollas
        frame_lista = ctk.CTkFrame(self)
        frame_lista.pack(fill="both", expand=True, padx=20, pady=5)

        self.ampollas_disponibles = self._obtener_ampollas_origen()
        
        self.checkboxes_ampollas = []
        scroll_ampollas = ctk.CTkScrollableFrame(frame_lista, height=150)
        scroll_ampollas.pack(fill="both", expand=True, padx=5, pady=5)

        if not self.ampollas_disponibles:
            ctk.CTkLabel(scroll_ampollas, text="No hay ampollas disponibles en este vacunatorio.").pack(pady=10)
        else:
            for amp in self.ampollas_disponibles:
                var = ctk.BooleanVar()
                texto_amp = (
                    f"Ampolla #{amp['id_ampolla']} | {amp['vacuna_nombre']} "
                    f"| Lote: {amp['numero_lote']} | Dosis: {amp['dosis_disponibles']}"
                )
                chk = ctk.CTkCheckBox(scroll_ampollas, text=texto_amp, variable=var)
                chk.pack(anchor="w", pady=4, padx=5)
                self.checkboxes_ampollas.append((amp['id_ampolla'], var))

        # Observaciones
        lbl_obs = ctk.CTkLabel(self, text="Observaciones:")
        lbl_obs.pack(anchor="w", padx=20, pady=(10, 2))
        self.txt_obs = ctk.CTkEntry(self, placeholder_text="Opcional: Motivo del traslado, transporte, etc.")
        self.txt_obs.pack(fill="x", padx=20)

        # Botón Guardar
        btn_guardar = ctk.CTkButton(
            self, text="Emitir Remito y Transferir", command=self._guardar
        )
        btn_guardar.pack(pady=15, padx=20, fill="x")

    def _obtener_ampollas_origen(self):
        """Consulta en la base las ampollas del vacunatorio actual del usuario logueado."""
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT 
                a.id_ampolla,
                a.dosis_disponibles,
                l.numero_lote,
                v.nombre AS vacuna_nombre
            FROM AMPOLLA a
            INNER JOIN LOTE l ON a.id_lote = l.id_lote
            INNER JOIN VACUNA v ON l.id_vacuna = v.id_vacuna
            WHERE a.id_vacunatorio_actual = ? AND a.dosis_disponibles > 0
            """,
            (self.usuario_logueado["id_vacunatorio"],)
        )
        filas = cursor.fetchall()
        conexion.close()
        return filas

    def _guardar(self):
        remito = self.txt_remito.get().strip()
        destino_nombre = self.combo_destino.get()
        obs = self.txt_obs.get().strip()

        if not remito:
            messagebox.showerror("Error", "Debe ingresar un número de remito.")
            return

        # Buscar ID del vacunatorio destino
        id_destino = None
        for v in self.vacunatorios:
            if v["nombre"] == destino_nombre:
                id_destino = v["id_vacunatorio"]
                break

        if not id_destino:
            messagebox.showerror("Error", "Seleccione un vacunatorio de destino válido.")
            return

        # Obtener IDs de ampollas tildadas
        ampollas_a_enviar = [
            id_amp for id_amp, var in self.checkboxes_ampollas if var.get()
        ]

        if not ampollas_a_enviar:
            messagebox.showerror("Error", "Debe seleccionar al menos una ampolla para transferir.")
            return

        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            registrar_transferencia(
                numero_remito=remito,
                fecha=fecha_actual,
                id_vacunatorio_origen=self.usuario_logueado["id_vacunatorio"],
                id_vacunatorio_destino=id_destino,
                id_usuario=self.usuario_logueado["id_usuario"],
                lista_id_ampollas=ampollas_a_enviar,
                observaciones=obs if obs else None
            )
            messagebox.showinfo("Éxito", "Transferencia realizada correctamente.")
            self.al_guardar_callback()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la transferencia:\n{str(e)}")