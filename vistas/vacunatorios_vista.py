"""
Pantalla de Vacunatorios: listado, alta y edición.

premite completar la dirección real de los vacunatorios que se crean automáticamente  desde la pantalla de Importar CSV.
"""

import customtkinter as ctk

from modelos.vacunatorio import (
    crear_vacunatorio,
    actualizar_vacunatorio,
    marcar_como_central,
    eliminar_vacunatorio,
    listar_vacunatorios,
)


class FrameVacunatorios(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.id_en_edicion = None  # None = modo alta; distinto de None = editando ese id
        self._construir_widgets()
        self._refrescar_listado()

    def _construir_widgets(self):
        ctk.CTkLabel(
            self, text="Vacunatorios",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(10, 15), anchor="w", padx=10)

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=10)
        contenedor.grid_columnconfigure(0, weight=3)
        contenedor.grid_columnconfigure(1, weight=2)
        contenedor.grid_rowconfigure(0, weight=1)

        # --- Columna izquierda: listado ---
        self.marco_listado = ctk.CTkScrollableFrame(contenedor, label_text="Listado")
        self.marco_listado.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # --- Columna derecha: formulario ---
        marco_form = ctk.CTkFrame(contenedor)
        marco_form.grid(row=0, column=1, sticky="nsew")

        self.titulo_form = ctk.CTkLabel(
            marco_form, text="Nuevo vacunatorio",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.titulo_form.pack(pady=(15, 10), padx=15, anchor="w")

        ctk.CTkLabel(marco_form, text="Nombre").pack(anchor="w", padx=15)
        self.campo_nombre = ctk.CTkEntry(marco_form)
        self.campo_nombre.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(marco_form, text="Dirección").pack(anchor="w", padx=15)
        self.campo_direccion = ctk.CTkEntry(marco_form)
        self.campo_direccion.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(marco_form, text="Teléfono (opcional)").pack(anchor="w", padx=15)
        self.campo_telefono = ctk.CTkEntry(marco_form)
        self.campo_telefono.pack(fill="x", padx=15, pady=(0, 10))

        self.casilla_central = ctk.CTkCheckBox(marco_form, text="Es el vacunatorio central")
        self.casilla_central.pack(anchor="w", padx=15, pady=(0, 5))
        # Nota: solo aplica al crear uno nuevo; no se puede editar en un
        # vacunatorio ya existente desde esta pantalla.

        self.etiqueta_error = ctk.CTkLabel(marco_form, text="", text_color="red")
        self.etiqueta_error.pack(anchor="w", padx=15)

        fila_botones = ctk.CTkFrame(marco_form, fg_color="transparent")
        fila_botones.pack(fill="x", padx=15, pady=15)

        self.boton_guardar = ctk.CTkButton(
            fila_botones, text="Crear vacunatorio", command=self._guardar
        )
        self.boton_guardar.pack(side="left")

        self.boton_cancelar = ctk.CTkButton(
            fila_botones, text="Cancelar", fg_color="gray40", hover_color="gray30",
            command=self._modo_alta
        )
        self.boton_cancelar.pack(side="left", padx=10)
        self.boton_cancelar.pack_forget()  # oculto hasta que se entre en modo edición

    def _refrescar_listado(self):
        for widget in self.marco_listado.winfo_children():
            widget.destroy()

        vacunatorios = listar_vacunatorios()
        self.existe_central = any(v["es_central"] for v in vacunatorios)

        if not vacunatorios:
            ctk.CTkLabel(self.marco_listado, text="No hay vacunatorios cargados todavía.").pack(pady=20)
        else:
            for v in vacunatorios:
                fila = ctk.CTkFrame(self.marco_listado)
                fila.pack(fill="x", pady=4, padx=2)

                etiqueta_central = "  ⭐ Central" if v["es_central"] else ""
                texto = f"{v['nombre']}{etiqueta_central}\n{v['direccion']}"
                if v["telefono"]:
                    texto += f"  ·  {v['telefono']}"

                ctk.CTkLabel(fila, text=texto, justify="left", anchor="w").pack(
                    side="left", padx=10, pady=8, fill="x", expand=True
                )

                # Una vez que existe un central, no se ofrece la opción de
                # cambiarlo desde acá para evitar reasignarlo por error.
                if not v["es_central"] and not self.existe_central:
                    ctk.CTkButton(
                        fila, text="Marcar como central", width=140,
                        fg_color="gray40", hover_color="gray30",
                        command=lambda v=v: self._marcar_central(v),
                    ).pack(side="right", padx=(0, 10))

                ctk.CTkButton(
                    fila, text="Eliminar", width=70,
                    fg_color="#b3261e", hover_color="#8c1d17",
                    command=lambda v=v: self._confirmar_eliminar(v),
                ).pack(side="right", padx=(0, 10))

                ctk.CTkButton(
                    fila, text="Editar", width=70,
                    command=lambda v=v: self._cargar_para_editar(v),
                ).pack(side="right", padx=10)

        # Si ya hay un central, no se puede tildar en el formulario de alta.
        if self.id_en_edicion is None:
            if self.existe_central:
                self.casilla_central.deselect()
                self.casilla_central.configure(state="disabled")
            else:
                self.casilla_central.configure(state="normal")

    def _confirmar_eliminar(self, vacunatorio):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Confirmar eliminación")
        ventana.geometry("380x160")
        ventana.resizable(False, False)
        ventana.grab_set()  # modal: bloquea la ventana principal hasta que se cierre

        ctk.CTkLabel(
            ventana,
            text=f"¿Eliminar el vacunatorio\n\"{vacunatorio['nombre']}\"?",
            font=ctk.CTkFont(size=14, weight="bold"),
            justify="center",
        ).pack(pady=(20, 5), padx=20)

        etiqueta_resultado = ctk.CTkLabel(ventana, text="", text_color="red")
        etiqueta_resultado.pack(pady=(0, 5))

        fila_botones = ctk.CTkFrame(ventana, fg_color="transparent")
        fila_botones.pack(pady=10)

        def confirmar():
            try:
                eliminar_vacunatorio(vacunatorio["id_vacunatorio"])
            except ValueError as error:
                etiqueta_resultado.configure(text=str(error))
                return
            ventana.destroy()
            if self.id_en_edicion == vacunatorio["id_vacunatorio"]:
                self._modo_alta()
            self._refrescar_listado()

        ctk.CTkButton(
            fila_botones, text="Sí, eliminar", fg_color="#b3261e", hover_color="#8c1d17",
            command=confirmar,
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            fila_botones, text="Cancelar", fg_color="gray40", hover_color="gray30",
            command=ventana.destroy,
        ).pack(side="left", padx=5)

    def _marcar_central(self, vacunatorio):
        marcar_como_central(vacunatorio["id_vacunatorio"])
        self.etiqueta_error.configure(
            text_color=("black", "white"),
            text=f"\"{vacunatorio['nombre']}\" es ahora el vacunatorio central.",
        )
        self._refrescar_listado()

    def _cargar_para_editar(self, vacunatorio):
        self.id_en_edicion = vacunatorio["id_vacunatorio"]
        self.titulo_form.configure(text=f"Editando: {vacunatorio['nombre']}")

        self.campo_nombre.delete(0, "end")
        self.campo_nombre.insert(0, vacunatorio["nombre"])

        self.campo_direccion.delete(0, "end")
        self.campo_direccion.insert(0, vacunatorio["direccion"])

        self.campo_telefono.delete(0, "end")
        if vacunatorio["telefono"]:
            self.campo_telefono.insert(0, vacunatorio["telefono"])

        # es_central no se edita desde acá: se deshabilita la casilla
        # y se refleja su valor actual solo a modo informativo.
        if vacunatorio["es_central"]:
            self.casilla_central.select()
        else:
            self.casilla_central.deselect()
        self.casilla_central.configure(state="disabled")

        self.boton_guardar.configure(text="Guardar cambios")
        self.boton_cancelar.pack(side="left", padx=10)
        self.etiqueta_error.configure(text="")

    def _modo_alta(self):
        self.id_en_edicion = None
        self.titulo_form.configure(text="Nuevo vacunatorio")
        self.campo_nombre.delete(0, "end")
        self.campo_direccion.delete(0, "end")
        self.campo_telefono.delete(0, "end")
        self.casilla_central.deselect()
        self.casilla_central.configure(state="disabled" if self.existe_central else "normal")
        self.boton_guardar.configure(text="Crear vacunatorio")
        self.boton_cancelar.pack_forget()
        self.etiqueta_error.configure(text="")

    def _guardar(self):
        nombre = self.campo_nombre.get().strip()
        direccion = self.campo_direccion.get().strip()
        telefono = self.campo_telefono.get().strip() or None

        if not nombre or not direccion:
            self.etiqueta_error.configure(text_color="red", text="Nombre y dirección son obligatorios.")
            return

        try:
            if self.id_en_edicion is None:
                crear_vacunatorio(
                    nombre=nombre,
                    direccion=direccion,
                    telefono=telefono,
                    es_central=(self.casilla_central.get() == 1),
                )
            else:
                actualizar_vacunatorio(
                    self.id_en_edicion, nombre=nombre, direccion=direccion, telefono=telefono
                )
        except Exception as error:
            # Típicamente salta acá si el nombre ya existe (UNIQUE)
            self.etiqueta_error.configure(text_color="red", text=f"No se pudo guardar: {error}")
            return

        self._modo_alta()
        self._refrescar_listado()