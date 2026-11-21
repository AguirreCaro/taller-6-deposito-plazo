"""Aplicación Streamlit — predicción de contratación de depósito a plazo (CRISP-DM).

Ejecutar desde la carpeta del proyecto:  streamlit run app/app.py
"""
import importlib

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
    nombre_iter = st.selectbox(
        "Versión del modelo (iteración)", list(iteraciones),
        help="Cada iteración es una nueva versión del trabajo: se construye un modelo, se evalúa, "
             "se detectan mejoras y se repite el proceso. La app permite consultar y comparar cada versión.",
    )
    iteracion = iteraciones[nombre_iter]
    rutas_modelos = utils.modelos_disponibles(iteracion)

metricas_iter = (
    utils.cargar_json(str(iteracion["metricas"])) if iteracion["metricas"].exists() else None
)
mejor_modelo = metricas_iter["mejor_modelo"] if metricas_iter else None

# Cada iteración puede usar un subconjunto de las variables: el formulario y la validación
# de datos se ajustan a las que figuran en su JSON de métricas.
esquema = utils.esquema_de_iteracion(esquema_base, metricas_iter)

with st.sidebar:
    st.divider()
    st.caption(f":material/rule: Variables usadas: {len(esquema['columnas'])} de {len(esquema_base['columnas'])}")

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

    formulario.inicializar(esquema)
    valores = formulario.mostrar(esquema)

    elegidos = st.multiselect(
        "Modelos a consultar", list(rutas_modelos), default=list(rutas_modelos), key="modelos_pred"
    )

    if st.button("Predecir", type="primary", icon=":material/query_stats:", disabled=not elegidos):
        cliente = pd.DataFrame([valores])[esquema["columnas"]]
        resultados = []
        columnas_res = st.columns(len(elegidos))
        for columna, nombre in zip(columnas_res, elegidos):
            clase, proba = utils.predecir(utils.cargar_modelo(rutas_modelos[nombre]), cliente)
            resultados.append({"Modelo": nombre, "Probabilidad de contratar": float(proba.iloc[0])})
            etiqueta = utils.ETIQUETAS[int(clase.iloc[0])]
            with columna:
                with st.container(border=True):
                    st.markdown(
                        f"**{nombre}**" + (" :green-badge[:material/star: Seleccionado]" if nombre == mejor_modelo else "")
                    )
                    st.metric("Predicción", etiqueta)
                    st.metric("Probabilidad de contratar", f"{proba.iloc[0]:.1%}")
        if mejor_modelo in elegidos:
            st.caption("**Seleccionado:** modelo con mejor F1 en validación cruzada en esta iteración.")
        balanceados = bool(metricas_iter) and all(
            d["hiperparametros"].get("class_weight") == "balanced" for d in metricas_iter["modelos"].values()
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
    datos = None
    if iteracion["datos_generalizacion"].exists():
        datos = utils.cargar_csv(str(iteracion["datos_generalizacion"]))
        st.caption(
            f"{len(datos):,} registros del 20 % de prueba: no participaron en el entrenamiento "
            "ni en la validación cruzada."
        )
    else:
        st.warning("No existe el archivo de generalización de esta iteración.")

    if datos is not None:
        try:
            X, avisos = utils.validar_datos(datos, esquema)
            y_real = utils.objetivo_a_binario(datos[esquema["objetivo"]]) if esquema["objetivo"] in datos else None
        except ValueError as error:
            st.error(str(error))
            st.stop()
        for aviso in avisos:
            st.warning(aviso)

        elegidos_gen = st.multiselect(
            "Modelos a evaluar", list(rutas_modelos), default=list(rutas_modelos), key="modelos_gen"
        )
        if elegidos_gen:
            filas, predicciones = [], {}
            for nombre in elegidos_gen:
                clase, proba = utils.predecir(utils.cargar_modelo(rutas_modelos[nombre]), X)
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
            for version in ("base", "optimizado"):
                m = datos_m[version]
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
        st.dataframe(df_met.style.format(formato), width="stretch", hide_index=True)

        metrica = st.radio("Métrica a comparar", ["F1", "Recall", "Precision", "Accuracy"], horizontal=True)
        izq, der = st.columns(2)
        with izq:
            st.markdown(f"**{metrica}: modelo base vs optimizado** ({nombre_iter})")
            sel = df_met[df_met["Iteración"] == nombre_iter]
            estilos.barras(sel.pivot(index="Modelo", columns="Versión", values=metrica), y_titulo=metrica)
        with der:
            st.markdown(f"**{metrica} de los modelos optimizados por iteración**")
            opt = df_met[df_met["Versión"] == "Optimizado"]
            estilos.barras(opt.pivot(index="Modelo", columns="Iteración", values=metrica), y_titulo=metrica)

        if metricas_iter:
            st.markdown(f"**Hiperparámetros óptimos ({nombre_iter})**")
            hp = pd.DataFrame({
                modelo: {**d["hiperparametros"], "F1 en validación cruzada": round(d["f1_cv"], 4)}
                for modelo, d in metricas_iter["modelos"].items()
            }).T.fillna("—").astype(str)
            st.dataframe(hp, width="stretch")
            st.success(f"Modelo seleccionado en {nombre_iter}: **{mejor_modelo}**", icon=":material/star:")
