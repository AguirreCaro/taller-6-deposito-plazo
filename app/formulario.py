"""Formulario de ingreso de datos de un cliente, en lenguaje de negocio.

Los modelos reciben siempre los valores originales del dataset (en inglés); aquí solo se
traducen las etiquetas que ve la persona usuaria.
"""
import streamlit as st

import utils

VALORES = {
    "job": {
        "admin.": "Administrativo", "blue-collar": "Obrero / trabajo manual",
        "entrepreneur": "Emprendedor", "housemaid": "Servicio doméstico",
        "management": "Gerencia / directivo", "retired": "Jubilado",
        "self-employed": "Independiente", "services": "Servicios",
        "student": "Estudiante", "technician": "Técnico",
        "unemployed": "Desempleado", "unknown": "No informado",
    },
    "marital": {"married": "Casado/a", "single": "Soltero/a", "divorced": "Divorciado/a o viudo/a"},
    "education": {
        "primary": "Básica (primaria)", "secondary": "Media (secundaria)",
        "tertiary": "Superior (universitaria)", "unknown": "No informado",
    },
    "contact": {"cellular": "Celular", "telephone": "Teléfono fijo", "unknown": "No informado"},
    "month": {
        "jan": "Enero", "feb": "Febrero", "mar": "Marzo", "apr": "Abril", "may": "Mayo",
        "jun": "Junio", "jul": "Julio", "aug": "Agosto", "sep": "Septiembre",
        "oct": "Octubre", "nov": "Noviembre", "dec": "Diciembre",
    },
    "poutcome": {
        "success": "Éxito (contrató el producto)", "failure": "Fracaso (no contrató)",
        "other": "Otro resultado", "unknown": "Sin información",
    },
    "default": {"no": "No", "yes": "Sí"},
    "housing": {"no": "No", "yes": "Sí"},
    "loan": {"no": "No", "yes": "Sí"},
}

ORDEN_MESES = list(VALORES["month"])


def _etiqueta(col):
    return lambda valor: VALORES.get(col, {}).get(valor, valor)


def _cat(esquema, col, titulo, ayuda):
    info = esquema["categoricas"][col]
    opciones = ORDEN_MESES if col == "month" else info["categorias"]
    return st.selectbox(titulo, opciones, key=f"in_{col}", format_func=_etiqueta(col), help=ayuda)


def _num(esquema, col, titulo, ayuda, **extra):
    info = esquema["numericas"][col]
    minimo = extra.pop("minimo", info["min"])
    if st.session_state.get(f"in_{col}", minimo) < minimo:
        st.session_state[f"in_{col}"] = minimo
    return st.number_input(
        titulo, min_value=minimo, max_value=info["max"],
        step=1, key=f"in_{col}", help=f"{ayuda}\n\nRango observado: {info['min']} a {info['max']}.", **extra,
    )


def inicializar(esquema):
    """Valores por defecto (mediana / categoría más frecuente), sin pisar lo ya escrito."""
    for col, info in esquema["numericas"].items():
        st.session_state.setdefault(f"in_{col}", info["mediana"])
    for col, info in esquema["categoricas"].items():
        st.session_state.setdefault(f"in_{col}", info["moda"])
    st.session_state.setdefault("in_contactado_antes", False)
    st.session_state.setdefault("in_pdays_dias", 90)


