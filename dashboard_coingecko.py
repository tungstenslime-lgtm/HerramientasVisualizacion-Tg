# Dashboard CoinGecko en Streamlit — EP.03.01 Evidencia de Producto
# Herramientas de Visualización · IDIA223 · UPQ
#
# Tarea (Classroom, Jairo Pacindo Piña, entrega 25/11/2026 8:40):
#   "Usando la api de tu evaluacion, realiza la integracion o
#    transformacion a un dasboard usando streamlit"
#   "Sube tu trabajo a github y adjunta como evidencia el URL"
#
# API: CoinGecko — /coins/markets, vs_currency=usd,
#      order=market_cap_desc, per_page=250, page=1
#      Header: x-cg-demo-api-key
#
# EL TOKEN NO VA EN ESTE ARCHIVO NI EN EL REPO.
# En tu equipo: crea la carpeta .streamlit y dentro un archivo
# secrets.toml con una sola línea:
#     coingecko_token = "pega-aqui-tu-token"
# O poné la variable de entorno COINGECKO_API_KEY.
# El archivo secrets.toml y token.txt nunca se suben al repositorio.
# Sin token, el dashboard usa datos_limpios.csv (250 activos,
# consultados el 24/11/2026), que sí está en el repo.
#
#     pip install -r requirements.txt
#     streamlit run dashboard_coingecko.py

import os
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st
from matplotlib.patches import Patch

# ─── Paleta de la actividad ────────────────────────────────────────────
AZUL = "#1C4C9A"
GRIS = "#B9C3D1"
NARANJA = "#E69F00"
VERDE = "#009E73"
AZUL_CLARO = "#56B4E9"

plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["axes.titlesize"] = 13
plt.rcParams["axes.labelsize"] = 11

COLUMNAS = [
    "name",
    "current_price",
    "market_cap",
    "total_volume",
    "price_change_percentage_24h",
    "market_cap_rank",
]
NUMERICAS = COLUMNAS[1:]

st.set_page_config(page_title="Tablero CoinGecko", layout="wide")


def leer_token():
    try:
        if "coingecko_token" in st.secrets:
            return str(st.secrets["coingecko_token"]).strip()
    except Exception:
        pass
    if os.environ.get("COINGECKO_API_KEY"):
        return os.environ["COINGECKO_API_KEY"].strip()
    return None


def limpiar(datos):
    df = pd.DataFrame(datos)
    df = df[COLUMNAS].copy()
    for columna in NUMERICAS:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")
    df = df.dropna(subset=NUMERICAS)
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=NUMERICAS)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def consultar_coingecko(token):
    respuesta = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets",
        headers={"x-cg-demo-api-key": token},
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": 1,
        },
        timeout=30,
    )
    if respuesta.status_code == 401:
        raise PermissionError("La API Key no fue aceptada (401).")
    if respuesta.status_code == 429:
        raise PermissionError("Límite de peticiones excedido (429).")
    respuesta.raise_for_status()
    return limpiar(respuesta.json())


def cargar_csv():
    ruta = Path(__file__).with_name("datos_limpios.csv")
    df = pd.read_csv(ruta)
    df = df[COLUMNAS].copy()
    for columna in NUMERICAS:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")
    return df.dropna(subset=NUMERICAS)


# ─── Datos ─────────────────────────────────────────────────────────────
TOKEN = leer_token()
origen = "Archivo local datos_limpios.csv (24/11/2026)"

with st.sidebar:
    st.header("Qué consultar")
    st.caption("CoinGecko · /coins/markets · USD · top 250 por capitalización")
    if st.button("Actualizar desde CoinGecko"):
        st.cache_data.clear()
    if TOKEN:
        st.success("Token detectado (en secretos). Se consulta la API en vivo.")
    else:
        st.info("Sin token: se usan los datos guardados en datos_limpios.csv. "
                "Para consultar en vivo, poné el token en .streamlit/secrets.toml "
                "como coingecko_token.")

if TOKEN:
    with st.spinner("Consultando CoinGecko..."):
        try:
            df = consultar_coingecko(TOKEN)
            origen = f"CoinGecko en vivo · consultado el {datetime.now():%d/%m/%Y %H:%M}"
        except Exception as e:
            st.warning(f"No se pudo consultar la API ({e}). Se usan los datos guardados.")
            df = cargar_csv()
else:
    df = cargar_csv()

if df.empty:
    st.error("No hay datos para mostrar.")
    st.stop()

