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
    # "Iteración 2": {
    #     "descripcion": "...",
    #     "modelos": {"Nombre del modelo": DIR_MODELOS / "modelo_iter2.joblib", ...},
    #     "metricas": DIR_MODELOS / "metricas_iter2.json",
    #     "datos_generalizacion": DIR_DATOS / "generalizacion_iter2.csv",
    # },
}

# Pendiente para el examen: selección de las variables más importantes.
# Cuando exista, se puede registrar aquí (p. ej. ranking de importancias por iteración)
# y mostrarlo en una pestaña nueva de app.py.
