# Contrato de datos

Fuente fija: https://zenodo.org/records/6795446, versión 1, publicada el 4 de julio de 2022. El manifiesto `fatigue_prediction/data.py` conserva los nombres y MD5 publicados. No se consulta «la última versión» automáticamente.

## Claves y columnas

Todas las tablas requieren `subject_id`, `condition`, `session`, sin ausentes. Sesión es un entero finito. Los identificadores no se emplean como predictores. Se conserva la codificación de condición del archivo, sin suponer que todo valor distinto de `hard` sea `easy`.

- **ratings**: `question`, `rating`; se selecciona exactamente `Fatigue`. Se valida escala 0–100, conforme a las salidas históricas del notebook. Stress y Hunger no entran en los modelos actuales.
- **ntask**: `task`, `block`, `trial`, `performance`, `response_time`, `rule_switch`. Performance y rule_switch deben ser 0/1 o ausentes. Bloque y ensayo definen el orden dentro de sujeto–condición–sesión. Se rechazan empates entre tareas: sin información adicional, su orden no es identificable.
- **glu**: `ROI`, `Glu_tCr`; clave única sujeto–condición–sesión–ROI.
- **dws**: `ROI`, `ADC_log_Glu_Gln_lin`; la misma unicidad. Se mantiene la denominación original del ADC; no se asignan unidades no verificadas.

Las columnas adicionales se permiten, pero no se incorporan automáticamente como predictores. La revisión del esquema se basa en las salidas conservadas del notebook y en el registro público; deberá contrastarse con los CSV al disponer de ellos.

## Variables derivadas

`fatigue_future` es la siguiente respuesta válida **solo si** `session_future - session == 1`. Se agrupa por sujeto y condición antes del desplazamiento. `delta_fatigue = fatigue_future - fatigue` se conserva para auditoría, sin entrar como predictor. El objetivo primario es el nivel futuro; el cambio no se usa como desenlace adicional en esta versión.

Exactitud = media de performance no ausente; se exporta su denominador `n_performance`. RT mediano se calcula sobre RT estrictamente positivos y no ausentes, incluyendo respuestas correctas e incorrectas. Se exporta `n_valid_rt`; no se aplica un umbral superior arbitrario. `n_trials` incluye todos los ensayos. Las mitades se definen por posición cronológica, usando el mismo criterio en todo el flujo; para un número impar, la primera mitad tiene un ensayo adicional. Los cambios son segunda mitad menos primera mitad, usando mediana para RT y media para exactitud.

Se combinan las tareas originales, como en el análisis exploratorio, y se exporta `n_tasks`. Su mezcla puede confundir cambios de rendimiento: antes de atribuirlos a fatiga conviene contrastar agregados específicos por tarea y el orden real del protocolo. No se inventa un orden para resolver empates.

MRS se transforma a columnas por ROI sin promediar duplicados. Glu/tCr PFC es la única variable fisiológica en los modelos predictivos actuales. VC y DWS sirven para auditar disponibilidad y preparar análisis futuros; pupila y decisiones necesitan un diseño temporal específico antes de incorporarlas.

## Ausentes y trazabilidad

No se imputa ni se interpola. Una medición de MRS posterior nunca rellena una sesión anterior. Los casos completos se seleccionan una vez por comparación. Esto puede producir selección de participantes/sesiones: examinar disponibilidad y distribución antes de interpretar resultados.

Los duplicados de fatiga se exportan, incluso si sus valores coinciden. La ausencia de marcas temporales impide decidir cuál corresponde a cada momento. Un rating ausente invalida los pares que lo necesitan; no se permite saltarlo para crear un par no consecutivo.
