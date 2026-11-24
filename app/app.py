"""Aplicación Streamlit — predicción de contratación de depósito a plazo (CRISP-DM).

Ejecutar desde la carpeta del proyecto:  streamlit run app/app.py
"""
import importlib

import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from sklearn.metrics import ConfusionMatrixDisplay

import config
import estilos
import formulario
import utils

# Streamlit solo recarga app.py al editar: se recargan los módulos propios para que
# los cambios en config/estilos/formulario/utils se vean sin reiniciar el servidor.
for _modulo in (config, utils, estilos, formulario):
    importlib.reload(_modulo)

st.set_page_config(page_title=config.NOMBRE_APP, page_icon=":material/account_balance:", layout="wide")
estilos.aplicar()

# ---------------------------------------------------------------- carga base
if not config.ESQUEMA.exists():
    st.error(
        "No se encontraron los artefactos de la aplicación. "
        "Ejecute el notebook completo (Fase 6) para generar `app/models` y `app/data`."
    )
    st.stop()

esquema_base = utils.cargar_json(str(config.ESQUEMA))
iteraciones = {
    nombre: it for nombre, it in config.ITERACIONES.items() if utils.modelos_disponibles(it)
}
if not iteraciones:
    st.error("Ninguna iteración tiene modelos exportados. Ejecute la Fase 6 del notebook.")
    st.stop()

# ------------------------------------------------------------------- sidebar
with st.sidebar:
    estilos.marca_lateral()
    nombres_iteraciones = list(iteraciones)
    st.caption("Selecciona la iteración en Predicción individual o Datos de generalización.")


def contexto_iteracion(nombre):
    iteracion = iteraciones[nombre]
    rutas = utils.modelos_disponibles(iteracion)
    metricas = (
        utils.cargar_json(str(iteracion["metricas"])) if iteracion["metricas"].exists() else None
    )
    esquema = utils.esquema_de_iteracion(esquema_base, metricas)
    return iteracion, rutas, metricas, esquema


def umbral_modelo(nombre, metricas):
    if not metricas:
        return 0.5
    datos_modelo = metricas["modelos"].get(nombre, {})
    return float(datos_modelo.get("umbral_optimo", 0.5))

estilos.encabezado()

tab_pred, tab_gen, tab_met = st.tabs([
    ":material/person_search: Predicción individual",
    ":material/fact_check: Datos de generalización",
    ":material/bar_chart: Desempeño de los modelos",
])

