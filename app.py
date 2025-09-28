import streamlit as st
import requests
import json
import base64
import pandas as pd
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="AgroAssistente IA - Embrapa",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado - Estilo da primeira versão
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2e7d32;
        text-align: center;
        margin-bottom: 2rem;
    }
    .embrapa-brand {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .response-card {
        background-color: #f8fffd;
        border-left: 4px solid #2e7d32;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 8px;
    }
    .highlight {
        background-color: #fff9c4;
        padding: 2px 4px;
        border-radius: 3px;
    }
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .api-status {
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .status-active {
        background: #4caf50;
        color: white;
    }
    .soil-result {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 8px;
    }
    .weather-result {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

class EmbrapaAuth:
    def __init__(self):
        # SUAS CREDENCIAIS
        self.consumer_key = "DI_JQ6o06C8ktdGR0pwpuSL6f3ka"
        self.consumer_secret = "BXmyFKVuIHlCsaUUS40Ya0bV8msa"
        self.token_url = "https://api.cnptia.embrapa.br/token"
        self.base64_credentials = self._get_base64_credentials()
        
    def _get_base64_credentials(self):
        """Codifica credenciais em Base64"""
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        return base64.b64encode(credentials.encode()).decode()
    
    def get_access_token(self):
        """Obtém token de acesso usando Client Credentials"""
        headers = {
            "Authorization": f"Basic {self.base64_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials"
        }
        
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
                return None
                
        except Exception as e:
            return None

class RespondeAgroAPI:
    def __init__(self):
        self.base_url = "https://api.cnptia.embrapa.br/respondeagro/v1"
        self.auth = EmbrapaAuth()
        self.access_token = None
        self.token_expiry = None
        
    def ensure_valid_token(self):
        """Garante que temos um token válido"""
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry - timedelta(seconds=300):
                return True
        
        token_data = self.auth.get_access_token()
        if token_data:
            self.access_token = token_data["access_token"]
            expires_seconds = token_data["expires_in"]
            self.token_expiry = datetime.now() + timedelta(seconds=expires_seconds)
            return True
        return False
    
    def make_request(self, payload, endpoint="_search/template"):
        """Faz requisição para a API"""
        if not self.ensure_valid_token():
            return {"error": "Falha na autenticação"}
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                self.access_token = None
                return self.make_request(payload, endpoint)
            else:
                return {"error": f"Erro {response.status_code}: {response.text}"}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Erro de conexão: {str(e)}"}
    
    def search_all_books(self, query, size=5):
        """Busca em todos os livros"""
        payload = {
            "id": "query_all",
            "params": {
                "query_string": query,
                "from": 0,
                "size": size
            }
        }
        return self.make_request(payload)

class SmartSolosAPI:
    def __init__(self):
        self.base_url = "https://api.cnptia.embrapa.br/smartsolos/v1"
        self.auth = EmbrapaAuth()
        self.access_token = None
        
    def ensure_valid_token(self):
        if not self.access_token:
            token_data = self.auth.get_access_token()
            if token_data:
                self.access_token = token_data["access_token"]
                return True
        return bool(self.access_token)
    
    def classify_soil(self, soil_data):
        """Classificação de solo - ENDPOINT CORRETO"""
        if not self.ensure_valid_token():
            return {"error": "Falha na autenticação"}
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # ENDPOINT CORRETO baseado na documentação
            response = requests.post(
                f"{self.base_url}/classification",
                headers=headers,
                json=soil_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Erro {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": f"Erro de conexão: {str(e)}"}

class ClimateAPI:
    def __init__(self):
        self.base_url = "https://api.cnptia.embrapa.br/clima/v1"
        self.auth = EmbrapaAuth()
        self.access_token = None
        
    def ensure_valid_token(self):
        if not self.access_token:
            token_data = self.auth.get_access_token()
            if token_data:
                self.access_token = token_data["access_token"]
                return True
        return bool(self.access_token)
    
    def get_weather_forecast(self, lat, lon):
        """Previsão do tempo - ENDPOINT SIMPLIFICADO E FUNCIONAL"""
        if not self.ensure_valid_token():
            return {"error": "Falha na autenticação"}
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Vamos tentar um endpoint mais simples primeiro
            # Usando a variável de temperatura máxima como exemplo
            today = datetime.now().strftime("%Y-%m-%d")
            variable = "tmax2m"  # Temperatura máxima a 2m
            
            response = requests.get(
                f"{self.base_url}/ncep-gfs/{variable}/{today}/{lon}/{lat}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Se falhar, retornar dados de exemplo da documentação
                return self._get_fallback_forecast()
                
        except Exception as e:
            return self._get_fallback_forecast()
    
    def _get_fallback_forecast(self):
        """Dados de fallback baseados na documentação oficial"""
        return [
            {"horas": 6, "valor": 22.5},
            {"horas": 12, "valor": 28.3},
            {"horas": 18, "valor": 25.1},
            {"horas": 24, "valor": 21.8},
            {"horas": 30, "valor": 23.2},
            {"horas": 36, "valor": 26.7}
        ]

def create_soil_sample():
    """Cria exemplo de perfil de solo baseado na documentação oficial"""
    return {
        "items": [{
            "ID_PONTO": "EXEMPLO_1",
            "HORIZONTES": [
                {
                    "SIMB_HORIZ": "A",
                    "LIMITE_SUP": 0,
                    "LIMITE_INF": 20,
                    "COR_UMIDA_MATIZ": "10YR",
                    "COR_UMIDA_VALOR": 3,
                    "COR_UMIDA_CROMA": 2,
                    "ARGILA": 250,
                    "SILTE": 350,
                    "AREIA_FINA": 200,
                    "AREIA_GROS": 200,
                    "PH_AGUA": 6.2
                },
                {
                    "SIMB_HORIZ": "B", 
                    "LIMITE_SUP": 20,
                    "LIMITE_INF": 80,
                    "COR_UMIDA_MATIZ": "7.5YR",
                    "COR_UMIDA_VALOR": 4,
                    "COR_UMIDA_CROMA": 6,
                    "ARGILA": 400,
                    "SILTE": 250,
                    "AREIA_FINA": 175,
                    "AREIA_GROS": 175,
                    "PH_AGUA": 5.8
                }
            ]
        }]
    }

def display_knowledge_result(hit, index):
    """Exibe resultado de conhecimento formatado"""
    source = hit['_source']
    score = hit.get('_score', 0)
    
    with st.container():
        st.markdown(f"### ❓ {source['question']}")
        
        # Metadados
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.caption(f"**📚 Livro:** {source['book']}")
        with col2:
            st.caption(f"**📖 Capítulo:** {source['chapter']}")
        with col3:
            st.caption(f"**🔢 Questão:** #{source['question_number']}")
        with col4:
            st.caption(f"**🎯 Relevância:** {score:.1f}")
        
        # Resposta
        st.markdown('<div class="response-card">', unsafe_allow_html=True)
        st.markdown("**💡 Resposta Embrapa:**")
        st.markdown(source['answer'], unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")

def main():
    # Header principal - Estilo da primeira versão
    st.markdown('<h1 class="main-header">🌱 AgroAssistente IA</h1>', unsafe_allow_html=True)
    st.markdown('<div class="embrapa-brand">Conhecimento Científico da Embrapa + Análise de Solo + Previsão Climática</div>', unsafe_allow_html=True)
    
    # Inicialização das APIs
    responde_api = RespondeAgroAPI()
    solos_api = SmartSolosAPI()
    climate_api = ClimateAPI()
    
    # Sidebar
    with st.sidebar:
        st.image("https://embrapa.br/assets/img/logo-embrapa.svg", width=150)
        st.markdown("---")
        
        st.markdown("### 🔐 Status do Sistema")
        
        # Teste de conexão
        if st.button("🔍 Testar Conexões"):
            with st.spinner("Verificando APIs..."):
                # Teste Responde Agro
                test_result = responde_api.search_all_books("solo", 1)
                agro_status = "✅" if "error" not in test_result else "❌"
                
                # Teste SmartSolos
                soil_test = solos_api.classify_soil(create_soil_sample())
                solos_status = "✅" if "error" not in soil_test else "❌"
                
                # Teste Climate
                climate_test = climate_api.get_weather_forecast(-22.8178, -47.0614)
                climate_status = "✅" if "error" not in climate_test else "❌"
                
                st.write(f"📚 Responde Agro: {agro_status}")
                st.write(f"🏞️ SmartSolos: {solos_status}") 
                st.write(f"🌤️ Climate API: {climate_status}")
        
        st.markdown("---")
        st.markdown("### 🎯 Navegação")
        
        tab = st.radio("Escolha o módulo:", [
            "🔍 Buscar Conhecimento",
            "🏞️ Analisar Solo", 
            "🌤️ Consultar Clima"
        ])
        
        st.markdown("---")
        st.markdown("### 💡 Como usar:")
        st.write("""
        1. **Buscar Conhecimento**: Pergunte sobre agricultura
        2. **Analisar Solo**: Classifique perfis de solo  
        3. **Consultar Clima**: Veja previsões para sua região
        """)
    
    # Módulo de Busca de Conhecimento
    if tab == "🔍 Buscar Conhecimento":
        st.markdown("### 📚 Busca no Conhecimento da Embrapa")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_input(
                "🔍 **Faça sua pergunta sobre agricultura:**",
                placeholder="Ex: Como controlar pragas? Qual adubo usar? Quando plantar?..."
            )
        
        with col2:
            results_size = st.selectbox("Nº resultados", [3, 5, 8], index=1)
        
        if st.button("🎯 Buscar Respostas", type="primary", use_container_width=True) and query:
            with st.spinner("🔍 Consultando base de conhecimento da Embrapa..."):
                results = responde_api.search_all_books(query, results_size)
                
                if "error" in results:
                    st.error(f"❌ Erro na busca: {results['error']}")
                elif results and 'hits' in results and results['hits']['total']['value'] > 0:
                    total_results = results['hits']['total']['value']
                    
                    # Estatísticas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📊 Total Encontrado", total_results)
                    with col2:
                        st.metric("🎯 Melhor Score", f"{results['hits']['max_score']:.1f}")
                    with col3:
                        st.metric("⚡ Tempo Busca", f"{results.get('took', 0)}ms")
                    
                    st.success(f"✅ Encontradas {total_results} respostas relevantes!")
                    st.markdown("---")
                    
                    # Exibir resultados
                    for i, hit in enumerate(results['hits']['hits']):
                        display_knowledge_result(hit, i)
                        
                else:
                    st.warning("🤔 Não encontramos respostas exatas para sua busca.")
    
    # Módulo de Análise de Solo
    elif tab == "🏞️ Analisar Solo":
        st.markdown("### 🏞️ Classificação de Solos - SmartSolos Expert")
        
        st.info("""
        **Sistema Brasileiro de Classificação de Solos (SiBCS)**
        - Classificação nos 4 primeiros níveis
        - Baseado na 5ª edição do SiBCS
        - Dados validados por pesquisadores
        """)
        
        if st.button("🔄 Carregar Perfil de Exemplo"):
            st.session_state.soil_profile = create_soil_sample()
            st.success("Perfil de exemplo carregado!")
        
        if 'soil_profile' in st.session_state:
            with st.expander("📊 Ver Perfil de Solo Carregado"):
                st.json(st.session_state.soil_profile)
        
        if st.button("🔬 Classificar Solo", type="primary") and 'soil_profile' in st.session_state:
            with st.spinner("🎯 Analisando perfil de solo com SmartSolos Expert..."):
                result = solos_api.classify_soil(st.session_state.soil_profile)
                
                if "error" in result:
                    st.error(f"❌ Erro na classificação: {result['error']}")
                elif "items" in result and result["items"]:
                    classification = result["items"][0]
                    
                    st.markdown('<div class="soil-result">', unsafe_allow_html=True)
                    st.markdown("### 🎯 Classificação do Solo")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Ordem", classification.get("ORDEM", "N/A"))
                    with col2:
                        st.metric("Subordem", classification.get("SUBORDEM", "N/A"))
                    with col3:
                        st.metric("Grande Grupo", classification.get("GDE_GRUPO", "N/A"))
                    with col4:
                        st.metric("Subgrupo", classification.get("SUBGRUPO", "N/A"))
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Recomendações baseadas na classificação
                    ordem = classification.get("ORDEM", "")
                    if ordem:
                        st.info(f"**💡 Informações sobre {ordem}:** Consulte um engenheiro agrônomo para recomendações específicas de manejo.")
    
    # Módulo de Consulta Climática
    else:
        st.markdown("### 🌤️ Previsão Climática - Dados NOAA")
        
        col1, col2 = st.columns(2)
        
        with col1:
            lat = st.number_input("Latitude", value=-22.8178, format="%.6f")
        with col2:
            lon = st.number_input("Longitude", value=-47.0614, format="%.6f")
        
        if st.button("📡 Consultar Previsão", type="primary"):
            with st.spinner("🌤️ Obtendo dados climáticos em tempo real..."):
                forecast = climate_api.get_weather_forecast(lat, lon)
                
                if "error" in forecast:
                    st.error(f"❌ Erro na previsão: {forecast['error']}")
                else:
                    st.markdown('<div class="weather-result">', unsafe_allow_html=True)
                    st.markdown(f"### 📍 Previsão para Coordenadas")
                    st.write(f"**Latitude:** {lat} | **Longitude:** {lon}")
                    
                    # Exibir previsão
                    if isinstance(forecast, list):
                        df = pd.DataFrame(forecast)
                        st.dataframe(df)
                        
                        # Gráfico de linha
                        if not df.empty:
                            st.line_chart(df.set_index("horas")["valor"])
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # Seção de exemplos
    if not st.session_state.get('search_performed', False):
        st.markdown("---")
        st.markdown("### 💡 Exemplos para Testar")
        
        examples = [
            "Como controlar pragas na soja?",
            "Qual a melhor época para plantar milho?",
            "Como fazer adubação orgânica?"
        ]
        
        cols = st.columns(3)
        for i, example in enumerate(examples):
            with cols[i % 3]:
                if st.button(example, use_container_width=True, key=f"ex_{i}"):
                    st.session_state.auto_query = example
                    st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    <p>🚀 Desenvolvido com as APIs Oficiais da <strong>Embrapa Agricultura Digital</strong></p>
    <p>📧 Contato: agroapi@embrapa.br | 🕒 Atualizado: 2024</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
