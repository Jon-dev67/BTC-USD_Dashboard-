import streamlit as st
import pandas as pd
import yfinance as yf
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from statsmodels.tsa.arima.model import ARIMA
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler

st.title("Análise Financeira de Criptomoedas")

# Baixar dados do BTC
st.subheader("Cotação do BTC-USD")
df = yf.download("BTC-USD", start="2023-01-20")
df.dropna(inplace=True)

# Exibir os dados básicos
st.write(df.describe())

# Plotando o preço de fechamento
st.subheader("Evolução do Preço do BTC-USD")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df["Close"], label="Preço de Fechamento", color="blue")
ax.set_xlabel("Data")
ax.set_ylabel("Preço ($)")
ax.set_title("Evolução do Preço do BTC-USD")
ax.legend()
ax.grid()
st.pyplot(fig)

# Criando médias móveis de 20 e 50 dias
df["MM_20"] = df["Close"].rolling(window=20).mean()
df["MM_50"] = df["Close"].rolling(window=50).mean()

st.subheader("Médias Móveis do BTC-USD")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df["Close"], label="Preço de Fechamento", color="blue")
ax.plot(df["MM_20"], label="Média Móvel 20 dias", color="red", linestyle="dashed")
ax.plot(df["MM_50"], label="Média Móvel 50 dias", color="green", linestyle="dashed")
ax.legend()
ax.grid()
st.pyplot(fig)

# Calcular Retorno Diário (%)
df["Retorno Diário"] = df["Close"].pct_change()

# Calcular Retorno Acumulado (%)
df["Retorno Acumulado"] = (1 + df["Retorno Diário"]).cumprod()

st.subheader("Retorno Acumulado do BTC-USD")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df["Retorno Acumulado"], label="Retorno Acumulado", color="purple")
ax.set_title("Retorno Acumulado da BTC-USD")
ax.set_xlabel("Data")
ax.set_ylabel("Retorno (%)")
ax.legend()
ax.grid()
st.pyplot(fig)

# Calcular Média Móvel Exponencial (EMA)
df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

# Calcular RSI (Índice de Força Relativa)
window = 14
delta = df["Close"].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
rs = gain / loss
df["RSI"] = 100 - (100 / (1 + rs))

# Plotar EMA e RSI
st.subheader("Análise Técnica: EMA e RSI")

fig, ax = plt.subplots(2, 1, figsize=(10, 8))

# Gráfico de Preço + EMA
ax[0].plot(df["Close"], label="Preço de Fechamento", color="blue")
ax[0].plot(df["EMA_20"], label="EMA 20 dias", color="orange", linestyle="dashed")
ax[0].set_title("Preço e EMA do BTC-USD")
ax[0].legend()
ax[0].grid()

# Gráfico do RSI
ax[1].plot(df["RSI"], label="RSI", color="green")
ax[1].axhline(70, linestyle="dashed", color="red")  # Nível de sobrecompra
ax[1].axhline(30, linestyle="dashed", color="blue") # Nível de sobrevenda
ax[1].set_title("RSI do BTC-USD")
ax[1].legend()
ax[1].grid()

plt.tight_layout()
st.pyplot(fig)




# Baixar dados do BTC
st.title("Análise Preditiva de Criptomoedas")
st.subheader("Previsão do Preço do BTC-USD")
df = yf.download("BTC-USD", start="2023-01-20")
df.dropna(inplace=True)

# Criar variáveis para modelos
df["MM_20"] = df["Close"].rolling(window=20).mean()
df["MM_50"] = df["Close"].rolling(window=50).mean()
df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
df["Retorno Diário"] = df["Close"].pct_change()
df.dropna(inplace=True)

# Criar seleção de modelo
modelo_selecionado = st.selectbox("Escolha um modelo de previsão:", ["Regressão Linear", "LSTM", "ARIMA"])

# Regressão Linear
if modelo_selecionado == "Regressão Linear":
    df["Target"] = df["Close"].shift(-1)
    df.dropna(inplace=True)
    X = df[["Close", "MM_20", "MM_50", "EMA_20", "Retorno Diário"]]
    y = df["Target"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    modelo = LinearRegression()
    modelo.fit(X_train, y_train)
    previsao = modelo.predict([X.iloc[-1]])[0]
    st.write(f"Previsão de fechamento com Regressão Linear: {previsao:.2f}")

# Modelo LSTM
elif modelo_selecionado == "LSTM":
    scaler = MinMaxScaler()
    df["Close_Scaled"] = scaler.fit_transform(df[["Close"]])

    def create_sequences(data, window_size=10):
        X, y = [], []
        for i in range(len(data) - window_size):
            X.append(data[i:i+window_size])
            y.append(data[i+window_size])
        return np.array(X), np.array(y)

    window_size = 10
    X, y = create_sequences(df["Close_Scaled"].values, window_size)
    X_train, X_test = X[:-100], X[-100:]
    y_train, y_test = y[:-100], y[-100:]

    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(window_size, 1)),
        Dropout(0.2),
        LSTM(50),
        Dense(1)
    ])

    model.compile(optimizer="adam", loss="mse")
    model.fit(X_train, y_train, epochs=20, batch_size=16, verbose=0)

    proxima_previsao = model.predict(np.expand_dims(X[-1], axis=0))
    previsao_real = scaler.inverse_transform(proxima_previsao.reshape(-1, 1))[0][0]
    st.write(f"Previsão de fechamento com LSTM: {previsao_real:.2f}")

