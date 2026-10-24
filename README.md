# Predicción de fatiga cognitiva

Análisis exploratorio de si las medidas de la sesión **t** aportan información sobre la fatiga subjetiva en **t+1**, por encima de la fatiga actual, sesión y condición. Datos de Wiehler et al. (2022), [Zenodo 6795446](https://doi.org/10.5281/zenodo.6795446), asociados a *A neuro-metabolic account of why daylong cognitive work alters the control of economic decisions*.

El resultado estudiado es el siguiente autorreporte. Esta base no demuestra que un marcador anticipe la experiencia consciente de fatiga ni establece causalidad. La correspondencia entre sesión y momento exacto de adquisición debe comprobarse en el protocolo antes de interpretar el análisis como predicción prospectiva.

## Inicio rápido

Python 3.11 o posterior. Desde la raíz del repositorio:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[notebook]'
python -m fatigue_prediction download
python -m fatigue_prediction run
# Opcional: añade Random Forest con hiperparámetros fijos
python -m fatigue_prediction run --rf --output results/with_rf
python -m unittest discover -s tests -v
# Comprobar celdas con datos sintéticos, sin descargar datos
MPLBACKEND=Agg python scripts/validate_notebook.py
jupyter lab program.ipynb
```

En Windows, activar con `.venv\Scripts\activate`. Los comandos `python -m fatigue_prediction` también funcionan desde la raíz sin instalar el paquete si ya están instaladas sus dependencias.

La descarga requiere acceso HTTPS a `zenodo.org`. Si la red lo bloquea, descargar manualmente los cuatro CSV de la tabla y colocarlos en `data/`, con los nombres originales. No es necesario renombrar `ntask`. Los archivos se verifican contra los MD5 publicados; un archivo modificado se rechaza con un error explícito. Los datos no se incorporan a Git.

## Datos

| Alias | Archivo original | Uso |
| --- | --- | --- |
| ratings | `MRSFATIGUE_ratings_session_zenodo.csv` | Autorreportes; objetivo `Fatigue` |
| ntask | `MRSFATIGUE_ntask_session_zenodo.csv` | Ensayos conductuales |
| glu | `MRSFATIGUE_MRS_semiLaser_session_ratio_Glu_tCr_zenodo.csv` | Glu/tCr por ROI |
| dws | `MRSFATIGUE_MRS_DWS_session_ADC_log_Glu_Gln_lin_zenodo.csv` | ADC por ROI, disponibilidad descriptiva |
| choice | `MRSFATIGUE_choice_bias_parameter_zenodo.csv` | Descarga opcional; sin modelo implementado |
| pupil | `MRSFATIGUE_pupil_choice_session_zenodo.csv` | Descarga opcional; sin modelo implementado |

`download --all` incluye los seis archivos, aproximadamente 167 MB en total. El análisis principal requiere los primeros cuatro. Véase el [diccionario y contrato de datos](docs/data.md).

## Qué ejecuta

1. Valida esquema, claves, variables numéricas e integridad de los archivos.
2. Excluye todas las respuestas de fatiga con clave sujeto–condición–sesión duplicada, conservándolas para auditoría. No elige arbitrariamente la primera.
3. Construye pares con la misma condición y sujeto, y diferencia exacta de una sesión. No salta sesiones ausentes.
4. Agrega conducta por sesión y une MRS con cardinalidad uno a uno; no interpola MRS ni toma valores de sesiones posteriores.
5. Evalúa dos cohortes de casos completos: conducta (M0/M1) y multimodal (M0–M3). Cada comparación usa las mismas filas y los mismos folds por participante.
6. Exporta métricas OOF, predicciones, errores por transición, disponibilidad, asociaciones OLS con errores agrupados y un modelo basal con intercepto aleatorio.

| Modelo | Predictores |
| --- | --- |
| Persistencia | Fatiga futura = fatiga actual |
| Media del entrenamiento | Media de fatiga futura de los participantes de entrenamiento |
| M0 | Fatiga actual + sesión + condición |
| M1 | M0 + exactitud, RT mediano y cambios entre mitades de sesión |
| M2 | M0 + Glu/tCr PFC |
| M3 | M1 + Glu/tCr PFC |

La validación por sujeto estima generalización a **participantes no vistos** en este conjunto experimental. No evalúa automáticamente un despliegue futuro en el mismo participante. El escalado y la codificación categórica se ajustan dentro de cada fold. No se seleccionan hiperparámetros con los datos de prueba.

## Resultados y reproducibilidad

La carpeta de salida contiene `comparison.csv`, métricas y folds de cada cohorte/algoritmo, predicciones individuales, errores, intervalos bootstrap condicionales, `model_frame.csv`, `ambiguous_ratings.csv`, resúmenes estadísticos y `audit.json` con hashes, tamaños, versiones, semilla y configuración. Utilice carpetas distintas para conservar ejecuciones anteriores: los archivos con el mismo nombre se reemplazan.

```bash
python -m fatigue_prediction run --data-dir data --output results/run_01 --folds 5 --seed 42 --bootstrap 2000
```

R² puede ser negativo. MAE y RMSE se expresan en la escala del autorreporte. Las diferencias positivas exportadas significan mejora respecto de M0. No comparar directamente métricas entre cohortes como si cambiaran únicamente los predictores.

**Estado de validación:** se comprobó el flujo con datos sintéticos y pruebas automatizadas. No se recalcularon resultados empíricos de Zenodo en esta revisión porque los CSV no estaban presentes y el entorno restringe el acceso al dominio. Las cifras guardadas en el notebook anterior no constituyen resultados verificados de esta versión. El manifiesto de versiones de prueba está en `docs/validation-environment.txt`; no es un lockfile multiplataforma.

Consulte [metodología y limitaciones](docs/methodology.md) y [auditoría del notebook original](docs/audit.md). El historial Git conserva el notebook original. No se ha añadido una licencia al código: su titular debe elegirla antes de distribuirlo bajo una licencia concreta; la procedencia de los datos se cita por separado.
