"""

Uso en cualquier vista:
    from estilos import Color, Fuente, RADIO

    ctk.CTkButton(self, fg_color=Color.PRIMARIO, font=Fuente.texto())
"""

import customtkinter as ctk


def aplicar_tema_global():
    """Llamar una sola vez, al arrancar la app (en main.py)."""
    ctk.set_appearance_mode("system")   # "light", "dark" o "system"
    ctk.set_default_color_theme("green")


class Color:
    
    PRIMARIO = ("#2FA572", "#2FA572")            # color de marca: botón "Ingresar", ítem de menú seleccionado
    PRIMARIO_HOVER = ("#106A43", "#1F6E44")       # color al pasar el mouse sobre esos mismos botones
 
    FONDO_APP = ("#EEF2F6", "#0F172A")            # fondo general de las ventanas (detrás de todo)
    TARJETA = ("#FFFFFF", "#1E293B")              # fondo de "tarjetas": el cuadro de login, la barra superior, el área de contenido
    BORDE = ("#E2E8F0", "#334155")                # líneas y bordes sutiles (separadores, contorno de tarjetas y campos de texto)
 
    SIDEBAR = ("#0F172A", "#0B1120")              # fondo del menú lateral izquierdo
    SIDEBAR_TEXTO = ("#E2E8F0", "#E2E8F0")        # texto de los botones del menú lateral (cuando NO están seleccionados)
    SIDEBAR_HOVER = ("#1E293B", "#1E293B")        # color de fondo al pasar el mouse sobre un botón del menú lateral
    SIDEBAR_TEXTO_SECUNDARIO = ("#94A3B8", "#64748B")  # texto chico del menú lateral, ej: el título "MENÚ"
 
    TEXTO = ("#0F172A", "#F1F5F9")                # texto principal (títulos, nombre de usuario)
    TEXTO_SECUNDARIO = ("#64748B", "#94A3B8")     # texto secundario/apagado (subtítulos, placeholders, módulos "pendiente")
    ERROR = ("#DC2626", "#F87171")                # mensajes de error, ej: "Usuario o contraseña incorrectos"
    EXITO = ("#16A34A", "#4ADE80")                # reservado para mensajes de éxito (todavía no se usa en ninguna vista)

    

class Fuente:
    """Funciones (no constantes) porque CTkFont necesita que ya
    exista una ventana ctk creada antes de instanciarse."""

    @staticmethod
    def titulo():
        return ctk.CTkFont(family="Segoe UI", size=20, weight="bold")

    @staticmethod
    def subtitulo():
        return ctk.CTkFont(family="Segoe UI", size=15, weight="bold")

    @staticmethod
    def texto():
        return ctk.CTkFont(family="Segoe UI", size=13)

    @staticmethod
    def texto_negrita():
        return ctk.CTkFont(family="Segoe UI", size=13, weight="bold")

    @staticmethod
    def chico():
        return ctk.CTkFont(family="Segoe UI", size=11)


RADIO = 10          # corner_radius estándar para tarjetas y botones grandes
RADIO_CHICO = 8      # corner_radius para botones de menú