"""Registro de iteraciones y modelos de la aplicación.

Es el único archivo que hay que editar para incorporar una nueva iteración:
basta con agregar una entrada a ITERACIONES (ver el ejemplo comentado abajo).
La app recorre este registro, por lo que no necesita más cambios.
"""
from pathlib import Path

NOMBRE_APP = "Predicción de Depósitos a Plazo"
SUBTITULO_APP = "Panel de apoyo a la gestión comercial: ¿qué clientes tienen más probabilidad de contratar?"

BASE = Path(__file__).parent
DIR_MODELOS = BASE / "models"
DIR_DATOS = BASE / "data"

ESQUEMA = DIR_MODELOS / "esquema.json"

ITERACIONES = {
    "Iteración 1": {
        "descripcion": (
            "Línea base de CRISP-DM: sin `duration`, preprocesador único "
            "(StandardScaler + OneHotEncoder) y optimización con GridSearchCV sobre F1."
        ),
        "modelos": {
            "Árbol de Decisión": DIR_MODELOS / "arbol_decision_iter1.joblib",
            "Regresión Logística": DIR_MODELOS / "regresion_logistica_iter1.joblib",
            "Random Forest": DIR_MODELOS / "random_forest_iter1.joblib",
        },
        "metricas": DIR_MODELOS / "metricas_iter1.json",
        "datos_generalizacion": DIR_DATOS / "generalizacion_iter1.csv",
    },
    "Iteración 2": {
        "descripcion": (
            "Vuelta a la comprensión del negocio: solo variables conocidas antes de llamar "
            "(13 variables, sin `day` ni `campaign`), con las mismas grillas de la iteración 1."
        ),
        "modelos": {
            "Árbol de Decisión": DIR_MODELOS / "arbol_decision_iter2.joblib",
            "Regresión Logística": DIR_MODELOS / "regresion_logistica_iter2.joblib",
            "Random Forest": DIR_MODELOS / "random_forest_iter2.joblib",
        },
        "metricas": DIR_MODELOS / "metricas_iter2.json",
        # La división de datos es la misma en todas las iteraciones: se reutiliza el mismo archivo.
        # Las variables que usa cada iteración se leen de su JSON de métricas (clave "variables").
        "datos_generalizacion": DIR_DATOS / "generalizacion_iter1.csv",
    },
    "Iteración 3": {
        "descripcion": (
            "Selección de variables por importancia: 10 variables, sin variables personales "
            "desactualizadas ni información posterior al contacto. Se comparan Random Forest, "
            "XGBoost y LightGBM con ajuste del umbral de decisión."
        ),
        "modelos": {
            "Random Forest (10 vars)": DIR_MODELOS / "random_forest_iter3.joblib",
            "XGBoost (10 vars)": DIR_MODELOS / "xgboost_iter3.joblib",
            "LightGBM (10 vars)": DIR_MODELOS / "lightgbm_iter3.joblib",
        },
        "metricas": DIR_MODELOS / "metricas_iter3.json",
        "datos_generalizacion": DIR_DATOS / "generalizacion_iter3.csv",
    },
}

