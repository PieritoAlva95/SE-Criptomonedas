# Esta aplicación es sólo para fines educativos. La información obtenida no es un consejo financiero. Utilícela bajo su propia responsabilidad.
import streamlit as st
from PIL import Image
import pandas as pd
import base64
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
import json
import time
#---------------------------------#
# Diseño de la página
# La página se expande a todo lo ancho
st.set_page_config(layout="wide")
#---------------------------------#
# Título

image = Image.open('logo.jpg')

st.image(image, width=500)

st.title('Aplicación de precios de criptomonedas')
st.markdown("""
¡Esta aplicación recupera los precios de las 100 principales criptomonedas del **CoinMarketCap**!
""")
#---------------------------------#
# Acerca de
expander_bar = st.beta_expander("Acerca de")
expander_bar.markdown("""
* **Bibliotecas de Python:** base64, pandas, streamlit, numpy, matplotlib, seaborn, BeautifulSoup, requests, json, time
* **Fuente de datos:** [CoinMarketCap](http://coinmarketcap.com).
* **Crédito:** Web scraper adapted from the Medium article *[Web Scraping Crypto Prices With Python](https://towardsdatascience.com/web-scraping-crypto-prices-with-python-41072ea5b5bf)* written by [Bryan Feng](https://medium.com/@bryanf).
""")


#---------------------------------#
# Diseño de la página (continuación)
# Dividir la página en 3 columnas (col1 = barra lateral, col2 y col3 = contenido de la página)
col1 = st.sidebar
col2, col3 = st.beta_columns((2, 1))

#---------------------------------#
# Barra lateral + panel principal
col1.header('Opciones de entrada')

# Barra lateral - Unidad de precio de la moneda
currency_price_unit = col1.selectbox(
    'Seleccione la moneda para el precio', ('USD', 'BTC', 'ETH'))

# Raspado web de los datos de CoinMarketCap


@st.cache
def load_data():
    cmc = requests.get('https://coinmarketcap.com')
    soup = BeautifulSoup(cmc.content, 'html.parser')

    data = soup.find('script', id='__NEXT_DATA__', type='application/json')
    coins = {}
    coin_data = json.loads(data.contents[0])
    listings = coin_data['props']['initialState']['cryptocurrency']['listingLatest']['data']
    for i in listings:
        coins[str(i['id'])] = i['slug']

    coin_name = []
    coin_symbol = []
    market_cap = []
    percent_change_1h = []
    percent_change_24h = []
    percent_change_7d = []
    price = []
    volume_24h = []

    for i in listings:
        coin_name.append(i['slug'])
        coin_symbol.append(i['symbol'])
        price.append(i['quote'][currency_price_unit]['price'])
        percent_change_1h.append(
            i['quote'][currency_price_unit]['percentChange1h'])
        percent_change_24h.append(
            i['quote'][currency_price_unit]['percentChange24h'])
        percent_change_7d.append(
            i['quote'][currency_price_unit]['percentChange7d'])
        market_cap.append(i['quote'][currency_price_unit]['marketCap'])
        volume_24h.append(i['quote'][currency_price_unit]['volume24h'])

    df = pd.DataFrame(columns=['nombre', 'símbolo_moneda', 'capitalización_de_mercado', 'cambio_porcentual_1h',
                      'cambio_porcentual_24h', 'cambio_porcentual_7d', 'precio', 'volumen_24h'])
    df['nombre'] = coin_name
    df['símbolo_moneda'] = coin_symbol
    df['precio'] = price
    df['cambio_porcentual_1h'] = percent_change_1h
    df['cambio_porcentual_24h'] = percent_change_24h
    df['cambio_porcentual_7d'] = percent_change_7d
    df['capitalización_de_mercado'] = market_cap
    df['volumen_24h'] = volume_24h
    return df


df = load_data()

# Barra lateral - Selecciones de criptodivisas
sorted_coin = sorted(df['símbolo_moneda'])
selected_coin = col1.multiselect('Criptomoneda', sorted_coin, sorted_coin)

# Filtrado de datos
df_selected_coin = df[(df['símbolo_moneda'].isin(selected_coin))]

# Barra lateral - Número de monedas a mostrar
num_coin = col1.slider('Mostrar Top N Coins', 1, 100, 100)
df_coins = df_selected_coin[:num_coin]

# Barra lateral - Porcentaje de cambio en el tiempo
percent_timeframe = col1.selectbox('Porcentaje de cambio marco temporal',
                                   ['7d', '24h', '1h'])
percent_dict = {"7d": 'cambio_porcentual_7d',
                "24h": 'cambio_porcentual_24h', "1h": 'cambio_porcentual_1h'}
selected_percent_timeframe = percent_dict[percent_timeframe]

# Sidebar - Sorting values
sort_values = col1.selectbox('¿Ordenar los valores?', ['Si', 'No'])

col2.subheader('Datos de precios de criptomonedas seleccionadas')
col2.write('Dimensión de los datos: ' + str(df_selected_coin.shape[0]) + ' filas y ' + str(
    df_selected_coin.shape[1]) + ' columnas.')

col2.dataframe(df_coins)

# Descargar datos CSV
# https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806


def filedownload(df):
    csv = df.to_csv(index=False)
    # Conversiones de strings <-> bytes
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="crypto.csv">Descargar archivo CSV</a>'
    return href


col2.markdown(filedownload(df_selected_coin), unsafe_allow_html=True)

#---------------------------------#
# Preparación de los datos para el diagrama de barras de la variación del precio en %
col2.subheader('Tabla de % de variación de precios')
df_change = pd.concat([df_coins.símbolo_moneda, df_coins.cambio_porcentual_1h,
                      df_coins.cambio_porcentual_24h, df_coins.cambio_porcentual_7d], axis=1)
df_change = df_change.set_index('símbolo_moneda')
df_change['cambio_positivo_porcentual_1h'] = df_change['cambio_porcentual_1h'] > 0
df_change['cambio_positivo_porcentual_24h'] = df_change['cambio_porcentual_24h'] > 0
df_change['cambio_positivo_porcentual_7d'] = df_change['cambio_porcentual_7d'] > 0
col2.dataframe(df_change)

# Creación condicional de un gráfico de barras (marco temporal)
col3.subheader('Gráfico de barras de la variación del precio en %')

if percent_timeframe == '7d':
    if sort_values == 'Si':
        df_change = df_change.sort_values(by=['cambio_porcentual_7d'])
    col3.write('*Periodo de 7 días*')
    plt.figure(figsize=(5, 25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['cambio_porcentual_7d'].plot(
        kind='barh', color=df_change.cambio_positivo_porcentual_7d.map({True: 'g', False: 'r'}))
    col3.pyplot(plt)
elif percent_timeframe == '24h':
    if sort_values == 'Si':
        df_change = df_change.sort_values(by=['cambio_porcentual_24h'])
    col3.write('*Periodo de 24 horas*')
    plt.figure(figsize=(5, 25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['cambio_porcentual_24h'].plot(
        kind='barh', color=df_change.cambio_positivo_porcentual_24h.map({True: 'g', False: 'r'}))
    col3.pyplot(plt)
else:
    if sort_values == 'Si':
        df_change = df_change.sort_values(by=['cambio_porcentual_1h'])
    col3.write('*Periodo de 1 hora*')
    plt.figure(figsize=(5, 25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['cambio_porcentual_1h'].plot(
        kind='barh', color=df_change.cambio_positivo_porcentual_1h.map({True: 'g', False: 'r'}))
    col3.pyplot(plt)
