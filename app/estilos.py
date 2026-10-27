"""Identidad visual de la aplicación: paleta verde y blanco, siempre en modo claro."""
import altair as alt
import pandas as pd
import streamlit as st

import config

VERDE = "#0F6B47"
VERDE_OSCURO = "#0A4D34"
VERDE_MEDIO = "#2E9E6B"
VERDE_CLARO = "#9AD1B4"
GRIS_VERDOSO = "#6B8577"

VERDE_PALIDO = "#E3F1E9"

# Rellenos de las series, de más a menos intenso. Con 2 series se usan extremos contrastados.
_RELLENOS = {
    2: [VERDE_OSCURO, VERDE_CLARO],
    3: [VERDE_OSCURO, VERDE_MEDIO, VERDE_CLARO],
    4: [VERDE_OSCURO, VERDE_MEDIO, VERDE_CLARO, VERDE_PALIDO],
}


def barras(datos: pd.DataFrame, y_titulo: str = "", formato: str = ".3f", altura: int = 320):
    """Barras agrupadas con borde oscuro y valor sobre cada barra.

    `datos`: una fila por categoría (el índice, con nombre) y una columna por serie.
    El borde y las etiquetas permiten distinguir las series sin depender solo del color.
    """
    eje_x = datos.index.name or "categoria"
    series = list(datos.columns)
    largo = datos.reset_index().melt(id_vars=eje_x, var_name="Serie", value_name="Valor")
    tope = max(float(largo["Valor"].max()) * 1.2, 0.05)

    codificacion = dict(
        x=alt.X(f"{eje_x}:N", title=None, sort=list(datos.index), axis=alt.Axis(labelAngle=0, labelLimit=150)),
        y=alt.Y("Valor:Q", title=y_titulo, scale=alt.Scale(domain=[0, tope]), axis=alt.Axis(format=".1f")),
    )
    if len(series) > 1:
        rellenos = _RELLENOS.get(len(series), _RELLENOS[4] * 2)[: len(series)]
        codificacion["xOffset"] = alt.XOffset("Serie:N", sort=series)
        codificacion["color"] = alt.Color(
            "Serie:N", sort=series, scale=alt.Scale(domain=series, range=rellenos),
            legend=alt.Legend(title=None, orient="bottom", symbolStrokeColor=VERDE_OSCURO, symbolStrokeWidth=1.5),
        )
    else:
        codificacion["color"] = alt.value(VERDE_MEDIO)

    base = alt.Chart(largo).encode(**codificacion)
    columnas = base.mark_bar(stroke=VERDE_OSCURO, strokeWidth=1.5, cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
    etiquetas = base.mark_text(dy=-7, fontSize=11, fontWeight="bold", color=VERDE_OSCURO).encode(
        text=alt.Text("Valor:Q", format=formato), color=alt.value(VERDE_OSCURO)
    )
    grafico = (
        (columnas + etiquetas)
        .properties(height=altura)
        .configure_view(stroke=None)
        .configure_axis(labelColor="#3F5B4C", titleColor="#3F5B4C", gridColor="#E3EDE7", domainColor="#B7CFC2")
        .configure_legend(labelColor="#16301F", labelFontSize=12)
    )
    st.altair_chart(grafico, width="stretch", theme=None)


_CSS = f"""
<style>
:root {{ color-scheme: light; }}
.stApp {{ background: #FFFFFF; color: #16301F; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2rem; max-width: 1200px; }}

/* Barra lateral */
[data-testid="stSidebar"] {{ background: #F1F7F3; border-right: 1px solid #D3E4DA; }}
.marca {{ display: flex; align-items: center; gap: .6rem; padding: .2rem 0 .8rem 0;
         border-bottom: 2px solid {VERDE}; margin-bottom: 1rem; }}
.marca .logo {{ background: {VERDE}; color: #fff; border-radius: 8px; width: 2.4rem; height: 2.4rem;
               display: flex; align-items: center; justify-content: center; }}
.marca .nombre {{ font-weight: 700; color: {VERDE_OSCURO}; line-height: 1.15; font-size: 1.05rem; }}
.marca .sub {{ font-size: .75rem; color: {GRIS_VERDOSO}; font-weight: 400; }}

/* Encabezado principal */
.banner {{ background: linear-gradient(120deg, {VERDE_OSCURO} 0%, {VERDE} 70%, {VERDE_MEDIO} 100%);
          color: #fff; padding: 1.5rem 2rem; border-radius: 12px; margin-bottom: 1.2rem; }}
.banner .titulo {{ font-size: 1.7rem; font-weight: 700; letter-spacing: .2px; margin: 0; }}
.banner .subtitulo {{ font-size: .95rem; opacity: .9; margin-top: .25rem; }}

/* Iconos Material dentro del HTML propio */
.ico {{ font-family: "Material Symbols Rounded"; font-weight: normal; font-style: normal;
       font-size: 1.4rem; line-height: 1; letter-spacing: normal; text-transform: none;
       display: inline-block; white-space: nowrap; font-feature-settings: "liga"; }}

/* Textos y tarjetas */
h1, h2, h3, h4, h5 {{ color: {VERDE_OSCURO}; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-color: #D3E4DA; border-radius: 10px; }}
[data-testid="stMetricValue"] {{ color: {VERDE_OSCURO}; }}
[data-testid="stMetricLabel"] {{ color: {GRIS_VERDOSO}; }}

/* Botones */
.stButton > button[kind="primary"], .stDownloadButton > button {{
    background: {VERDE}; border: 1px solid {VERDE}; color: #fff; font-weight: 600; }}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {{
    background: {VERDE_OSCURO}; border-color: {VERDE_OSCURO}; color: #fff; }}
.stButton > button[kind="secondary"] {{ border: 1px solid {VERDE}; color: {VERDE}; background: #fff; }}
.stButton > button[kind="secondary"]:hover {{ background: #EEF5F1; border-color: {VERDE_OSCURO}; color: {VERDE_OSCURO}; }}

/* Pestañas */
[data-baseweb="tab-list"] {{ gap: .4rem; border-bottom: 1px solid #D3E4DA; }}
[data-baseweb="tab"] {{ font-weight: 600; }}
</style>
"""


def aplicar():
    st.markdown(_CSS, unsafe_allow_html=True)


def encabezado():
    st.markdown(
        f"""<div class="banner">
        <div class="titulo">{config.NOMBRE_APP}</div>
        <div class="subtitulo">{config.SUBTITULO_APP}</div></div>""",
        unsafe_allow_html=True,
    )


def marca_lateral():
    st.markdown(
        f"""<div class="marca"><div class="logo"><span class="ico">account_balance</span></div>
        <div><div class="nombre">{config.NOMBRE_APP}</div>
        <div class="sub">Gestión comercial · Depósitos</div></div></div>""",
        unsafe_allow_html=True,
    )
