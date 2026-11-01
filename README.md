# Análisis de fatiga cognitiva

El análisis principal ahora es **estadístico longitudinal**, centrado en asociaciones ajustadas, tamaños de efecto e intervalos de confianza.

- **Empezar aquí:** [fatigue_analysis_longitudinal_v3.ipynb](fatigue_analysis_longitudinal_v3.ipynb).
- Resultados reales y límites: [longitudinal_validation.md](longitudinal_validation.md).
- Predicción exploratoria y optimización OOF: [fatigue_analysis_clean_v2.ipynb](fatigue_analysis_clean_v2.ipynb).
- Reproducción de los resultados predictivos previos: [real_m03_validation.md](real_m03_validation.md).

## Ejecución

Colocar los CSV originales en `data/` (o configurar `DATA_DIR`) y usar **Restart Kernel → Run All**. Se aceptan `.csv`, `.csv.gz` y ZIP con un único CSV.

```bash
python -m pip install numpy pandas scipy matplotlib seaborn statsmodels scikit-learn jupyterlab
```

El notebook v3 requiere ratings, n-task y semiLASER; procesa DWS, pupila y choice-bias cuando están disponibles y declara cualquier ausencia. El modelo principal de glutamato utiliza ratings y semiLASER; la descripción conductual y las sensibilidades utilizan n-task. Las seis fuentes se incorporan al inventario y los análisis complementarios cuando están presentes.

El modelo mixto se evalúa mediante diagnósticos; si su intercepto aleatorio no es estimable de forma fiable, se informa y se usa regresión con errores agrupados por sujeto y referencia t. Incluye una t pareada entre sesiones 0 y 5, bootstrap por sujeto, sensibilidad a las exclusiones y análisis complementario de modalidades con ajuste Holm.

La inferencia principal no elimina observaciones por su cambio de fatiga. La sensibilidad conserva la regla de limpieza previamente utilizada, eliminando todos los candidatos extremos, sin límite de uno. Los archivos originales no se modifican; los resultados se guardan en `fatigue_longitudinal_results/`.

Las asociaciones estadísticas no son métricas OOF ni pruebas de causalidad. Conservar el manifiesto de versiones, entradas y reglas para reproducir cada ejecución.
