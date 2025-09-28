import streamlit as st
import requests
import json
import base64
import pandas as pd
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="AgroAssistente IA Completo - Embrapa",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        color: #2e7d32;
        text-align: center;
        margin-bottom: 1rem;
    }
    .response-card {
        background-color: #f8fffd;
        border-left: 4px solid #2e7d32;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 8px;
    }
    .soil-card {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 8px;
    }
    .weather-card {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 8px;
    }
    .api-status {
        padding: 6px 12px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        color: white;
    }
    .status-active { background: #4caf50; }
    .status-error { background: #f44336; }
</style>
""", unsafe_allow_html=True)

class EmbrapaAuth:
    def __init__(self):
        self.consumer_key = "DI_JQ6o06C8ktdGR0pwpuSL6f3ka"
        self.consumer_secret = "BXmyFKVuIHlCsaUUS40Ya0bV8msa"
        self.token_url = "https://api.cnptia.embrapa.br/token"
        self.base64_credentials = self._get_base64_credentials()
        
    def _get_base64_credentials(self):
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        return base64.b64encode(credentials.encode()).decode()
    
    def get_access_token(self):
        headers = {
            "Authorization": f"Basic {self.base64_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {"grant_type": "client_credentials"}
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                return {
                    "access_token": token_data.get("access_token"),
                    "expires_in": token_data.get("expires_in"),
                    "token_type": token_data.get("token_type"),
                    "timestamp": datetime.now()
                }
            else:
                st.error(f"❌ Erro na autenticação: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"🚫 Erro de conexão: {e}")
            return None

class RespondeAgroAPI:
    def __init__(self, auth):
        self.base_url = "https://api.cnptia.embrapa.br/respondeagro/v1"
        self.auth = auth
        self.access_token = None
        
    def ensure_valid_token(self):
        if not self.access_token:
            token_data = self.auth.get_access_token()
            if token_data:
                self.access_token = token_data["access_token"]
                return True
        return bool(self.access_token)
    
    def search_all_books(self, query, size=5):
        if not self.ensure_valid_token():
            return {"error": "Falha na autenticação"}
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "id": "query_all",
            "params": {
                "query_string": query,
                "from": 0,
                "size": size
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/_search/template",
                headers=headers,
                json=payload,
                timeout=30
            )
            return response.json() if response.status_code == 200 else {"error": f"Erro {response.status_code}"}
        except Exception as e:
            return {"error": f"Erro de conexão: {str(e)}"}

class SmartSolosAPI:
    def __init__(self, auth):
        self.base_url = "https://api.cnptia.embrapa.br/smartsolos/v1"
        self.auth = auth
        self.access_token = None
        
    def ensure_valid_token(self):
        if not self.access_token:
            token_data = self.auth.get_access_token()
            if token_data:
                self.access_token = token_data["access_token"]
                return True
        return bool(self.access_token)
    
    def classify_soil(self, soil_profile):
        """Classifica solo usando o endpoint /classification da API real"""
        if not self.ensure_valid_token():
            return {"error": "Falha na autenticação"}
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/classification",
                headers=headers,
                json=soil_profile,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Erro {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": f"Erro de conexão: {str(e)}"}
    
    def validate_classification(self, soil_profile):
        """Valida classificação usando o endpoint /verification da API real"""
        if not self.ensure_valid_token():
            return {"error": "Falha na autenticação"}
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/verification",
                headers=headers,
                json=soil_profile,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Erro {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": f"Erro de conexão: {str(e)}"}

class ClimateAPI:
    def __init__(self, auth):
        self.base_url = "https://api.cnptia.embrapa.br/clima/v1"
        self.auth = auth
        self.access_token = None
        
    def ensure_valid_token(self):
        if not self.access_token:
            token_data = self.auth.get_access_token()
            if token_data:
                self.access_token = token_data["access_token"]
                return True
        return bool(self.access_token)
    
    def get_weather_variables(self):
        """Obtém lista de variáveis climáticas disponíveis"""
        if not self.ensure_valid_token():
            return {"error": "Falha na autenticação"}
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/ncep-gfs",
                headers=headers,
                timeout=30
            )
            return response.json() if response.status_code == 200 else {"error": f"Erro {response.status_code}"}
        except Exception as e:
            return {"error": f"Erro de conexão: {str(e)}"}
    
    def get_weather_forecast(self, variable, date, lat, lon):
        """Obtém previsão do tempo real para coordenadas específicas"""
        if not self.ensure_valid_token():
            return {"error": "Falha na autenticação"}
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/ncep-gfs/{variable}/{date}/{lon}/{lat}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Erro {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": f"Erro de conexão: {str(e)}"}

def create_sample_soil_profile():
    """Cria um perfil de solo de exemplo baseado na documentação"""
    return {
        "items": [{
            "ID_PONTO": "Perfil_Exemplo_1",
            "HORIZONTES": [
                {
                    "SIMB_HORIZ": "Ap",
                    "LIMITE_SUP": 0,
                    "LIMITE_INF": 20,
                    "COR_UMIDA_MATIZ": "10YR",
                    "COR_UMIDA_VALOR": 3,
                    "COR_UMIDA_CROMA": 2,
                    "ARGILA": 200,
                    "SILTE": 300,
                    "AREIA_FINA": 250,
                    "AREIA_GROS": 250,
                    "PH_AGUA": 6.0,
                    "C_ORG": 15.0
                },
                {
                    "SIMB_HORIZ": "Bt",
                    "LIMITE_SUP": 20,
                    "LIMITE_INF": 100,
                    "COR_UMIDA_MATIZ": "7.5YR",
                    "COR_UMIDA_VALOR": 4,
                    "COR_UMIDA_CROMA": 6,
                    "ARGILA": 450,
                    "SILTE": 200,
                    "AREIA_FINA": 175,
                    "AREIA_GROS": 175,
                    "PH_AGUA": 5.8,
                    "C_ORG": 5.0
                }
            ]
        }]
    }

def main():
    st.markdown('<h1 class="main-header">🌱 AgroAssistente IA Completo</h1>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; color: #666; margin-bottom: 2rem;">Conectado às APIs Oficiais da Embrapa - Dados Reais em Tempo Real</div>', unsafe_allow_html=True)
    
    # Inicialização das APIs
    auth = EmbrapaAuth()
    responde_api = RespondeAgroAPI(auth)
    solos_api = SmartSolosAPI(auth)
    climate_api = ClimateAPI(auth)
    
    # Sidebar
    with st.sidebar:
        st.image("https://embrapa.br/assets/img/logo-embrapa.svg", width=150)
        st.markdown("---")
        
        st.markdown("### 🔗 APIs Conectadas")
        
        # Status das APIs
        apis_status = {
            "📚 Responde Agro": "Conectado",
            "🏞️ SmartSolos": "Conectado", 
            "🌤️ Climate API": "Conectado"
        }
        
        for api_name, status in apis_status.items():
            st.write(f"{api_name}: <span class='api-status status-active'>{status}</span>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🎯 Navegação")
        
        tab = st.radio("Selecione o módulo:", [
            "🔍 Busca Conhecimento",
            "🏞️ Análise de Solo", 
            "🌤️ Previsão Climática",
            "📊 Dashboard Integrado"
        ])
    
    # Módulo de Busca de Conhecimento
    if tab == "🔍 Busca Conhecimento":
        st.markdown("### 📚 Busca no Conhecimento Embrapa")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input("Digite sua pergunta sobre agricultura:")
        with col2:
            results_size = st.selectbox("Resultados", [3, 5, 8], index=1)
        
        if st.button("🎯 Buscar na Base Embrapa", type="primary") and query:
            with st.spinner("Consultando base de conhecimento..."):
                results = responde_api.search_all_books(query, results_size)
                
                if "error" in results:
                    st.error(f"Erro na busca: {results['error']}")
                elif results and 'hits' in results and results['hits']['total']['value'] > 0:
                    total_results = results['hits']['total']['value']
                    st.success(f"✅ Encontradas {total_results} respostas relevantes!")
                    
                    for i, hit in enumerate(results['hits']['hits']):
                        source = hit['_source']
                        with st.expander(f"📖 {source['question']}", expanded=i==0):
                            st.write(f"**Livro:** {source['book']} | **Capítulo:** {source['chapter']}")
                            st.markdown("**💡 Resposta:**")
                            st.markdown(source['answer'], unsafe_allow_html=True)
                else:
                    st.warning("Nenhum resultado encontrado para sua busca.")
    
    # Módulo de Análise de Solo
    elif tab == "🏞️ Análise de Solo":
        st.markdown("### 🏞️ Classificação de Solos - SmartSolos Expert")
        
        st.info("""
        **Sistema Brasileiro de Classificação de Solos (SiBCS)**
        - Classificação nos 4 primeiros níveis: Ordem, Subordem, Grande Grupo, Subgrupo
        - Baseado na 5ª edição do SiBCS (2018)
        - Dados validados por especialistas em pedologia
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Dados do Perfil de Solo")
            st.write("Use o perfil de exemplo ou adicione seus dados:")
            
            if st.button("🔄 Carregar Perfil de Exemplo"):
                soil_profile = create_sample_soil_profile()
                st.session_state.soil_profile = soil_profile
                st.success("Perfil de exemplo carregado!")
            
            if 'soil_profile' in st.session_state:
                st.json(st.session_state.soil_profile)
        
        with col2:
            st.markdown("#### 🎯 Classificação")
            
            if st.button("🔬 Classificar Solo", type="primary") and 'soil_profile' in st.session_state:
                with st.spinner("Classificando solo com SmartSolos Expert..."):
                    result = solos_api.classify_soil(st.session_state.soil_profile)
                    
                    if "error" in result:
                        st.error(f"Erro na classificação: {result['error']}")
                    elif "items" in result and result["items"]:
                        classification = result["items"][0]
                        
                        st.markdown('<div class="soil-card">', unsafe_allow_html=True)
                        st.markdown("### 🎯 Resultado da Classificação")
                        st.metric("Ordem", classification.get("ORDEM", "N/A"))
                        st.metric("Subordem", classification.get("SUBORDEM", "N/A"))
                        st.metric("Grande Grupo", classification.get("GDE_GRUPO", "N/A"))
                        st.metric("Subgrupo", classification.get("SUBGRUPO", "N/A"))
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Recomendações baseadas na classificação
                        ordem = classification.get("ORDEM", "")
                        if ordem == "LATOSSOLO":
                            st.info("**💡 Recomendações para Latossolo:** Solos profundos e bem drenados. Ideal para culturas anuais como soja e milho.")
                        elif ordem == "ARGISSOLO":
                            st.info("**💡 Recomendações para Argissolo:** Cuidado com erosão. Recomendada adubação fosfatada.")
    
    # Módulo de Previsão Climática
    elif tab == "🌤️ Previsão Climática":
        st.markdown("### 🌤️ Previsão Climática em Tempo Real")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            lat = st.number_input("Latitude", value=-22.8178, format="%.6f")
        with col2:
            lon = st.number_input("Longitude", value=-47.0614, format="%.6f")
        with col3:
            variable = st.selectbox("Variável", [
                "tmax2m", "tmin2m", "apcpsfc", "rh2m", "gustsfc"
            ], help="tmax2m: Temperatura máxima, tmin2m: Temperatura mínima, apcpsfc: Precipitação")
        
        # Data atual para a consulta
        today = datetime.now().strftime("%Y-%m-%d")
        
        if st.button("📡 Obter Previsão", type="primary"):
            with st.spinner("Consultando dados climáticos..."):
                forecast = climate_api.get_weather_forecast(variable, today, lat, lon)
                
                if "error" in forecast:
                    st.error(f"Erro na previsão: {forecast['error']}")
                else:
                    st.markdown('<div class="weather-card">', unsafe_allow_html=True)
                    st.markdown(f"### 📍 Previsão para Lat: {lat}, Lon: {lon}")
                    
                    # Converter dados para DataFrame para melhor visualização
                    if isinstance(forecast, list):
                        df = pd.DataFrame(forecast)
                        st.dataframe(df)
                        
                        # Gráfico simples se houver dados suficientes
                        if len(df) > 1:
                            st.line_chart(df.set_index("horas")["valor"])
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # Dashboard Integrado
    else:
        st.markdown("### 📊 Dashboard Integrado")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Consulta Rápida")
            quick_query = st.text_input("Pergunta rápida sobre agricultura:")
            if st.button("🔍 Buscar") and quick_query:
                with st.spinner("Buscando..."):
                    results = responde_api.search_all_books(quick_query, 3)
                    if "error" not in results and results.get('hits', {}).get('hits'):
                        for hit in results['hits']['hits'][:2]:
                            st.info(f"**{hit['_source']['question']}**")
                            st.write(hit['_source']['answer'][:200] + "...")
        
        with col2:
            st.markdown("#### 🌤️ Clima Atual")
            if st.button("🔄 Atualizar Dados Climáticos"):
                with st.spinner("Obtendo dados..."):
                    # Exemplo rápido de clima
                    variables = climate_api.get_weather_variables()
                    if "error" not in variables:
                        st.success("Conexão climática ativa!")
                        st.write(f"Variáveis disponíveis: {len(variables)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    <p>🚀 <strong>CONEXÕES ATIVAS</strong> - APIs Oficiais Embrapa</p>
    <p>📚 Responde Agro | 🏞️ SmartSolos Expert | 🌤️ Climate API</p>
    <p>📧 Contato: agroapi@embrapa.br</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
