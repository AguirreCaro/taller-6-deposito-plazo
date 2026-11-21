"""Carga de modelos y utilidades de predicción.

No se reimplementa ningún preprocesamiento: cada modelo guardado es un Pipeline
(ColumnTransformer + algoritmo) que recibe el DataFrame con las columnas originales.
"""
import json
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

ETIQUETAS = {0: "No contratará", 1: "Contratará"}


# Las cargas se cachean por (ruta, fecha de modificación): si el notebook vuelve a
# exportar los artefactos, la app los recarga sin necesidad de reiniciarse.
def _mtime(ruta: str) -> float:
    return Path(ruta).stat().st_mtime


@st.cache_resource(show_spinner=False)
def _modelo(ruta: str, mtime: float):
    return joblib.load(ruta)


@st.cache_data(show_spinner=False)
def _json(ruta: str, mtime: float) -> dict:
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def _csv(ruta: str, mtime: float) -> pd.DataFrame:
    return pd.read_csv(ruta)


def cargar_modelo(ruta: str):
    return _modelo(ruta, _mtime(ruta))


def cargar_json(ruta: str) -> dict:
    return _json(ruta, _mtime(ruta))


def cargar_csv(ruta: str) -> pd.DataFrame:
    return _csv(ruta, _mtime(ruta))


def modelos_disponibles(iteracion: dict) -> dict:
    """Solo los modelos cuyo archivo existe, para no romper la app si falta alguno."""
    return {n: str(r) for n, r in iteracion["modelos"].items() if r.exists()}


def esquema_de_iteracion(esquema: dict, metricas: dict | None) -> dict:
    """Esquema acotado a las variables que usa la iteración.

    La lista sale del JSON de métricas (clave "variables"); si no existe, se usan todas.
    """
    usadas = set((metricas or {}).get("variables") or esquema["columnas"])
    return {
        **esquema,
        "columnas": [c for c in esquema["columnas"] if c in usadas],
        "numericas": {c: v for c, v in esquema["numericas"].items() if c in usadas},
        "categoricas": {c: v for c, v in esquema["categoricas"].items() if c in usadas},
        "columnas_dataset": esquema["columnas"],
    }


def validar_datos(df: pd.DataFrame, esquema: dict) -> tuple[pd.DataFrame, list[str]]:
    """Deja el DataFrame con las columnas del esquema, en su orden.

    Devuelve (datos, advertencias). Lanza ValueError si faltan columnas o hay nulos.
    """
    faltantes = [c for c in esquema["columnas"] if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(faltantes)}")

    advertencias = []
    # Las columnas del dataset que esta iteración no usa se omiten sin avisar; solo se avisa de las ajenas al dataset
    conocidas = set(esquema.get("columnas_dataset", esquema["columnas"])) | {esquema["objetivo"]}
    sobrantes = [c for c in df.columns if c not in conocidas]
    if sobrantes:
        advertencias.append(f"Se ignoran columnas que el modelo no usa: {', '.join(sobrantes)}")

    X = df[esquema["columnas"]].copy()
    if X.isnull().any().any():
        raise ValueError("Los datos contienen valores nulos en las variables predictoras.")

    for col, info in esquema["categoricas"].items():
        nuevas = sorted(set(X[col].astype(str)) - set(info["categorias"]))
        if nuevas:
            advertencias.append(
                f"`{col}` tiene categorías que el modelo no conoce ({', '.join(nuevas[:5])}); "
                "se tratarán como categoría de referencia."
            )
    return X, advertencias


def objetivo_a_binario(serie: pd.Series) -> pd.Series:
    """Acepta yes/no o 1/0 y devuelve 0/1."""
    mapa = {"no": 0, "yes": 1, "0": 0, "1": 1}
    convertida = serie.astype(str).str.strip().str.lower().map(mapa)
    if convertida.isnull().any():
        raise ValueError("La columna `y` solo puede contener yes/no (o 1/0).")
    return convertida.astype(int)


def predecir(modelo, X: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Devuelve (clase predicha, probabilidad de contratar)."""
    clases = pd.Series(modelo.predict(X), index=X.index)
    proba = pd.Series(modelo.predict_proba(X)[:, 1], index=X.index)
    return clases, proba


def calcular_metricas(y_real: pd.Series, y_pred: pd.Series) -> dict:
    vn, fp, fn, vp = confusion_matrix(y_real, y_pred, labels=[0, 1]).ravel()
    return {
        "Accuracy": accuracy_score(y_real, y_pred),
        "Precision": precision_score(y_real, y_pred, zero_division=0),
        "Recall": recall_score(y_real, y_pred, zero_division=0),
        "F1": f1_score(y_real, y_pred, zero_division=0),
        "VN": int(vn), "FP": int(fp), "FN": int(fn), "VP": int(vp),
    }
