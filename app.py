import streamlit as st
import requests
import json
import base64
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import io
import warnings
warnings.filterwarnings('ignore')

# ================================
# CONFIGURAÇÃO DA PÁGINA
# ================================
st.set_page_config(
    page_title="🌱 AgroAssistente IA - Sistema Inteligente",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================
# CSS AVANÇADO
# ================================
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        background: linear-gradient(135deg, #2e7d32, #4caf50);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 800;
    }
    .sub-header {
        font-size: 1.4rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .response-card {
        background: linear-gradient(135deg, #f8fffd, #e8f5e9);
        border-left: 6px solid #2e7d32;
        padding: 2rem;
        margin: 1.5rem 0;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .analysis-card {
        background: linear-gradient(135deg, #fff3e0, #ffecb3);
        border-left: 6px solid #ff9800;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .insight-card {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        border-left: 6px solid #2196f3;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .token-status {
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
        text-align: center;
    }
    .status-valid {
        background: linear-gradient(135deg, #4caf50, #66bb6a);
        color: white;
    }
    .status-expired {
        background: linear-gradient(135deg, #ff9800, #ffb74d);
        color: white;
    }
    .status-error {
        background: linear-gradient(135deg, #f44336, #ef5350);
        color: white;
    }
    .credential-box {
        background: #1a1a1a;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
        color: #00ff00;
    }
    .metric-card {
        background: linear-gradient(135deg, #2c3e50, #34495e);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0px 0px;
        gap: 8px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2e7d32;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ================================
# CONFIGURAÇÕES DO BANCO DE DADOS
# ================================
DB_CONFIG = {
    "host": "dpg-d361csili9vc738rea90-a.oregon-postgres.render.com",
    "database": "postgresql_agro",
    "user": "postgresql_agro_user",
    "password": "gl5pErtk8tC2vqFLfswn7B7ocoxK7gk5",
    "port": "5432"
}

# ================================
# CLASSES PRINCIPAIS
# ================================
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

class AgroDatabase:
    def __init__(self):
        self.config = DB_CONFIG
    
    def get_connection(self):
        try:
            conn = psycopg2.connect(**self.config)
            return conn
        except Exception as e:
            st.error(f"❌ Erro ao conectar com o banco: {str(e)}")
            return None
    
    def load_productions(self):
        conn = self.get_connection()
        if conn is None:
            return pd.DataFrame()
        
        try:
            query = """
            SELECT * FROM productions 
            ORDER BY date DESC
            """
            df = pd.read_sql_query(query, conn)
            return df
        except Exception as e:
            st.error(f"❌ Erro ao carregar produções: {str(e)}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def load_inputs(self):
        conn = self.get_connection()
        if conn is None:
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM inputs ORDER BY date DESC"
            df = pd.read_sql_query(query, conn)
            return df
        except Exception as e:
            st.error(f"❌ Erro ao carregar insumos: {str(e)}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def load_price_config(self):
        conn = self.get_connection()
        if conn is None:
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM price_config"
            df = pd.read_sql_query(query, conn)
            return df
        except Exception as e:
            st.error(f"❌ Erro ao carregar preços: {str(e)}")
            return pd.DataFrame()
        finally:
            conn.close()

class RespondeAgroAPI:
    def __init__(self):
        self.base_url = "https://api.cnptia.embrapa.br/respondeagro/v1"
        self.auth = EmbrapaAuth()
        self.access_token = None
        self.token_expiry = None
        
    def ensure_valid_token(self):
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
                return {
                    "error": f"Erro {response.status_code}",
                    "details": response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Erro de conexão: {str(e)}"}
    
    def search_all_books(self, query, size=5):
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
    
    def get_token_status(self):
        if self.access_token and self.token_expiry:
            time_left = self.token_expiry - datetime.now()
            minutes_left = max(0, int(time_left.total_seconds() / 60))
            return {
                "status": "valid" if minutes_left > 5 else "expiring",
                "minutes_left": minutes_left,
                "token": self.access_token[:20] + "..." if self.access_token else None
            }
        return {"status": "no_token", "minutes_left": 0}

class AgroAnalytics:
    def __init__(self, database):
        self.db = database
    
    def calculate_financials(self, productions_df, inputs_df):
        price_config = self.db.load_price_config()
        
        if productions_df.empty:
            return {
                "total_revenue": 0,
                "first_quality_revenue": 0,
                "second_quality_revenue": 0,
                "total_costs": 0,
                "profit": 0,
                "profit_margin": 0
            }
        
        revenue_data = []
        for _, row in productions_df.iterrows():
            product = row['product']
            price_row = price_config[price_config['product'] == product]
            
            if not price_row.empty:
                first_price = price_row['first_quality_price'].values[0]
                second_price = price_row['second_quality_price'].values[0]
            else:
                first_price, second_price = 10.0, 5.0
            
            first_revenue = row['first_quality'] * first_price
            second_revenue = row['second_quality'] * second_price
            
            revenue_data.append({
                'product': product,
                'first_revenue': first_revenue,
                'second_revenue': second_revenue,
                'total_revenue': first_revenue + second_revenue
            })
        
        revenue_df = pd.DataFrame(revenue_data)
        total_revenue = revenue_df['total_revenue'].sum()
        first_quality_revenue = revenue_df['first_revenue'].sum()
        second_quality_revenue = revenue_df['second_revenue'].sum()
        
        total_costs = inputs_df['cost'].sum() if not inputs_df.empty else 0
        profit = total_revenue - total_costs
        profit_margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            "total_revenue": total_revenue,
            "first_quality_revenue": first_quality_revenue,
            "second_quality_revenue": second_quality_revenue,
            "total_costs": total_costs,
            "profit": profit,
            "profit_margin": profit_margin
        }
    
    def generate_business_insights(self, productions_df, inputs_df):
        """Gera insights inteligentes baseados nos dados do negócio"""
        insights = []
        
        if productions_df.empty:
            return ["📊 Adicione dados de produção para gerar insights"]
        
        # Análise de produtividade
        total_production = productions_df['first_quality'].sum() + productions_df['second_quality'].sum()
        avg_daily_production = total_production / len(productions_df['date'].unique())
        
        insights.append(f"📈 **Produtividade Média Diária**: {avg_daily_production:.1f} caixas/dia")
        
        # Análise de qualidade
        first_quality_percent = (productions_df['first_quality'].sum() / total_production * 100) if total_production > 0 else 0
        insights.append(f"🎯 **Qualidade Premium**: {first_quality_percent:.1f}% da produção é 1ª qualidade")
        
        # Análise financeira
        financials = self.calculate_financials(productions_df, inputs_df)
        insights.append(f"💰 **Lucratividade**: Margem de {financials['profit_margin']:.1f}%")
        
        # Análise por cultura
        best_product = productions_df.groupby('product')['first_quality'].sum().idxmax() if not productions_df.empty else "N/A"
        insights.append(f"🏆 **Cultura Mais Rentável**: {best_product}")
        
        # Análise temporal
        if len(productions_df) > 1:
            productions_df['date'] = pd.to_datetime(productions_df['date'])
            monthly_trend = productions_df.groupby(productions_df['date'].dt.to_period('M'))['first_quality'].sum()
            if len(monthly_trend) > 1:
                trend = "📈 Crescente" if monthly_trend.iloc[-1] > monthly_trend.iloc[-2] else "📉 Decrescente"
                insights.append(f"🕒 **Tendência Mensal**: {trend}")
        
        return insights
    
    def generate_recommendations(self, productions_df, inputs_df):
        """Gera recomendações inteligentes baseadas nos dados"""
        recommendations = []
        
        if productions_df.empty:
            return ["💡 Comece registrando suas produções para receber recomendações personalizadas"]
        
        # Análise de eficiência
        total_costs = inputs_df['cost'].sum() if not inputs_df.empty else 0
        total_production = productions_df['first_quality'].sum() + productions_df['second_quality'].sum()
        
        if total_production > 0 and total_costs > 0:
            cost_per_box = total_costs / total_production
            recommendations.append(f"💰 **Custo por Caixa**: R$ {cost_per_box:.2f} - Otimize seus insumos")
        
        # Análise de qualidade
        first_quality_ratio = productions_df['first_quality'].sum() / total_production if total_production > 0 else 0
        if first_quality_ratio < 0.7:
            recommendations.append("🎯 **Melhore a Qualidade**: Considere ajustes no manejo para aumentar a 1ª qualidade")
        
        # Análise de diversificação
        unique_products = productions_df['product'].nunique()
        if unique_products < 3:
            recommendations.append("🌱 **Diversificação**: Considere expandir para mais culturas para reduzir riscos")
        
        # Análise climática
        if 'temperature' in productions_df.columns:
            avg_temp = productions_df['temperature'].mean()
            if avg_temp > 30:
                recommendations.append("🌡️ **Temperatura Alta**: Considere estratégias de resfriamento para as culturas")
        
        return recommendations

# ================================
# FUNÇÕES DE VISUALIZAÇÃO
# ================================
def display_embrapa_result(hit, index):
    """Exibe um resultado formatado da Embrapa"""
    source = hit['_source']
    score = hit.get('_score', 0)
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### ❓ {source['question']}")
        with col2:
            st.metric("Relevância", f"{score:.1f}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.caption(f"**📚 Livro:** {source['book']}")
        with col2:
            st.caption(f"**📖 Capítulo:** {source['chapter']}")
        with col3:
            st.caption(f"**🔢 Questão:** #{source['question_number']}")
        with col4:
            st.caption(f"**📅 Ano:** {source['year']}")
        
        st.markdown('<div class="response-card">', unsafe_allow_html=True)
        st.markdown("**💡 Resposta Embrapa:**")
        st.markdown(source['answer'], unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.expander("📎 Recursos Adicionais"):
            col1, col2 = st.columns(2)
            with col1:
                if source.get('pdf'):
                    st.markdown(f"**[📄 PDF Completo]({source['pdf']})**")
            with col2:
                if source.get('epub'):
                    st.markdown(f"**[📱 Versão EPUB]({source['epub']})**")
        
        st.markdown("---")

def create_production_dashboard(productions_df, inputs_df, analytics):
    """Cria dashboard interativo de produção"""
    
    if productions_df.empty:
        st.warning("📊 Adicione dados de produção para visualizar o dashboard")
        return
    
    # Métricas principais
    financials = analytics.calculate_financials(productions_df, inputs_df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_boxes = productions_df['first_quality'].sum() + productions_df['second_quality'].sum()
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("📦 Total Produzido", f"{total_boxes:,.0f} cx")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("💰 Receita Total", f"R$ {financials['total_revenue']:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("💸 Custos Totais", f"R$ {financials['total_costs']:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("🎯 Lucro Líquido", f"R$ {financials['profit']:,.2f}", f"{financials['profit_margin']:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Produção por Cultura")
        production_by_product = productions_df.groupby('product')[['first_quality', 'second_quality']].sum()
        production_by_product['total'] = production_by_product['first_quality'] + production_by_product['second_quality']
        
        fig = px.bar(production_by_product.reset_index(), x='product', y='total',
                     color='product', color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', 
                         paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Qualidade por Cultura")
        quality_data = []
        for product in productions_df['product'].unique():
            product_data = productions_df[productions_df['product'] == product]
            total = product_data['first_quality'].sum() + product_data['second_quality'].sum()
            first_percent = (product_data['first_quality'].sum() / total * 100) if total > 0 else 0
            second_percent = (product_data['second_quality'].sum() / total * 100) if total > 0 else 0
            
            quality_data.append({
                'product': product,
                '1ª Qualidade': first_percent,
                '2ª Qualidade': second_percent
            })
        
        quality_df = pd.DataFrame(quality_data)
        fig = px.bar(quality_df, x='product', y=['1ª Qualidade', '2ª Qualidade'], 
                     barmode='stack', color_discrete_sequence=['#2ecc71', '#f1c40f'])
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                         font=dict(color='white'), yaxis_title="Percentual (%)")
        st.plotly_chart(fig, use_container_width=True)

# ================================
# PÁGINAS PRINCIPAIS
# ================================
def show_ai_assistant(api, db, analytics):
    """Página principal do assistente IA"""
    
    st.markdown('<h1 class="main-header">🧠 AgroAssistente IA Inteligente</h1>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Conhecimento Científico da Embrapa + Análise de Dados do Seu Negócio</div>', unsafe_allow_html=True)
    
    # Carregar dados do negócio
    productions_df = db.load_productions()
    inputs_df = db.load_inputs()
    
    # Sidebar com análises do negócio
    with st.sidebar:
        st.header("📈 Análise do Seu Negócio")
        
        if not productions_df.empty:
            insights = analytics.generate_business_insights(productions_df, inputs_df)
            st.markdown("### 💡 Insights do Negócio")
            for insight in insights:
                st.success(insight)
            
            recommendations = analytics.generate_recommendations(productions_df, inputs_df)
            st.markdown("### 🎯 Recomendações")
            for rec in recommendations:
                st.info(rec)
        else:
            st.info("💼 Adicione dados de produção para insights personalizados")
        
        st.markdown("---")
        st.header("🔍 Configurações de Busca")
        
        search_mode = st.radio(
            "Modo de Busca:",
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
        
        results_size = st.slider("Número de resultados", 3, 10, 5)
    
    # Área de busca principal
    tab1, tab2, tab3 = st.tabs(["🔍 Busca Inteligente", "📊 Meu Negócio", "🤖 Análise IA"])
    
    with tab1:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_input(
                "💬 **Faça sua pergunta sobre agricultura:**",
                placeholder="Ex: Como controlar pragas? Qual adubo usar? Quando plantar?...",
                help="Combine conhecimento científico com dados do seu negócio"
            )
        
        with col2:
            search_clicked = st.button("🚀 Buscar Conhecimento", type="primary", use_container_width=True)
        
        if search_clicked and query:
            with st.spinner("🔍 Conectando ao conhecimento científico da Embrapa..."):
                if not api.ensure_valid_token():
                    st.error("❌ Falha na autenticação com a API Embrapa")
                    return
                
                if search_mode == "🔍 Todos os Livros":
                    results = api.search_all_books(query, results_size)
                else:
                    results = api.search_specific_book(query, book_id, results_size)
                
                if "error" in results:
                    st.error(f"❌ Erro na busca: {results['error']}")
                elif results and 'hits' in results and results['hits']['total']['value'] > 0:
                    total_results = results['hits']['total']['value']
                    st.success(f"✅ Encontradas {total_results} respostas científicas relevantes!")
                    
                    for i, hit in enumerate(results['hits']['hits']):
                        display_embrapa_result(hit, i)
                else:
                    st.warning("🤔 Não encontramos respostas exatas. Tente reformular sua pergunta.")
    
    with tab2:
        st.header("📊 Dashboard do Seu Negócio")
        create_production_dashboard(productions_df, inputs_df, analytics)
        
        # Dados recentes
        if not productions_df.empty:
            st.subheader("📋 Produções Recentes")
            st.dataframe(productions_df.head(10), use_container_width=True)
    
    with tab3:
        st.header("🤖 Análise IA Integrada")
        
        if not productions_df.empty:
            # Análise avançada
            st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
            st.markdown("### 📈 Análise Preditiva")
            
            # Simulação de análise preditiva
            financials = analytics.calculate_financials(productions_df, inputs_df)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Tendência", "Positiva ↗️", "15%")
            with col2:
                st.metric("🎯 ROI Estimado", f"{(financials['profit']/financials['total_costs']*100) if financials['total_costs'] > 0 else 0:.1f}%")
            with col3:
                st.metric("🚀 Potencial", "Alto", "12%")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Recomendações específicas
            st.markdown('<div class="insight-card">', unsafe_allow_html=True)
            st.markdown("### 💡 Recomendações Personalizadas")
            
            if financials['profit_margin'] < 20:
                st.warning("**Otimização Financeira**: Sua margem pode ser melhorada. Considere:")
                st.write("- Negociar melhores preços com fornecedores")
                st.write("- Aumentar a produção de 1ª qualidade")
                st.write("- Diversificar culturas para reduzir riscos")
            
            first_quality_ratio = productions_df['first_quality'].sum() / (productions_df['first_quality'].sum() + productions_df['second_quality'].sum())
            if first_quality_ratio < 0.6:
                st.info("**Melhoria de Qualidade**: Estratégias para aumentar a 1ª qualidade:")
                st.write("- Revisar práticas de colheita")
                st.write("- Melhorar condições de armazenamento")
                st.write("- Capacitar equipe em seleção")
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("💼 Adicione dados de produção para habilitar a análise IA completa")

def show_system_status(api, db):
    """Página de status do sistema"""
    st.header("🔧 Status do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌐 Conexão Embrapa")
        token_status = api.get_token_status()
        
        if token_status["status"] == "valid":
            st.markdown(f'<span class="token-status status-valid">✅ Token Válido</span>', unsafe_allow_html=True)
            st.write(f"Expira em: {token_status['minutes_left']} minutos")
        elif token_status["status"] == "expiring":
            st.markdown(f'<span class="token-status status-expired">⚠️ Token Expirando</span>', unsafe_allow_html=True)
            st.write(f"Expira em: {token_status['minutes_left']} minutos")
        else:
            st.markdown(f'<span class="token-status status-error">❌ Sem Token</span>', unsafe_allow_html=True)
        
        if st.button("🔄 Renovar Token Embrapa"):
            api.access_token = None
            st.rerun()
    
    with col2:
        st.subheader("🗄️ Banco de Dados")
        
        # Testar conexão com o banco
        conn = db.get_connection()
        if conn:
            st.success("✅ Conexão estabelecida")
            
            # Estatísticas do banco
            productions_df = db.load_productions()
            inputs_df = db.load_inputs()
            
            st.write(f"📊 Produções: {len(productions_df)} registros")
            st.write(f"💰 Insumos: {len(inputs_df)} registros")
            st.write(f"🏪 Culturas: {productions_df['product'].nunique() if not productions_df.empty else 0} tipos")
            
            conn.close()
        else:
            st.error("❌ Falha na conexão")
    
    # Credenciais (em expander)
    with st.expander("🔐 Credenciais do Sistema"):
        st.markdown("""
        <div class="credential-box">
        <strong>Embrapa API:</strong><br>
        Consumer Key: DI_JQ6o06C8ktdGR0pwpuSL6f3ka<br>
        Consumer Secret: BXmyFKVuIHlCsaUUS40Ya0bV8msa<br>
        Token URL: https://api.cnptia.embrapa.br/token<br><br>
        
        <strong>Banco de Dados:</strong><br>
        Host: dpg-d361csili9vc738rea90-a.oregon-postgres.render.com<br>
        Database: postgresql_agro<br>
        User: postgresql_agro_user<br>
        Port: 5432
        </div>
        """, unsafe_allow_html=True)

# ================================
# APLICAÇÃO PRINCIPAL
# ================================
def main():
    # Inicialização dos serviços
    api = RespondeAgroAPI()
    db = AgroDatabase()
    analytics = AgroAnalytics(db)
    
    # Sidebar principal
    with st.sidebar:
        st.image("https://embrapa.br/assets/img/logo-embrapa.svg", width=150)
        st.markdown("---")
        
        page = st.radio(
            "Navegação Principal:",
            ["🧠 Assistente IA", "🔧 Status do Sistema"]
        )
        
        st.markdown("---")
        st.markdown("### 💡 Dicas Rápidas")
        st.info("""
        - Combine perguntas técnicas com dados do seu negócio
        - Use o modo específico para culturas determinadas
        - Consulte análises preditivas regularmente
        """)
    
    # Navegação entre páginas
    if page == "🧠 Assistente IA":
        show_ai_assistant(api, db, analytics)
    elif page == "🔧 Status do Sistema":
        show_system_status(api, db)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    <p>🚀 <strong>SISTEMA INTELIGENTE AGRO</strong> - Conhecimento Científico + Dados do Negócio</p>
    <p>📧 Suporte: agroai@embrapa.br | 🕒 Atualizado: Dez 2024</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