# ------------------------------------------------------ 1. predicción individual
with tab_pred:
    st.subheader("Consulta en tiempo real a los modelos")
    st.write(
        "Complete los datos del cliente que el ejecutivo tendría **antes de llamarlo**. "
        "Los tres modelos estimarán qué tan probable es que contrate un depósito a plazo."
    )

    nombre_iter_pred = st.selectbox(
        "Iteración del modelo", nombres_iteraciones, index=len(nombres_iteraciones) - 1,
        key="iteracion_prediccion",
    )
    _, rutas_modelos_pred, metricas_pred, esquema_pred = contexto_iteracion(nombre_iter_pred)
    mejor_modelo_pred = metricas_pred["mejor_modelo"] if metricas_pred else None
    ganador_final_pred = metricas_pred.get("ganador_final", {}) if metricas_pred else {}
    st.caption(f"Variables usadas: {len(esquema_pred['columnas'])} de {len(esquema_base['columnas'])}")

    formulario.inicializar(esquema_pred)
    valores = formulario.mostrar(esquema_pred)

    if ganador_final_pred:
        st.info(
            f"Modelo recomendado: **{ganador_final_pred['modelo']}** "
            f"(umbral óptimo {ganador_final_pred.get('umbral', 0.5):.2f}).",
            icon=":material/recommend:",
        )
    elegidos = st.multiselect(
        "Modelos a consultar", list(rutas_modelos_pred), default=list(rutas_modelos_pred),
        key=f"modelos_pred_v2_{nombre_iter_pred}",
    )

    if st.button("Predecir", type="primary", icon=":material/query_stats:", disabled=not elegidos):
        cliente = pd.DataFrame([valores])[esquema_pred["columnas"]]
        resultados = []
        columnas_res = st.columns(len(elegidos))
        for columna, nombre in zip(columnas_res, elegidos):
            clase, proba = utils.predecir(
                utils.cargar_modelo(rutas_modelos_pred[nombre]), cliente,
                umbral_modelo(nombre, metricas_pred),
            )
            resultados.append({"Modelo": nombre, "Probabilidad de contratar": float(proba.iloc[0])})
            etiqueta = utils.ETIQUETAS[int(clase.iloc[0])]
            with columna:
                with st.container(border=True):
                    st.markdown(
                        f"**{nombre}**"
                        + (
                            " :green-badge[:material/star: Mejor en validación]"
                            if nombre == mejor_modelo_pred else ""
                        )
                        + (
                            " :orange-badge[:material/trophy: Ganador final]"
                            if nombre == ganador_final_pred.get("modelo") else ""
                        )
                    )
                    st.metric("Predicción", etiqueta)
                    st.metric("Probabilidad de contratar", f"{proba.iloc[0]:.1%}")
                    if umbral_modelo(nombre, metricas_pred) != 0.5:
                        st.caption(
                            f"Umbral de decisión: {umbral_modelo(nombre, metricas_pred):.2f}"
                        )
        if mejor_modelo_pred in elegidos:
            st.caption("**Mejor en validación:** modelo con mayor F1 en validación cruzada.")
        if ganador_final_pred.get("modelo") in elegidos:
            st.caption(
                f"**Ganador final:** {ganador_final_pred['modelo']} "
                f"(umbral {ganador_final_pred['umbral']:.2f})."
            )
        balanceados = bool(metricas_pred) and all(
            d["hiperparametros"].get("class_weight") == "balanced"
            for d in metricas_pred["modelos"].values()
        )
        if balanceados:
            st.caption(
                "Los modelos fueron entrenados dando más peso a los clientes que sí contratan (`class_weight='balanced'`), "
                "por lo que la probabilidad no es una tasa real: sirve para comparar clientes entre sí. "
                "Solo el 11,7 % de los clientes del dataset contrató."
            )
        else:
            st.caption(
                "La probabilidad es una estimación del modelo y sirve sobre todo para comparar clientes entre sí. "
                "Solo el 11,7 % de los clientes del dataset contrató."
            )
        estilos.barras(
            pd.DataFrame(resultados).set_index("Modelo"), y_titulo="Probabilidad de contratar", formato=".1%"
        )

# ------------------------------------------------------ 2. datos de generalización
with tab_gen:
    st.subheader("Evaluación con datos no vistos en el entrenamiento")
    nombre_iter_gen = st.selectbox(
        "Iteración del modelo", nombres_iteraciones, index=len(nombres_iteraciones) - 1,
        key="iteracion_generalizacion",
    )
    iteracion_gen, rutas_modelos_gen, metricas_gen, esquema_gen = contexto_iteracion(nombre_iter_gen)
    mejor_modelo_gen = metricas_gen["mejor_modelo"] if metricas_gen else None
    ganador_final_gen = metricas_gen.get("ganador_final", {}) if metricas_gen else {}
    datos = None
    if iteracion_gen["datos_generalizacion"].exists():
        datos = utils.cargar_csv(str(iteracion_gen["datos_generalizacion"]))
        st.caption(
            f"{len(datos):,} registros del 20 % de prueba: no participaron en el entrenamiento "
            "ni en la validación cruzada."
        )
    else:
        st.warning("No existe el archivo de generalización de esta iteración.")

    if datos is not None:
        try:
            X, avisos = utils.validar_datos(datos, esquema_gen)
            y_real = (
                utils.objetivo_a_binario(datos[esquema_gen["objetivo"]])
                if esquema_gen["objetivo"] in datos else None
            )
        except ValueError as error:
            st.error(str(error))
            st.stop()
        for aviso in avisos:
            st.warning(aviso)

        if ganador_final_gen:
            st.info(
                f"Modelo recomendado: **{ganador_final_gen['modelo']}** "
                f"(umbral óptimo {ganador_final_gen.get('umbral', 0.5):.2f}).",
                icon=":material/recommend:",
            )
        elegidos_gen = st.multiselect(
            "Modelos a evaluar", list(rutas_modelos_gen), default=list(rutas_modelos_gen),
            key=f"modelos_gen_v2_{nombre_iter_gen}",
        )
        if elegidos_gen:
            filas, predicciones = [], {}
            for nombre in elegidos_gen:
                clase, proba = utils.predecir(
                    utils.cargar_modelo(rutas_modelos_gen[nombre]), X,
                    umbral_modelo(nombre, metricas_gen),
                )
                predicciones[nombre] = (clase, proba)
                if y_real is not None:
                    filas.append({"Modelo": nombre, **utils.calcular_metricas(y_real, clase)})

            if y_real is not None:
                tabla = pd.DataFrame(filas).set_index("Modelo")
                st.markdown("**Desempeño sobre estos datos**")
                st.dataframe(
                    tabla.style.format(
                        {c: "{:.4f}" for c in ["Accuracy", "Precision", "Recall", "F1"]}
                    ).highlight_max(subset=["F1"], color="#CDE8D9"),
                    width="stretch",
                )
                estilos.barras(tabla[["Accuracy", "Precision", "Recall", "F1"]])

                detalle = st.selectbox("Matriz de confusión de", elegidos_gen)
                fig, ax = plt.subplots(figsize=(4, 3.5))
                ConfusionMatrixDisplay.from_predictions(
                    y_real, predicciones[detalle][0], display_labels=["No", "Sí"], cmap="Greens",
                    values_format="d", ax=ax, colorbar=False,
                )
                ax.set_title(detalle)
                st.pyplot(fig, width="content")
            else:
                st.info("El archivo no trae la columna `y`: se muestran predicciones, sin métricas.")

            st.markdown("**Predicciones**")
            ver = st.selectbox("Modelo", elegidos_gen, key="modelo_tabla")
            clase, proba = predicciones[ver]
            salida = X.copy()
            if y_real is not None:
                salida["real"] = y_real.map(utils.ETIQUETAS)
            salida["predicción"] = clase.map(utils.ETIQUETAS)
            salida["prob. contratar"] = proba.round(4)
            st.dataframe(salida, width="stretch", height=300)
            st.download_button(
                "Descargar predicciones (CSV)", salida.to_csv(index=False).encode("utf-8"),
                file_name=f"predicciones_{ver.lower().replace(' ', '_')}.csv", mime="text/csv",
            )

