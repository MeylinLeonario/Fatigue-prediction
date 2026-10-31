# Validación real de M0–M3

Se reprodujeron los cuatro resultados comunicados por el usuario usando los CSV adjuntos: M0 RMSE=16.818, M1=17.933, M2=17.080 y M3=17.817. Las líneas originales eran resultados de referencia del Ridge fijo con alpha=10. La optimización produce nuevas predicciones y una tabla separada; no modifica esos resultados de referencia.

## Comparación en las mismas observaciones y folds

| Modelo | RMSE Ridge fijo | RMSE ajustado | MAE ajustado | R² ajustado | Cambio RMSE |
| --- | --- | --- | --- | --- | --- |
| M0 | 16.818 | 17.522 | 13.606 | 0.437 | +0.704 |
| M1 | 17.933 | 20.128 | 16.579 | 0.257 | +2.195 |
| M2 | 17.080 | 18.812 | 14.959 | 0.351 | +1.732 |
| M3 | 17.817 | 17.661 | 14.161 | 0.428 | -0.156 |

La búsqueda anidada no supera al M0 de referencia. M3 mejora 0.156 puntos respecto a su propio Ridge fijo, pero sigue siendo peor que M0. Los resultados negativos se conservan; no se cambiaron los umbrales de exclusión ni se eliminaron observaciones de prueba para mejorar las métricas.

## Procedimiento y alcance

- Cohorte común: 36 transiciones de 28 sujetos. Antes del requisito de casos completos M0–M3: 123 transiciones de 34 sujetos; se excluyeron 12 filas de ratings con claves temporales ambiguas.
- Cinco folds externos por sujeto. Tres folds internos por sujeto para elegir entre 16 candidatos Ridge/Huber/SVR y formulaciones de nivel/cambio. Selección por RMSE interno agrupado. Las exclusiones y el preprocesamiento se recalculan dentro de cada entrenamiento interno.
- Se reprodujo la función usada por el usuario: cinco features de auditoría (cuatro conductuales y Glu/tCr PFC), burden calculado como flagged/observed, umbral 0.20, mínimo ocho celdas observadas, robust-z de features 3.5; transiciones con robust-z >4.5 calculado después de excluir sujetos, eliminando todos los candidatos. Esta reproducción no usa la auditoría multimodal balanceada de M4, que es una política distinta.
- M0–M3 usan ratings, n-task y semiLASER. Se pudieron descargar esos archivos, DWS y choice-bias. El CSV de pupila excedió el límite de transferencia de 32 MiB: M4 completo no se ejecutó y no se imputaron datos ficticios para reemplazarlo.
- Entorno que reproduce exactamente la referencia: Python 3.12.14, NumPy 2.5.4, pandas 3.1.0, SciPy 1.18.1, scikit-learn 1.9.1, matplotlib 3.11.2; seaborn 0.13.2. Otro entorno con NumPy 2.3.5/pandas 2.2.3/scikit-learn 1.8.0 produjo resultados distintos; conservar las versiones y las asignaciones por sujeto es necesario para reproducibilidad exacta.
- Los intervalos bootstrap por sujeto de las diferencias de RMSE incluyen cero para M0, M1 y M3. Son intervalos de predicciones OOF fijas y no incluyen la incertidumbre de reajustar modelos. M2 empeora en esta comparación. No hay evidencia de una mejora estable.
- Se ensayó además entrenamiento con más sesiones disponibles manteniendo los sujetos externos de prueba en el entorno alternativo; tampoco redujo el RMSE frente a su referencia. Es un análisis exploratorio, no un resultado directamente comparable al entorno principal.
- Estas pruebas son exploratorias porque se propusieron después de ver resultados previos. No constituyen validación externa.

## Cómo interpretar la nueva salida

`Referencia Ridge ...` identifica el modelo original. Al finalizar la sección 8 aparece `Ajustado ...`, junto con `nested_comparison`. `RMSE_change < 0` indica mejora frente al Ridge de ese mismo grupo, no necesariamente frente a M0. El notebook principal sigue configurado para las seis fuentes y una auditoría multimodal; sus resultados pueden diferir de esta reproducción M0–M3 si cambia la política de calidad.

El notebook acepta `.csv`, `.csv.gz` y ZIP con un único CSV. El archivo de pupila comprimido permitirá completar M4 sin descartar esa modalidad.
