import streamlit as st
import requests
import json
import base64
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="AgroAssistente IA - Embrapa",
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
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .token-status {
        padding: 6px 12px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-valid {
        background: #4caf50;
        color: white;
    }
    .status-expired {
        background: #ff9800;
        color: white;
    }
    .status-error {
        background: #f44336;
        color: white;
    }
    .credential-box {
        background: #f5f5f5;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        font-family: monospace;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

class EmbrapaAuth:
    def __init__(self):
        # SUAS CREDENCIAIS - Cole aqui as que você recebeu
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
                st.error(f"❌ Erro na autenticação: {response.status_code}")
                st.write(f"Resposta: {response.text}")
                return None
                
        except Exception as e:
            st.error(f"🚫 Erro de conexão: {e}")
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
            if datetime.now() < self.token_expiry - timedelta(seconds=300):  # 5 min de margem
                return True
        
        # Obter novo token
        token_data = self.auth.get_access_token()
        if token_data:
            self.access_token = token_data["access_token"]
            expires_seconds = token_data["expires_in"]
            self.token_expiry = datetime.now() + timedelta(seconds=expires_seconds)
            return True
        return False
    
    def make_request(self, payload, endpoint="_search/template"):
        """Faz requisição para a API com autenticação"""
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
                # Token expirado, tentar renovar
                self.access_token = None
                return self.make_request(payload, endpoint)
            else:
                return {
                    "error": f"Erro {response.status_code}",
                    "details": response.text
                }
                
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
    
    def search_specific_book(self, query, book_id, size=3):
        """Busca em livro específico"""
        payload = {
            "id": "query_one_book",
            "params": {
                "query_string": query,
                "book_id": book_id,
                "from": 0,
                "size": size
            }
        }
        return self.make_request(payload)
    
    def autocomplete(self, query, book_id=None):
        """Sugestões de autocomplete"""
        template_id = "autocomplete_one_book" if book_id else "autocomplete_all"
        payload = {
            "id": template_id,
            "params": {
                "query_string": query,
                "book_id": book_id
            } if book_id else {
                "query_string": query
            }
        }
        return self.make_request(payload)
    
    def get_book_ids(self):
        """Obtém lista de livros disponíveis"""
        payload = {
            "id": "book_ids",
            "params": {}
        }
        return self.make_request(payload)
    
    def get_token_status(self):
        """Retorna status do token"""
        if self.access_token and self.token_expiry:
            time_left = self.token_expiry - datetime.now()
            minutes_left = max(0, int(time_left.total_seconds() / 60))
            return {
                "status": "valid" if minutes_left > 5 else "expiring",
                "minutes_left": minutes_left,
                "token": self.access_token[:20] + "..." if self.access_token else None
            }
        return {"status": "no_token", "minutes_left": 0}

def display_result(hit, index):
    """Exibe um resultado formatado"""
    source = hit['_source']
    score = hit.get('_score', 0)
    
    with st.container():
        # Header do resultado
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### ❓ {source['question']}")
        with col2:
            st.metric("Relevância", f"{score:.1f}")
        
        # Metadados
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.caption(f"**📚 Livro:** {source['book']}")
        with col2:
            st.caption(f"**📖 Capítulo:** {source['chapter']}")
        with col3:
            st.caption(f"**🔢 Questão:** #{source['question_number']}")
        with col4:
            st.caption(f"**📅 Ano:** {source['year']}")
        
        # Resposta
        st.markdown('<div class="response-card">', unsafe_allow_html=True)
        st.markdown("**💡 Resposta Embrapa:**")
        st.markdown(source['answer'], unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Links e recursos
        with st.expander("📎 Recursos Adicionais"):
            col1, col2 = st.columns(2)
            with col1:
                if source.get('pdf'):
                    st.markdown(f"**[📄 PDF Completo]({source['pdf']})**")
            with col2:
                if source.get('epub'):
                    st.markdown(f"**[📱 Versão EPUB]({source['epub']})**")
        
        st.markdown("---")

def main():
    # Header principal
    st.markdown('<h1 class="main-header">🌱 AgroAssistente IA</h1>', unsafe_allow_html=True)
    st.markdown('<div class="embrapa-brand">Conectado à API Oficial da Embrapa - Conhecimento Científico em Tempo Real</div>', unsafe_allow_html=True)
    
    # Inicialização da API
    api = RespondeAgroAPI()
    
    # Sidebar
    with st.sidebar:
        st.image("https://embrapa.br/assets/img/logo-embrapa.svg", width=150)
        st.markdown("---")
        
        st.markdown("### 🔐 Status da Autenticação")
        
        # Status do token
        token_status = api.get_token_status()
        
        if token_status["status"] == "valid":
            st.markdown(f'<span class="token-status status-valid">✅ Token Válido</span>', unsafe_allow_html=True)
            st.caption(f"Expira em: {token_status['minutes_left']} minutos")
        elif token_status["status"] == "expiring":
            st.markdown(f'<span class="token-status status-expired">⚠️ Token Expirando</span>', unsafe_allow_html=True)
            st.caption(f"Expira em: {token_status['minutes_left']} minutos")
        else:
            st.markdown(f'<span class="token-status status-error">❌ Sem Token</span>', unsafe_allow_html=True)
        
        # Botão para renovar token
        if st.button("🔄 Renovar Token"):
            api.access_token = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🎯 Modo de Busca")
        
        search_mode = st.radio(
            "Escolha o tipo de busca:",
            ["🔍 Todos os Livros", "📚 Livro Específico"]
        )
        
        book_id = None
        if search_mode == "📚 Livro Específico":
            books = {
                "Soja": "soja",
                "Milho": "milho", 
                "Café": "cafe",
                "Feijão": "feijao",
                "Algodão": "algodao",
                "ILPF": "ilpf",
                "Abacaxi": "abacaxi",
                "Uva": "uva"
            }
            selected_book = st.selectbox("Selecione o livro:", list(books.keys()))
            book_id = books[selected_book]
        
        st.markdown("---")
        st.markdown("### 📊 Configurações")
        results_size = st.slider("Número de resultados", 3, 10, 5)
        
        st.markdown("---")
        st.markdown("### 🔧 Suas Credenciais")
        with st.expander("Ver Credenciais"):
            st.markdown("""
            <div class="credential-box">
            Consumer Key: DI_JQ6o06C8ktdGR0pwpuSL6f3ka<br>
            Consumer Secret: BXmyFKVuIHlCsaUUS40Ya0bV8msa<br>
            Token URL: https://api.cnptia.embrapa.br/token
            </div>
            """, unsafe_allow_html=True)
    
    # Área principal de busca
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "🔍 **Faça sua pergunta sobre agricultura:**",
            placeholder="Ex: Como controlar pragas? Qual adubo usar? Quando plantar?...",
            help="Digite termos específicos para melhores resultados"
        )
    
    with col2:
        if st.button("🎯 Buscar na Embrapa", type="primary", use_container_width=True):
            st.session_state.do_search = True
    
    # Busca automática quando query é preenchida por exemplo
    if 'auto_query' in st.session_state:
        query = st.session_state.auto_query
        st.session_state.do_search = True
        del st.session_state.auto_query
    
    # Executar busca
    if st.session_state.get('do_search', False) and query:
        st.session_state.do_search = False
        
        with st.spinner("🔍 Conectando à API Embrapa..."):
            # Primeiro verifica autenticação
            if not api.ensure_valid_token():
                st.error("❌ Falha na autenticação com a API Embrapa")
                return
            
            # Realiza a busca
            if search_mode == "🔍 Todos os Livros":
                results = api.search_all_books(query, results_size)
            else:
                results = api.search_specific_book(query, book_id, results_size)
            
            # Processamento dos resultados
            if "error" in results:
                st.error(f"❌ Erro na busca: {results['error']}")
                if "details" in results:
                    with st.expander("Detalhes técnicos do erro"):
                        st.code(results['details'])
            elif results and 'hits' in results and results['hits']['total']['value'] > 0:
                total_results = results['hits']['total']['value']
                
                # Estatísticas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📊 Total Encontrado", total_results)
                with col2:
                    st.metric("🎯 Melhor Score", f"{results['hits']['max_score']:.1f}")
                with col3:
                    st.metric("⚡ Tempo Busca", f"{results.get('took', 0)}ms")
                with col4:
                    unique_books = len(set(hit['_source']['book_id'] for hit in results['hits']['hits']))
                    st.metric("📚 Livros", unique_books)
                
                st.success(f"✅ Encontradas {total_results} respostas relevantes!")
                st.markdown("---")
                
                # Exibir resultados
                for i, hit in enumerate(results['hits']['hits']):
                    display_result(hit, i)
                    
            else:
                st.warning("""
                🤔 Não encontramos respostas exatas para sua busca.
                
                **💡 Dicas para melhorar sua busca:**
                - Use termos mais específicos (ex: "ferrugem soja" em vez de "doenças")
                - Verifique a ortografia
                - Tente sinônimos
                - Use o modo "Todos os Livros" para busca mais ampla
                """)
    
    # Seção de exemplos (quando não há busca)
    if not query:
        st.markdown("---")
        st.markdown("### 💡 Exemplos de Perguntas")
        
        examples = [
            "Como controlar a ferrugem da soja?",
            "Qual a melhor época para plantar milho?",
            "Como fazer adubação orgânica?",
            "Controle de cigarrinha do milho",
            "Manejo de irrigação para feijão",
            "Como identificar deficiência de nutrientes?"
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
    <p>🚀 <strong>CONEXÃO ATIVA</strong> - API Oficial Embrapa Agricultura Digital</p>
    <p>📧 Contato: agroapi@embrapa.br | 🕒 Atualizado: Nov 2024</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