# ------------------------------------------------------ 3. métricas por iteración
with tab_met:
    st.subheader("Desempeño de los modelos por iteración")
    st.caption("Métricas de la clase 'contrata' sobre el conjunto de prueba de cada iteración.")

    filas = []
    for nombre_it, it in iteraciones.items():
        if not it["metricas"].exists():
            continue
        met = utils.cargar_json(str(it["metricas"]))
        for modelo, datos_m in met["modelos"].items():
            versiones = {
                "Base": datos_m["base"],
                "Optimizado": datos_m["optimizado"],
            } if "base" in datos_m else {
                "Optimizado": datos_m["optimizado"],
            }
            if "optimizado_umbral" in datos_m:
                versiones["Optimizado (umbral)"] = datos_m["optimizado_umbral"]
            for version, m in versiones.items():
                filas.append({
                    "Iteración": nombre_it, "Modelo": modelo, "Versión": version.capitalize(),
                    "Accuracy": m["accuracy"], "Precision": m["precision"],
                    "Recall": m["recall"], "F1": m["f1"],
                    "VN": m["vn"], "FP": m["fp"], "FN": m["fn"], "VP": m["vp"],
                })

    if not filas:
        st.info("Aún no hay métricas exportadas.")
    else:
        df_met = pd.DataFrame(filas)
        formato = {c: "{:.4f}" for c in ["Accuracy", "Precision", "Recall", "F1"]}
        opciones_iter = ["Todas"] + list(iteraciones)
        iteracion_filtro = st.selectbox(
            "Filtrar por iteración",
            opciones_iter,
            index=0,
            key="filtro_desempeno",
        )
        df_filtrado = (
            df_met if iteracion_filtro == "Todas"
            else df_met[df_met["Iteración"] == iteracion_filtro]
        )

        st.dataframe(df_filtrado.style.format(formato), width="stretch", hide_index=True)

        metrica = st.radio(
            "Métrica a comparar",
            ["F1", "Recall", "Precision", "Accuracy"],
            horizontal=True
        )

        # Seleccionar una sola versión final por modelo.
        # Prioridad: optimizado con umbral > optimizado.
        candidatas = df_filtrado[
            df_filtrado["Versión"].isin(
                ["Optimizado", "Optimizado (umbral)"]
            )
        ].copy()

        candidatas["Prioridad"] = candidatas["Versión"].map({
            "Optimizado": 1,
            "Optimizado (umbral)": 2,
        })

        finales = (
            candidatas.sort_values("Prioridad")
            .drop_duplicates(
                subset=["Iteración", "Modelo"],
                keep="last"
            )
            .drop(columns="Prioridad")
        )

        # GRÁFICO 1: COMPARACIÓN DE MODELOS
        if iteracion_filtro == "Todas":
            st.markdown(
                f"**{metrica} final por modelo e iteración**"
            )
            comparacion = finales
            grupo = "Iteración"
        else:
            st.markdown(
                f"**{metrica}: comparación de versiones "
                f"({iteracion_filtro})**"
            )
            comparacion = df_filtrado
            grupo = "Versión"

        grafico_comparacion = (
            alt.Chart(comparacion)
            .mark_bar(cornerRadiusEnd=3)
            .encode(
                x=alt.X(
                    f"{metrica}:Q",
                    title=metrica,
                    scale=alt.Scale(domain=[0, 1]),
                    axis=alt.Axis(format=".0%"),
                ),
                y=alt.Y(
                    "Modelo:N",
                    title=None,
                    axis=alt.Axis(
                        labelLimit=260,
                        labelFontSize=12
                    ),
                ),
                yOffset=alt.YOffset(f"{grupo}:N"),
                color=alt.Color(
                    f"{grupo}:N",
                    title=grupo,
                    scale=alt.Scale(
                        range=[
                            "#0A4D34",
                            "#2E9E6B",
                            "#9AD1B4"
                        ]
                    ),
                ),
                tooltip=[
                    alt.Tooltip("Iteración:N"),
                    alt.Tooltip("Modelo:N"),
                    alt.Tooltip("Versión:N"),
                    alt.Tooltip(
                        f"{metrica}:Q",
                        format=".4f"
                    ),
                ],
            )
            .properties(
                height=max(
                    260,
                    85 * comparacion["Modelo"].nunique()
                )
            )
        )

        st.altair_chart(
            grafico_comparacion,
            width="stretch",
            theme=None
        )

        # GRÁFICO 2: RANKING SIN DUPLICADOS
        st.markdown(
            f"**Ranking de {metrica} ({iteracion_filtro})**"
        )

        ranking = finales.sort_values(
            metrica,
            ascending=False
        ).copy()

        if iteracion_filtro == "Todas":
            ranking["Categoría"] = (
                ranking["Modelo"]
                + " · "
                + ranking["Iteración"]
            )
        else:
            ranking["Categoría"] = ranking["Modelo"]

        base_ranking = alt.Chart(ranking).encode(
            x=alt.X(
                f"{metrica}:Q",
                title=metrica,
                scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(format=".0%"),
            ),
            y=alt.Y(
                "Categoría:N",
                sort="-x",
                title=None,
                axis=alt.Axis(
                    labelLimit=340,
                    labelFontSize=12
                ),
            ),
            tooltip=[
                alt.Tooltip("Iteración:N"),
                alt.Tooltip("Modelo:N"),
                alt.Tooltip("Versión:N"),
                alt.Tooltip(
                    f"{metrica}:Q",
                    format=".4f"
                ),
            ],
        )

        barras_ranking = base_ranking.mark_bar(
            color="#2E9E6B",
            cornerRadiusEnd=3
        )

        etiquetas_ranking = base_ranking.mark_text(
            align="left",
            baseline="middle",
            dx=6,
            color="#0A4D34",
            fontWeight="bold"
        ).encode(
            text=alt.Text(
                f"{metrica}:Q",
                format=".3f"
            )
        )

        grafico_ranking = (
            barras_ranking + etiquetas_ranking
        ).properties(
            height=max(240, 42 * len(ranking))
        )

        st.altair_chart(
            grafico_ranking,
            width="stretch",
            theme=None
        )


        if iteracion_filtro != "Todas":
            it_filtrada = iteraciones[iteracion_filtro]
            metricas_filtradas = (
                utils.cargar_json(str(it_filtrada["metricas"]))
                if it_filtrada["metricas"].exists() else None
            )
        else:
            metricas_filtradas = None

        if metricas_filtradas:
            st.markdown(f"**Hiperparámetros óptimos ({iteracion_filtro})**")
            hp = pd.DataFrame({
                modelo: {**d["hiperparametros"], "F1 en validación cruzada": round(d["f1_cv"], 4)}
                for modelo, d in metricas_filtradas["modelos"].items()
            }).T.fillna("—").astype(str)
            st.dataframe(hp, width="stretch")
            modelo_seleccionado = (
                metricas_filtradas.get("ganador_final", {}).get("modelo")
                or metricas_filtradas["mejor_modelo"]
            )
            st.success(
                f"Modelo seleccionado en {iteracion_filtro}: "
                f"**{modelo_seleccionado}**",
                icon=":material/star:",
            )
