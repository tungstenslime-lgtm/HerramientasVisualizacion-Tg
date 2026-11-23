# HerramientasVisualizacion — Tablero del SIE de Banxico (modificado)

Repositorio propio a partir del repo base del docente:
https://github.com/BOWadapter/HerramientasVisualizacion

Archivos clonados del repo base (2 archivos principales):
- `dashboard_banxico.py` — el dashboard en Streamlit (modificado, ver abajo)
- `requirements.txt` — dependencias (sin cambios)

## Cómo correrlo

```bash
pip install -r requirements.txt
streamlit run dashboard_banxico.py
```

El token del SIE **no va en este archivo**. Crea la carpeta `.streamlit`
junto a `dashboard_banxico.py` y dentro un archivo `secrets.toml` con:

```toml
banxico_token = "pega-aqui-tu-token"
```

Pídelo gratis en https://www.banxico.org.mx/SieAPIRest/service/v1/token
Por defecto consulta la serie `SF43718` (tipo de cambio FIX), 2021–2025.

## Cambio realizado

### Gráfica eliminada: "Promedio por mes y año" (mapa de calor)
Estaba abajo a la derecha. Se quitó porque no aportaba al muestreo de la
información:
- Era redundante: el nivel ya se ve en "La serie y su tendencia" y el
  cambio mensual ya se ve en "Cambio de un mes a otro".
- El promedio mensual suaviza los datos y oculta justo lo que interesa
  en un tipo de cambio: la volatilidad día a día.
- Con valores del FIX tan cercanos entre sí, la escala de color apenas
  distinguía un mes de otro.

### Gráfica añadida: "Volatilidad móvil a 30 días"
Ocupa el lugar del mapa de calor (abajo a la derecha). Es la desviación
estándar móvil de 30 días de la variación diaria (%), con el máximo
marcado en rojo.
- Muestra **cuándo** el tipo de cambio estuvo estable y cuándo se movió
  mucho, algo que el boxplot por año solo resume y que la serie de nivel
  no muestra.
- Sirve para elegir ventanas de muestreo estables y para detectar
  periodos de inestabilidad (por ejemplo, picos como los de junio de 2024).

## Gráficas del tablero (4)

1. La serie y su tendencia (o comparación en base 100, si hay varias series)
2. Cambio de un mes a otro
3. Qué tan movido estuvo cada año (boxplot de la variación diaria)
4. **Volatilidad móvil a 30 días** (nueva)

## Prueba de implementación

Sin token real no se puede consultar el SIE, así que la prueba simula su
respuesta con una serie FIX sintética (2021–2025, con un pico de
volatilidad en junio de 2024) y ejecuta la app completa con AppTest de
Streamlit. Resultado: la app arranca sin errores, muestra título,
4 métricas y las 4 gráficas, y el mapa de calor ya no aparece.
Volatilidad media 30 días en la prueba: 0.625 %, máx: 2.012 %.

Nota: la prueba se hizo con pandas 3.1.1 (la versión que instala
`requirements.txt` hoy). Con pandas 2.1 el código base falla en
`resample("ME")`, que exige pandas ≥ 2.2; en Streamlit Cloud, con las
dependencias actuales, funciona.