def mostrar(esquema):
    """Dibuja el formulario y devuelve {columna: valor} con los valores originales del modelo."""
    v = {}

    with st.container(border=True):
        st.markdown("##### :material/person: Perfil del cliente")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            v["age"] = _num(esquema, "age", "Edad (años)", "Edad actual del cliente.")
        with c2:
            v["job"] = _cat(esquema, "job", "Ocupación", "Tipo de trabajo del cliente.")
        with c3:
            v["marital"] = _cat(esquema, "marital", "Estado civil", "Divorciado/a incluye viudos/as.")
        with c4:
            v["education"] = _cat(esquema, "education", "Nivel educativo", "Máximo nivel educativo alcanzado.")

    with st.container(border=True):
        st.markdown("##### :material/account_balance_wallet: Situación financiera")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            v["balance"] = _num(
                esquema, "balance", "Saldo promedio anual (€)",
                "Saldo medio de la cuenta del cliente durante el año, en euros. Puede ser negativo.",
            )
        with c2:
            v["default"] = _cat(
                esquema, "default", "¿Tiene deudas en mora?",
                "'Sí' si el cliente tiene un crédito en incumplimiento (impago).",
            )
        with c3:
            v["housing"] = _cat(esquema, "housing", "¿Tiene crédito hipotecario?", "Préstamo para vivienda vigente.")
        with c4:
            v["loan"] = _cat(esquema, "loan", "¿Tiene préstamo personal?", "Préstamo de consumo vigente.")

    # Las iteraciones que usan solo variables conocidas antes de llamar no tienen `day` ni `campaign`:
    # el formulario muestra solo los campos que existen en el esquema de la iteración elegida.
    antes_de_llamar = "day" not in esquema["columnas"] and "campaign" not in esquema["columnas"]
    campos = {
        "contact": lambda: _cat(
            esquema, "contact", "Medio de contacto",
            "Canal con que se planea llamar al cliente." if antes_de_llamar else "Canal usado para llamar al cliente.",
        ),
        "day": lambda: _num(
            esquema, "day", "Día del mes del último contacto",
            "Día del mes (1 a 31) en que se contactó por última vez al cliente en esta campaña.",
        ),
        "month": lambda: _cat(
            esquema, "month", "Mes en que se llamaría" if antes_de_llamar else "Mes del último contacto",
            "Mes del año en que se planea llamar al cliente." if antes_de_llamar
            else "Mes del año en que se contactó por última vez al cliente en esta campaña.",
        ),
        "campaign": lambda: _num(
            esquema, "campaign", "Contactos en esta campaña",
            "Cantidad de veces que se ha contactado a este cliente en la campaña actual, incluyendo el contacto más reciente.",
            minimo=1,
        ),
    }
    presentes = [c for c in campos if c in esquema["columnas"]]
    if presentes:
        with st.container(border=True):
            st.markdown(
                "##### :material/call: " + ("Plan de la campaña" if antes_de_llamar else "Contacto en la campaña actual")
            )
            for columna_st, nombre in zip(st.columns(len(presentes)), presentes):
                with columna_st:
                    v[nombre] = campos[nombre]()

    with st.container(border=True):
        st.markdown("##### :material/history: Historial de campañas anteriores")
        antes = st.checkbox(
            "El cliente fue contactado en una campaña anterior", key="in_contactado_antes",
            help="Si no se marca, se asume que es la primera vez que el banco lo contacta por un producto de este tipo.",
        )
        if antes:
            c1, c2, c3 = st.columns(3)
            with c1:
                v["pdays"] = st.number_input(
                    "Días desde ese último contacto", min_value=0, max_value=esquema["numericas"]["pdays"]["max"],
                    step=1, key="in_pdays_dias",
                    help="Días transcurridos desde que se contactó al cliente en la campaña anterior.",
                )
            with c2:
                v["previous"] = _num(
                    esquema, "previous", "Contactos previos a esta campaña",
                    "Cantidad de veces que se contactó al cliente antes de la campaña actual.", minimo=1,
                )
            with c3:
                v["poutcome"] = _cat(
                    esquema, "poutcome", "Resultado de la campaña anterior",
                    "Qué ocurrió con el cliente en la campaña anterior.",
                )
        else:
            # Así codifica el dataset a un cliente nunca contactado antes
            v["pdays"], v["previous"], v["poutcome"] = -1, 0, "unknown"
            st.caption("Cliente sin historial previo: no se usan datos de campañas anteriores.")

    return {col: v[col] for col in esquema["columnas"]}