# Modelo ARIMA
elif modelo_selecionado == "ARIMA":
    modelo_arima = ARIMA(df["Close"], order=(5,1,0))
    modelo_treinado = modelo_arima.fit()
    previsao = modelo_treinado.forecast(steps=1)[0]
    st.write(f"Previsão de fechamento com ARIMA: {previsao:.2f}")



# Histograma dos Retornos Diários
st.subheader("Distribuição dos Retornos Diários")
fig, ax = plt.subplots(figsize=(10,5))
sns.histplot(df["Retorno Diário"].dropna(), bins=50, kde=True, color="purple", ax=ax)
ax.set_title("Distribuição dos Retornos Diários da BTC-USD")
ax.set_xlabel("Retorno Diário")
ax.set_ylabel("Frequência")
ax.grid()
st.pyplot(fig)

# Analisando múltiplas criptomoedas
st.subheader("Correlação entre Criptomoedas")
cripto = ["BTC-USD", "ETH-USD", "SOL-USD", "SHIB-USD"]
df_crypto = yf.download(cripto, start="2023-01-20")["Close"]
correlacao = df_crypto.pct_change().corr()

fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(correlacao, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5, ax=ax)
st.pyplot(fig)

# Lista de criptomoedas no portfólio
cripto = ["BTC-USD", "ETH-USD", "SHIB-USD", "SOL-USD"]

# Baixar dados de todas as criptomoedas
df = yf.download(cripto, start="2023-01-20")

# Calcular retornos diários
retornos = df["Close"].pct_change().dropna()  # Utilizando apenas o 'Close' para calcular os retornos

# Definir pesos do portfólio (exemplo: 25% para cada cripto)
pesos = np.array([0.25, 0.25, 0.25, 0.25])

# Calcular retorno esperado do portfólio
retorno_esperado = np.sum(retornos.mean() * pesos) * 252  # 252 dias úteis no ano

# Calcular risco do portfólio (desvio padrão anualizado)
cov_matriz = retornos.cov() * 252
risco_portfolio = np.sqrt(np.dot(pesos.T, np.dot(cov_matriz, pesos)))

# Exibir resultados
st.write(f"Retorno Esperado do Portfólio: {retorno_esperado:.2%}")
st.write(f"Risco (Volatilidade) do Portfólio: {risco_portfolio:.2%}")

# Simulação de múltiplos portfólios
np.random.seed(42)  # Garantir resultados consistentes
n_portfolios = 10000
resultados = np.zeros((3, n_portfolios))

for i in range(n_portfolios):
    pesos = np.random.random(len(cripto))  # Gerar pesos aleatórios
    pesos /= np.sum(pesos)  # Normalizar para que a soma seja 1

    # Calcular retorno e risco do portfólio
    retorno_portfolio = np.sum(retornos.mean() * pesos) * 252  # 252 dias úteis no ano
    cov_matriz = retornos.cov() * 252
    risco_portfolio = np.sqrt(np.dot(pesos.T, np.dot(cov_matriz, pesos)))

    # Armazenar resultados
    resultados[0, i] = retorno_portfolio
    resultados[1, i] = risco_portfolio
    resultados[2, i] = resultados[0, i] / resultados[1, i]  # Sharpe ratio

# Converter resultados em DataFrame
portfolios = pd.DataFrame(resultados.T, columns=["Retorno", "Risco", "Sharpe"])

# Melhor portfólio (máximo Sharpe ratio)
melhor_portfolio = portfolios.loc[portfolios["Sharpe"].idxmax()]

# Plotar os portfólios simulados
st.subheader("Otimização de Portfólio: Fronteira Eficiente")
fig, ax = plt.subplots(figsize=(10,6))
ax.scatter(portfolios["Risco"], portfolios["Retorno"], c=portfolios["Sharpe"], cmap="viridis", marker="o")
ax.set_title("Otimização de Portfólio: Fronteira Eficiente")
ax.set_xlabel("Risco (Volatilidade)")
ax.set_ylabel("Retorno Esperado")
fig.colorbar(ax.collections[0], ax=ax, label="Sharpe Ratio")

# Destacar o portfólio ótimo (máximo Sharpe)
ax.scatter(melhor_portfolio["Risco"], melhor_portfolio["Retorno"], color="red", marker="*", s=200, label="Melhor Portfólio")
ax.legend()
ax.grid()
st.pyplot(fig)

# Exibir o melhor portfólio
st.write("Melhor Portfólio (Máximo Sharpe Ratio):")
st.write(f"Retorno: {melhor_portfolio['Retorno']:.2%}")
st.write(f"Risco: {melhor_portfolio['Risco']:.2%}")
st.write(f"Sharpe Ratio: {melhor_portfolio['Sharpe']:.2f}")

