# Metodología e interpretación

## Pregunta que los datos permiten examinar

¿Añaden conducta o Glu/tCr PFC de la sesión t capacidad para predecir el autorreporte de fatiga de t+1, condicionando por el autorreporte de t y las covariables experimentales?

No se identifica el instante de aparición de la conciencia de fatiga. La numeración de sesiones no garantiza por sí sola que la ventana de adquisición de cada marcador finalice antes del autorreporte objetivo. Hasta comprobar el protocolo y las marcas temporales, describir el resultado como asociación entre sesiones y evaluación exploratoria de predicción.

## Asociación y predicción

El modelo basal longitudinal tiene intercepto aleatorio por participante y ajuste ML (`reml=False`). Se informa convergencia y advertencias, incluyendo posibles soluciones en el límite. Las asociaciones M0–M3 se ajustan con OLS y errores agrupados por sujeto, sobre una muestra común dentro de cada cohorte. Una matriz singular se declara no estimable. Los errores agrupados no corrigen confusión, sesgo por casos completos ni todos los problemas de inferencia con pocos grupos. El intercepto aleatorio tampoco separa automáticamente efectos intraindividuales e interindividuales.

Los R² de ajuste, AIC y coeficientes de esos resúmenes no son pruebas de valor predictivo. La comparación predictiva usa regresión lineal y, opcionalmente, Random Forest con parámetros fijos; cada modelo se vuelve a entrenar por fold. Si se añade Elastic Net o se eligen predictores/hiperparámetros, se necesitará validación interna también agrupada por sujeto, dentro de cada fold externo.

## Diseño de validación

GroupKFold, cinco folds por defecto, conserva todas las transiciones de cada sujeto en un único conjunto de prueba. Todos los modelos de una comparación comparten filas y particiones. Las transformaciones se ajustan únicamente en entrenamiento. Se conservan las predicciones de prueba y la identidad del fold. Las métricas globales se calculan reuniendo las predicciones OOF, sin promediar R² de folds con tamaños distintos.

La cohorte conductual permite aprovechar sujetos sin MRS; la multimodal impone disponibilidad de todos los predictores M0–M3. M0 se reevalúa en cada cohorte. No se considera que las dos cohortes sean intercambiables. Persistencia y media del entrenamiento permiten juzgar si la complejidad del modelo aporta valor sobre referencias simples.

Las sesiones no se separan cronológicamente entre entrenamiento y prueba: el objetivo de este diseño es generalizar a nuevos sujetos bajo el mismo protocolo, no a días futuros ni a nuevas condiciones. Una evaluación prospectiva exige un conjunto independiente y conocer las ventanas reales de adquisición.

## Incertidumbre y errores difíciles

El bootstrap remuestrea **participantes**, conserva juntas sus transiciones y compara modelos sobre las mismas muestras. Los cuantiles 2.5/50/97.5% describen incertidumbre condicional a los modelos OOF ya ajustados. No incluyen todo el efecto de volver a entrenar ni sustituyen validación externa; no constituyen una prueba confirmatoria tras explorar modelos.

Se exportan errores OOF por transición y agrupados por sesión y condición. Se pueden inspeccionar grandes cambios, cobertura y tamaños de grupo sin eliminar observaciones según el error. El error de un autorreporte puede proceder de variación real, ruido de medición, efectos de techo/suelo, heterogeneidad individual o falta de predictores. Estas hipótesis requieren comprobación y no se deducen de un residual grande.

La revisión elimina la selección por Cook's D calculado con toda la muestra antes de validar. Este filtro usa el objetivo de los futuros conjuntos de prueba y produce estimaciones optimistas sobre una población seleccionada. Si se estudia robustez, definir reglas antes del análisis o estimarlas solo con entrenamiento, manteniendo intacto el conjunto de prueba.

## Antes de una conclusión científica

Verificar cronología y codificación con el protocolo, inspeccionar patrones de datos faltantes y mezcla de tareas, comprobar convergencia y tamaño efectivo en sujetos, y registrar de antemano la comparación primaria. La exploración del notebook original ya ha utilizado estos datos: los análisis revisados siguen siendo exploratorios. No interpretar ausencia de mejora como prueba de ausencia de relación biológica, ni una mejora pequeña como biomarcador validado.
