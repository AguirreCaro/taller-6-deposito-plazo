# Examen — Predicción de contratación de depósitos a plazo (CRISP-DM, 3 iteraciones)

**Integrantes:** Antonella Aedo · Carolina Aguirre · Benjamín Díaz

Metodología CRISP-DM sobre el dataset *Bank Marketing* (`bank-full.csv`): se predice si un cliente
contratará un depósito a plazo (`y`). Se desarrollaron **tres iteraciones**, y los resultados se consultan
en una aplicación web hecha con Streamlit. En cada iteración se comparan tres modelos, con su versión
base y su versión optimizada con `GridSearchCV` (en la iteración 3 no hay versión base, solo la optimizada):

- **Iteraciones 1 y 2:** Árbol de Decisión, Regresión Logística y Random Forest.
- **Iteración 3:** Random Forest, XGBoost y LightGBM, además del ajuste del umbral de decisión.

| Iteración | Qué cambia | Variables | Mejor modelo (F1 en prueba) |
|---|---|---|---|
| 1 | Línea base, sin `duration`, `GridSearchCV` | 15 | Random Forest, 0,4451 |
| 2 | Se vuelve a la comprensión del negocio: se quitan `day` y `campaign`, que no se conocen antes de llamar | 13 | Random Forest, 0,4263 |
| 3 | Se quitan `default`, `loan` y `education` (aportan poco), se prueban modelos de *boosting* y se ajusta el umbral de decisión con validación cruzada | 10 | LightGBM con umbral 0,62, 0,4698 |

**Cómo leer la comparación.** Las iteraciones 1 y 2 se evalúan con el umbral estándar (0,50) y la 3 con el
umbral óptimo de cada modelo, así que la mejora de la iteración 3 combina tres cambios a la vez (menos
variables, *boosting* y umbral). Entre los tres modelos de la iteración 3 la diferencia de F1 (0,457 a 0,470)
es similar a la variación de la validación cruzada. Con el umbral más alto el modelo hace menos llamadas
fallidas (688 falsos positivos frente a 1.231 en la iteración 2), pero detecta menos contrataciones
(*recall* de 50,7 % frente a 58,6 %). El notebook incluye un análisis de costo-beneficio: el modelo final
conviene cuando una contratación vale menos de unas 7,5 llamadas; sobre ese valor, el umbral más bajo de la
iteración 2 deja más beneficio neto. Esa razón depende de cifras que el banco no entrega, por lo que se
presenta con escenarios ilustrativos.

## Contenido de la carpeta

| Archivo / carpeta | Descripción |
|---|---|
| `Examen_AedoAntonella_AguirreCarolina_DiazBenjamin.ipynb` | Notebook con las 6 fases de CRISP-DM, recorridas en tres iteraciones (ya ejecutado, con sus resultados). |
| `bank-full.csv` | Dataset *Bank Marketing* (lo lee el notebook). |
| `app/` | Aplicación Streamlit (código, modelos entrenados y datos de generalización). |
| `.streamlit/config.toml` | Tema visual de la aplicación (verde y blanco). |
| `requirements.txt` | Librerías necesarias para el notebook y la aplicación. |

## Requisitos

- **Python 3.11 o superior** (desarrollado y probado con Python 3.13).
- Conexión a internet solo para instalar las librerías.

## Instalación

Desde una terminal, dentro de la carpeta raíz del proyecto (la que contiene `app/` y `requirements.txt`):

```bash
python -m venv .venv
```

Activar el entorno virtual:

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- Windows (cmd): `.venv\Scripts\activate.bat`
- macOS / Linux: `source .venv/bin/activate`

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

> `scikit-learn` está fijado en la versión **1.8.0** porque los modelos guardados en `app/models`
> se generaron con esa versión; con otra versión la carga puede fallar o mostrar advertencias.
> Lo mismo vale para `xgboost` (3.4.1) y `lightgbm` (4.7.0), que se necesitan para cargar los modelos de la iteración 3.

## Ejecutar la aplicación

Los modelos ya vienen entrenados dentro de `app/models`, por lo que **no es necesario ejecutar el
notebook** para probar la aplicación. Desde esta carpeta:

```bash
streamlit run app/app.py
```

