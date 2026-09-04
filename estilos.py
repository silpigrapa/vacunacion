"""
Estilos centralizados del Sistema de Vacunación.

Tener los colores, fuentes y tamaños en un solo lugar permite que
todas las pantallas (login, panel principal, vacunas, stock, etc.)
compartan el mismo estilo visual y sea fácil ajustarlo a futuro.

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
    """
    Cada color es una tupla (modo_claro, modo_oscuro), como lo pide
    CustomTkinter. Paleta pensada para un sistema de salud: teal como
    color de marca, fondos neutros y buen contraste de texto.
    """
    PRIMARIO = ("#2FA572", "#2FA572")            # verde - color de marca
    PRIMARIO_HOVER = ("#106A43", "#1F6E44")

    FONDO_APP = ("#EEF2F6", "#0F172A")
    TARJETA = ("#FFFFFF", "#1E293B")
    BORDE = ("#E2E8F0", "#334155")

    SIDEBAR = ("#0F172A", "#0B1120")
    SIDEBAR_TEXTO = ("#E2E8F0", "#E2E8F0")
    SIDEBAR_HOVER = ("#1E293B", "#1E293B")
    SIDEBAR_TEXTO_SECUNDARIO = ("#94A3B8", "#64748B")

    TEXTO = ("#0F172A", "#F1F5F9")
    TEXTO_SECUNDARIO = ("#64748B", "#94A3B8")
    ERROR = ("#DC2626", "#F87171")
    EXITO = ("#16A34A", "#4ADE80")


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