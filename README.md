# Análise Financeira de Criptomoedas - BTC-USD

Este é um aplicativo de análise de dados financeiros focado na criptomoeda Bitcoin (BTC) contra o dólar (USD), desenvolvido com Streamlit. Ele permite visualizar e analisar diversos indicadores financeiros, gráficos e realizar otimizações de portfólio. O app utiliza dados históricos obtidos da API do Yahoo Finance e oferece visualizações interativas de métricas como preço de fechamento, médias móveis, retorno diário, RSI e mais.

## Funcionalidades

- **Evolução do Preço do BTC-USD**: Visualize a evolução histórica do preço de fechamento do Bitcoin.
- **Médias Móveis**: Compare o preço de fechamento com as médias móveis de 20 e 50 dias.
- **Retorno Diário e Acumulado**: Calcule os retornos diários e o retorno acumulado do BTC.
- **Indicadores Técnicos**: Análise do preço do BTC com a média móvel exponencial (EMA) de 20 dias e o Índice de Força Relativa (RSI).
- **Distribuição de Retornos**: Visualize a distribuição dos retornos diários do BTC.
- **Correlação entre Criptomoedas**: Veja a correlação entre várias criptomoedas como BTC, ETH, SOL e SHIB.
- **Otimização de Portfólio**: Realize simulações de portfólio com criptomoedas e visualize a fronteira eficiente, destacando o portfólio ótimo com o maior Sharpe Ratio.

## Tecnologias Utilizadas

- **Streamlit**: Para a criação da interface interativa.
- **Pandas**: Para manipulação e análise dos dados financeiros.
- **Matplotlib e Seaborn**: Para visualizações gráficas.
- **yFinance**: Para download de dados históricos de criptomoedas.

## Como Rodar o App Localmente

1. Clone este repositório:
    ```bash
    git clone https://github.com/Jon-dev67/BTC-USD_Dashboard-.git
    ```

2. Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

3. Execute o app:
    ```bash
    streamlit run app.py
    ```

## Como Contribuir

1. Faça um fork deste repositório.
2. Crie uma branch com a sua funcionalidade (`git checkout -b feature/nome-da-sua-funcionalidade`).
3. Faça suas mudanças e commit (`git commit -am 'Adicionando nova funcionalidade'`).
4. Envie para o repositório remoto (`git push origin feature/nome-da-sua-funcionalidade`).
5. Abra um pull request.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.