Se abre en el navegador (por defecto en <http://localhost:8501>). Si el puerto está ocupado,
Streamlit indicará en la terminal el puerto alternativo o se puede usar `--server.port 8600`.
Importante: ejecutar el comando **desde la carpeta raíz del proyecto**, para que se aplique el tema de `.streamlit/`.

### Qué permite hacer la aplicación

1. **Predicción individual:** se elige la iteración y aparece un formulario con los datos de un cliente (solo
   las variables que usa esa iteración, todas conocidas antes de llamarlo). Consulta a los tres modelos al
   mismo tiempo y muestra, por modelo, la predicción (*Contratará / No contratará*) y la probabilidad de
   contratación. En la iteración 3 la decisión usa el **umbral óptimo de cada modelo** (no 0,50) y se
   indica cuál es el modelo ganador.
2. **Datos de generalización:** se elige la iteración y se ejecutan sus modelos sobre 9.043 registros que
   **no participaron en el entrenamiento ni en la validación cruzada** (el 20 % de prueba). Muestra Accuracy,
   Precision, Recall y F1, matriz de confusión y la tabla de predicciones, descargable en CSV.
3. **Desempeño de los modelos:** puntajes de todas las iteraciones o de una sola (filtro), comparación entre
   versiones (base, optimizada y optimizada con umbral), ranking de modelos, hiperparámetros óptimos y modelo
   seleccionado.

## Ejecutar el notebook

Abrir `Examen_AedoAntonella_AguirreCarolina_DiazBenjamin.ipynb` con Jupyter (`jupyter notebook`),
VS Code u otro entorno, seleccionando el Python del entorno virtual creado arriba. El notebook
debe abrirse con esta carpeta como directorio de trabajo (así lo hacen Jupyter y VS Code por defecto),
porque lee `bank-full.csv` con una ruta relativa.

- El notebook entregado **ya está ejecutado**; sus resultados se pueden revisar sin volver a correrlo.
- Para volver a ejecutarlo completo: *Run All*. Los `GridSearchCV` (sobre todo los de Random Forest)
  tardan varios minutos, y más en equipos con menos núcleos. Las iteraciones 1 y 2 tardaron cerca de
  15 minutos en un equipo de 12 núcleos; la iteración 3 agrega las búsquedas de XGBoost y LightGBM y la
  búsqueda del umbral, y su tiempo no se midió.
- Al terminar, la **Fase 6** regenera los archivos de `app/models` y `app/data` que usa la aplicación
  y comprueba que los modelos guardados predicen exactamente igual que los del notebook. Si se
  reejecuta, conviene reiniciar la aplicación.

## Decisiones de diseño relevantes

- Se excluye `duration` (duración de la llamada): no se conoce antes de contactar al cliente. En la
  iteración 2 se aplica el mismo criterio a `day` y `campaign`. En la iteración 3 se quitan además `default`,
  `loan` y `education` por su bajo aporte. La aplicación solo pide las variables que usa cada iteración.
- El modelo de cada iteración se elige por su F1 en validación cruzada, no con los datos de prueba. El umbral
  de decisión de la iteración 3 también se elige con validación cruzada sobre el conjunto de entrenamiento;
  el conjunto de prueba solo se usa para evaluar.
- El preprocesamiento (`StandardScaler` + `OneHotEncoder`) va **dentro** del `Pipeline` de cada modelo.
  La aplicación llama directamente a ese `Pipeline`, por lo que el preprocesamiento al predecir es
  idéntico al del entrenamiento.
- Para el desbalance de clases (11,7 % de contrataciones), los modelos de las iteraciones 1 y 2 (y el
  Random Forest de la 3) usan `class_weight='balanced'`, y los de *boosting* de la iteración 3 usan `scale_pos_weight`. Por eso la
  probabilidad mostrada sirve para comparar clientes entre sí, no como tasa real de contratación.

## Estructura de la aplicación y próximas iteraciones

```
app/
  app.py          # pantallas y lógica de la interfaz
  config.py       # registro de iteraciones y modelos (único archivo a editar al agregar una)
  utils.py        # carga de modelos, validación de datos y métricas
  formulario.py   # formulario de ingreso de datos del cliente
  estilos.py      # tema, encabezado y gráficos
  models/         # modelos (.joblib), métricas (con la lista de variables de cada iteración) y esquema
  data/           # datos de generalización
```

Para sumar una nueva iteración (la 4, por ejemplo): exportar sus modelos y métricas con el sufijo
`iter4` (función `exportar_iteracion` del notebook, como en la sección 6.7, indicando las variables que usa y,
si ajusta el umbral, `umbrales=`) y agregar una entrada al diccionario `ITERACIONES` de `app/config.py`. La aplicación recorre ese registro y
la nueva iteración aparece en el selector y en la comparación de desempeño. La lista de variables de cada
iteración se lee de su JSON de métricas, así que el formulario y la evaluación se ajustan solos. Si la
iteración agrega pasos de preparación propios (por ejemplo, una clase que crea variables nuevas), esa clase
debe quedar en un módulo dentro de `app/`, para que los modelos guardados puedan cargarse desde la aplicación.

## Solución de problemas

- **`ModuleNotFoundError`**: el entorno virtual no está activado o falta `pip install -r requirements.txt`.
- **Advertencia o error al cargar un `.joblib`**: la versión de `scikit-learn` (1.8.0), `xgboost` (3.4.1) o `lightgbm` (4.7.0) no coincide con `requirements.txt`.
- **La app no encuentra los modelos**: ejecutar el notebook completo (Fase 6) para regenerarlos.
- **Cambios no visibles tras reejecutar el notebook**: detener Streamlit (Ctrl+C) y volver a ejecutarlo.
