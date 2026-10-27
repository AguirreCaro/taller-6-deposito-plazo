# Taller 6 — Predicción de contratación de depósitos a plazo (CRISP-DM, iteración 1)

**Integrantes:** Antonella Aedo · Carolina Aguirre · Benjamín Díaz

Primera iteración de la metodología CRISP-DM sobre el dataset *Bank Marketing* (`bank-full.csv`):
se predice si un cliente contratará un depósito a plazo (`y`). Se comparan tres modelos
(Árbol de Decisión, Regresión Logística y Random Forest), cada uno con su versión base y su versión
optimizada con `GridSearchCV`, y los resultados se consultan en una aplicación web hecha con Streamlit.

## Contenido de la carpeta

| Archivo / carpeta | Descripción |
|---|---|
| `Taller_6AedoAntonella_AguirreCarolina_DiazBenjamin.ipynb` | Notebook con las 6 fases de CRISP-DM (ya ejecutado, con sus resultados). |
| `bank-full.csv` | Dataset *Bank Marketing* (lo lee el notebook). |
| `app/` | Aplicación Streamlit (código, modelos entrenados y datos de generalización). |
| `.streamlit/config.toml` | Tema visual de la aplicación (verde y blanco). |
| `requirements.txt` | Librerías necesarias para el notebook y la aplicación. |

## Requisitos

- **Python 3.11 o superior** (desarrollado y probado con Python 3.13).
- Conexión a internet solo para instalar las librerías.

## Instalación

Desde una terminal, dentro de esta carpeta (`Taller 6`):

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

## Ejecutar la aplicación

Los modelos ya vienen entrenados dentro de `app/models`, por lo que **no es necesario ejecutar el
notebook** para probar la aplicación. Desde esta carpeta:

```bash
streamlit run app/app.py
```

Se abre en el navegador (por defecto en <http://localhost:8501>). Si el puerto está ocupado,
Streamlit indicará en la terminal el puerto alternativo o se puede usar `--server.port 8600`.
Importante: ejecutar el comando **desde la carpeta `Taller 6`**, para que se aplique el tema de `.streamlit/`.

### Qué permite hacer la aplicación

1. **Predicción individual:** formulario con los datos de un cliente (los que se conocen antes de
   llamarlo). Consulta a los tres modelos al mismo tiempo y muestra, por modelo, la predicción
   (*Contratará / No contratará*) y la probabilidad de contratación.
2. **Datos de generalización:** ejecuta los modelos sobre 9.043 registros que **no participaron en el
   entrenamiento ni en la validación cruzada** (el 20 % de prueba). Muestra Accuracy, Precision,
   Recall y F1, matriz de confusión y la tabla de predicciones, descargable en CSV.
3. **Desempeño de los modelos:** puntajes de cada iteración, comparación entre la versión base y la
   optimizada, hiperparámetros óptimos y modelo seleccionado (Random Forest, F1 = 0,4451).

## Ejecutar el notebook

Abrir `Taller_6AedoAntonella_AguirreCarolina_DiazBenjamin.ipynb` con Jupyter (`jupyter notebook`),
VS Code u otro entorno, seleccionando el Python del entorno virtual creado arriba. El notebook
debe abrirse con esta carpeta como directorio de trabajo (así lo hacen Jupyter y VS Code por defecto),
porque lee `bank-full.csv` con una ruta relativa.

- El notebook entregado **ya está ejecutado**; sus resultados se pueden revisar sin volver a correrlo.
- Para volver a ejecutarlo completo: *Run All*. Los `GridSearchCV` (sobre todo el de Random Forest)
  tardan varios minutos, entre 15 y 40 según el equipo.
- Al terminar, la **Fase 6** regenera los archivos de `app/models` y `app/data` que usa la aplicación
  y comprueba que los modelos guardados predicen exactamente igual que los del notebook. Si se
  reejecuta, conviene reiniciar la aplicación.

## Decisiones de diseño relevantes

- Se excluye `duration` (duración de la llamada): no se conoce antes de contactar al cliente.
- El preprocesamiento (`StandardScaler` + `OneHotEncoder`) va **dentro** del `Pipeline` de cada modelo.
  La aplicación llama directamente a ese `Pipeline`, por lo que el preprocesamiento al predecir es
  idéntico al del entrenamiento.
- Los modelos optimizados usan `class_weight='balanced'` por el desbalance de clases (11,7 % de
  contrataciones). Por eso la probabilidad mostrada sirve para comparar clientes entre sí, no como
  tasa real de contratación.

## Estructura de la aplicación y próximas iteraciones

```
app/
  app.py          # pantallas y lógica de la interfaz
  config.py       # registro de iteraciones y modelos (único archivo a editar al agregar una)
  utils.py        # carga de modelos, validación de datos y métricas
  formulario.py   # formulario de ingreso de datos del cliente
  estilos.py      # tema, encabezado y gráficos
  models/         # modelos (.joblib), métricas y esquema de variables
  data/           # datos de generalización
```

Para sumar la iteración 2 o 3: exportar sus modelos, métricas y datos de generalización con el sufijo
`iter2` / `iter3` (mismo bloque de la Fase 6 del notebook) y agregar una entrada al diccionario
`ITERACIONES` de `app/config.py`. La aplicación recorre ese registro y la nueva iteración aparece en
el selector y en la comparación de desempeño.

## Solución de problemas

- **`ModuleNotFoundError`**: el entorno virtual no está activado o falta `pip install -r requirements.txt`.
- **Advertencia o error al cargar un `.joblib`**: la versión de `scikit-learn` no es la 1.8.0.
- **La app no encuentra los modelos**: ejecutar el notebook completo (Fase 6) para regenerarlos.
- **Cambios no visibles tras reejecutar el notebook**: detener Streamlit (Ctrl+C) y volver a ejecutarlo.
