# Validación real del análisis longitudinal v3

Se ejecutaron todas las celdas con los cinco CSV descargables. Pupila no pudo transferirse porque superó 32 MiB; el notebook la integrará si se proporciona comprimida. Además se comprobó la ruta de integración de las seis fuentes con fixtures sintéticos separados. No se sustituyeron mediciones reales por valores sintéticos.

## Pregunta y muestra

Asociación entre Glu/tCr PFC actual y fatiga en la sesión siguiente, ajustando fatiga actual, sesión y condición. Casos completos: **36 transiciones de 28 sujetos**; solo ocho sujetos tienen dos transiciones. Los registros temporalmente ambiguos se excluyen antes de construir el objetivo. La inferencia principal conserva valores extremos temporalmente válidos y la exclusión se evalúa como sensibilidad.

## Modelo principal y diagnóstico

Se intentó un modelo mixto REML con intercepto aleatorio. L-BFGS falló por matriz singular; Powell convergió nominalmente, pero la varianza aleatoria fue casi nula y hubo advertencia de Hessiano no definido positivo. Por ello **no se interpretan los intervalos del mixto como evidencia fiable**. La alternativa principal es OLS con errores CR1 agrupados por sujeto, corrección de muestra y referencia t con 27 grados de libertad.

Por +0.1 unidades Glu/tCr PFC, la asociación ajustada es **2.945 puntos de fatiga futura**, IC agrupado 95% **[0.229, 5.661]**, p bilateral=0.0346. Este contraste es exploratorio: el protocolo se reformuló después de ver análisis previos y no es confirmatorio.

El bootstrap por sujeto tuvo 1999 reajustes válidos de 2000; uno fue omitido por rango deficiente y se registra. El IC percentil 95% es **[-0.240, 5.701]**, que incluye cero. Este remuestreo conserva la muestra de casos completos y no incorpora incertidumbre por datos ausentes ni decisiones analíticas previas.

## Sensibilidad a la limpieza anterior

Se conservan cuatro features conductuales y Glu/tCr PFC para la regla previa de outliers. En la auditoría global se identifican tres sujetos y, después de excluirlos, dos transiciones candidatas: **se excluyen ambas**. Los cambios de muestra impiden interpretar diferencias de coeficientes como mejora automática del modelo.

| Escenario | Transiciones | Sujetos | Coeficiente por +0.1 Glu/tCr | IC 95% | p |
|---|---:|---:|---:|---|---:|
| sin_exclusiones | 36 | 28 | 2.945 | [0.229, 5.661] | 0.0346 |
| solo_sujetos | 33 | 26 | 2.325 | [-0.910, 5.559] | 0.1513 |
| solo_extremos | 35 | 27 | 1.791 | [-0.336, 3.918] | 0.0954 |
| ambas_reglas | 32 | 25 | 0.716 | [-1.372, 2.805] | 0.4859 |

La asociación de glutamato **no es estable frente a estas exclusiones**. La descomposición exploratoria intra/interindividual también muestra que el coeficiente conjunto no debe interpretarse como un efecto dentro del sujeto: hay pocos sujetos repetidos y el IC del componente intraindividual incluye cero. No se concluye que el marcador permita anticipar fatiga en sujetos nuevos.

## t de Student pareada: pregunta complementaria

Sesiones 0 y 5 fijadas: **38 sujetos con ambos extremos inequívocos**, una diferencia por persona. Cambio medio final−inicial: **44.031 puntos**, IC t 95% **[36.028, 52.034]**, t(37)=11.148, p bilateral=2.19e-13. Este cambio medio no demuestra asociación con glutamato ni explica qué condición lo causa.

## Otras modalidades y alcance

Cada feature complementaria se contrasta por separado con covariables básicas, mínimos de filas/sujetos y control Holm para esa familia. Las métricas de calidad no se interpretan como mecanismos. Las muestras pueden diferir entre features. Las medias de glutamato usadas en la descomposición intra/interindividual son descriptivas y no features prospectivas.

El notebook v2 mantiene la predicción como exploratoria. La t pareada, los coeficientes ajustados y los scores OOF responden preguntas distintas. Ninguno de estos resultados justifica una conclusión causal o una mejora de RMSE.

## Verificación

Notebook válido (22 celdas), ejecución real completa, bootstrap agrupado, omisión explícita del ajuste mixto no admisible, pruebas Holm verificadas y escenarios de exclusión comprobados. Ruta con seis fuentes y pupila validada con fixtures sintéticos. Las versiones, hashes de entrada, exclusiones y ajustes se exportan en el manifiesto y tablas al ejecutar; los CSV originales no se subieron al repositorio.