# ─── Encabezado e indicadores ──────────────────────────────────────────
st.title("Tablero CoinGecko: top 250 por capitalización")
st.caption(f"Fuente: CoinGecko · {origen} · Precios en USD")

mayor_cap = df.loc[df["market_cap"].idxmax()]
mayor_aumento = df.loc[df["price_change_percentage_24h"].idxmax()]
mayor_baja = df.loc[df["price_change_percentage_24h"].idxmin()]
correlacion = df["market_cap"].corr(df["total_volume"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Activos analizados", len(df))
c2.metric("Precio mediano", f"${df['current_price'].median():,.6f} USD")
c3.metric("Mayor capitalización", mayor_cap["name"],
          f"${mayor_cap['market_cap']:,.0f} USD")
c4.metric("Correlación cap. / volumen", f"{correlacion:.3f}")

st.divider()

# ─── Gráfica 1: distribución de precios ────────────────────────────────
izq, der = st.columns(2)
with izq:
    st.subheader("1. Los precios presentan una amplia diferencia entre activos")
    precios = df.loc[df["current_price"] > 0, "current_price"]
    fig, ax = plt.subplots(figsize=(6, 3.4))
    bins = np.logspace(np.log10(precios.min()), np.log10(precios.max()), 30)
    ax.hist(precios, bins=bins, color=AZUL, edgecolor="white")
    ax.set_xscale("log")
    ax.set_xlabel("Precio en USD (escala logarítmica)")
    ax.set_ylabel("Número de activos")
    ax.grid(axis="y", alpha=0.25)
    st.pyplot(fig)

with der:
    st.subheader("2. Diez activos con mayor capitalización de mercado")
    top10 = df.nlargest(10, "market_cap").sort_values("market_cap")
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.barh(top10["name"], top10["market_cap"] / 1_000_000_000, color=AZUL)
    ax.set_xlabel("Capitalización de mercado (miles de millones de USD)")
    ax.set_ylabel("Activo")
    ax.grid(axis="x", alpha=0.25)
    st.pyplot(fig)

abajo_izq, abajo_der = st.columns(2)
with abajo_izq:
    st.subheader("3. Relación entre capitalización y volumen negociado")
    relacion = df[(df["market_cap"] > 0) & (df["total_volume"] > 0)]
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.scatter(relacion["market_cap"], relacion["total_volume"],
               color=AZUL_CLARO, edgecolor=AZUL, alpha=0.7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Capitalización de mercado (USD, escala logarítmica)")
    ax.set_ylabel("Volumen negociado en 24 horas (USD, escala logarítmica)")
    ax.grid(alpha=0.25)
    st.pyplot(fig)

with abajo_der:
    st.subheader("4. Activos con mayores variaciones porcentuales en 24 horas")
    cambios = df.copy()
    cambios["magnitud_cambio"] = cambios["price_change_percentage_24h"].abs()
    top_cambios = cambios.nlargest(15, "magnitud_cambio").sort_values(
        "price_change_percentage_24h")
    colores = [VERDE if v >= 0 else NARANJA
               for v in top_cambios["price_change_percentage_24h"]]
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.barh(top_cambios["name"], top_cambios["price_change_percentage_24h"],
            color=colores)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Cambio porcentual (%)")
    ax.set_ylabel("Activo")
    ax.legend(handles=[Patch(color=VERDE, label="Aumento"),
                       Patch(color=NARANJA, label="Disminución")])
    ax.grid(axis="x", alpha=0.25)
    st.pyplot(fig)

# ─── Resultados y datos ────────────────────────────────────────────────
st.divider()
st.subheader("Resultados para el reporte")
st.write(f"Total de registros analizados: {len(df)}")
st.write(f"Mayor aumento en 24 horas: {mayor_aumento['name']} "
         f"({mayor_aumento['price_change_percentage_24h']:.2f}%)")
st.write(f"Mayor disminución en 24 horas: {mayor_baja['name']} "
         f"({mayor_baja['price_change_percentage_24h']:.2f}%)")
st.write(f"Correlación entre capitalización y volumen: {correlacion:.3f}")

with st.expander("Ver y descargar los datos"):
    texto = st.text_input("Buscar por nombre", "")
    vista = df[df["name"].str.contains(texto, case=False, na=False)] if texto else df
    st.dataframe(vista)
    st.download_button(
        "Descargar CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="datos_limpios.csv",
        mime="text/csv",
    )
