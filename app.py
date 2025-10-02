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
    .metric-card {
        background: linear-gradient(135deg, #2c3e50, #34495e);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .user-message {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        border: 1px solid #90caf9;
    }
    .assistant-message {
        background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        border: 1px solid #a5d6a7;
    }
</style>
""", unsafe_allow_html=True)

# ================================
# CONFIGURAÇÕES
# ================================
DB_CONFIG = {
    "host": "dpg-d361csili9vc738rea90-a.oregon-postgres.render.com",
    "database": "postgresql_agro",
    "user": "postgresql_agro_user",
    "password": "gl5pErtk8tC2vqFLfswn7B7ocoxK7gk5",
    "port": "5432"
}

# ================================
# SISTEMA UNIFICADO DE IA
# ================================
class AgroIntelligentAssistant:
    def __init__(self):
        self.db = AgroDatabase()
        self.embrapa_api = EmbrapaAPI()
        self.conversation_history = []
    
    def get_business_context(self):
        """Obtém todos os dados do negócio para contexto"""
        productions = self.db.load_productions()
        inputs = self.db.load_inputs()
        price_config = self.db.load_price_config()
        
        context = {
            "has_data": not productions.empty,
            "productions": [],
            "financial_summary": {},
            "insights": []
        }
        
        if not productions.empty:
            # Resumo das produções
            context["productions"] = productions.to_dict('records')
            
            # Análise financeira
            total_first_quality = productions['first_quality'].sum()
            total_second_quality = productions['second_quality'].sum()
            total_production = total_first_quality + total_second_quality
            
            # Cálculo de receitas
            revenue = 0
            for _, row in productions.iterrows():
                product = row['product']
                price_row = price_config[price_config['product'] == product]
                first_price = price_row['first_quality_price'].values[0] if not price_row.empty else 10.0
                second_price = price_row['second_quality_price'].values[0] if not price_row.empty else 5.0
                revenue += row['first_quality'] * first_price + row['second_quality'] * second_price
            
            total_costs = inputs['cost'].sum() if not inputs.empty else 0
            profit = revenue - total_costs
            profit_margin = (profit / revenue * 100) if revenue > 0 else 0
            
            context["financial_summary"] = {
                "total_revenue": revenue,
                "total_costs": total_costs,
                "profit": profit,
                "profit_margin": profit_margin,
                "total_production": total_production,
                "first_quality_percent": (total_first_quality / total_production * 100) if total_production > 0 else 0
            }
            
            # Insights
            if profit_margin < 20:
                context["insights"].append("Margem de lucro pode ser melhorada")
            if context["financial_summary"]["first_quality_percent"] < 60:
                context["insights"].append("Percentual de 1ª qualidade abaixo do ideal")
            
            # Cultura principal
            main_crop = productions.groupby('product')['first_quality'].sum().idxmax()
            context["main_crop"] = main_crop
            
        return context
    
    def search_embrapa_knowledge(self, query):
        """Busca conhecimento científico na Embrapa"""
        try:
            results = self.embrapa_api.search_all_books(query, size=3)
            if "error" in results or not results.get('hits', {}).get('hits'):
                return "Não encontrei informações específicas na base científica da Embrapa para esta pergunta."
            
            # Processar resultados
            knowledge = []
            for hit in results['hits']['hits'][:3]:
                source = hit['_source']
                knowledge.append({
                    'pergunta': source.get('question', ''),
                    'resposta': source.get('answer', '')[:300] + "...",
                    'livro': source.get('book', ''),
                    'relevancia': hit.get('_score', 0)
                })
            
            return knowledge
        except Exception as e:
            return f"Erro ao acessar base científica: {str(e)}"
    
    def generate_intelligent_response(self, user_message):
        """Gera resposta inteligente integrando todos os dados"""
        
        # Obter contexto do negócio
        business_context = self.get_business_context()
        
        # Buscar conhecimento científico
        scientific_knowledge = self.search_embrapa_knowledge(user_message)
        
        # Construir prompt contextual
        prompt = self._build_contextual_prompt(user_message, business_context, scientific_knowledge)
        
        # Gerar resposta (aqui usaremos uma lógica inteligente de templates)
        response = self._generate_contextual_response(prompt, business_context, scientific_knowledge)
        
        # Atualizar histórico
        self.conversation_history.append({
            "user": user_message,
            "assistant": response,
            "timestamp": datetime.now()
        })
        
        return response
    
    def _build_contextual_prompt(self, user_message, business_context, scientific_knowledge):
        """Constrói o prompt contextual para a resposta"""
        
        prompt_parts = []
        
        # Contexto do negócio
        if business_context["has_data"]:
            financial = business_context["financial_summary"]
            prompt_parts.append(f"""
            CONTEXTO DO NEGÓCIO:
            - Cultura principal: {business_context.get('main_crop', 'Não identificada')}
            - Produção total: {financial['total_production']:.0f} caixas
            - Receita: R$ {financial['total_revenue']:.2f}
            - Custos: R$ {financial['total_costs']:.2f}
            - Lucro: R$ {financial['profit']:.2f}
            - Margem: {financial['profit_margin']:.1f}%
            - Qualidade 1ª: {financial['first_quality_percent']:.1f}%
            - Insights: {', '.join(business_context['insights']) if business_context['insights'] else 'Nenhum insight crítico'}
            """)
        else:
            prompt_parts.append("CONTEXTO DO NEGÓCIO: Nenhum dado de produção cadastrado ainda.")
        
        # Conhecimento científico
        if isinstance(scientific_knowledge, list) and scientific_knowledge:
            sci_text = "CONHECIMENTO CIENTÍFICO EMBRAPA:\n"
            for i, knowledge in enumerate(scientific_knowledge, 1):
                sci_text += f"""
                {i}. {knowledge['pergunta']}
                   Resposta: {knowledge['resposta']}
                   Fonte: {knowledge['livro']} (Relevância: {knowledge['relevancia']:.1f})
                """
            prompt_parts.append(sci_text)
        else:
            prompt_parts.append("CONHECIMENTO CIENTÍFICO: " + str(scientific_knowledge))
        
        prompt_parts.append(f"PERGUNTA DO USUÁRIO: {user_message}")
        
        return "\n".join(prompt_parts)
    
    def _generate_contextual_response(self, prompt, business_context, scientific_knowledge):
        """Gera resposta contextual integrando todas as informações"""
        
        # Análise da pergunta do usuário
        user_question = prompt.split("PERGUNTA DO USUÁRIO: ")[-1].lower()
        
        # Resposta baseada no tipo de pergunta
        if any(word in user_question for word in ['como', 'fazer', 'procedimento']):
            return self._generate_how_to_response(user_question, business_context, scientific_knowledge)
        elif any(word in user_question for word in ['quanto', 'custo', 'preço', 'financeiro']):
            return self._generate_financial_response(user_question, business_context, scientific_knowledge)
        elif any(word in user_question for word in ['qualidade', 'produtividade', 'rendimento']):
            return self._generate_quality_response(user_question, business_context, scientific_knowledge)
        elif any(word in user_question for word in ['problema', 'doença', 'praga']):
            return self._generate_problem_response(user_question, business_context, scientific_knowledge)
        else:
            return self._generate_general_response(user_question, business_context, scientific_knowledge)
    
    def _generate_how_to_response(self, question, business_context, scientific_knowledge):
        """Gera resposta para perguntas de procedimento"""
        
        response_parts = ["🌱 **Orientação Técnica Personalizada**\n\n"]
        
        # Adicionar conhecimento científico
        if isinstance(scientific_knowledge, list) and scientific_knowledge:
            response_parts.append("**Base Científica Embrapa:**")
            for knowledge in scientific_knowledge:
                response_parts.append(f"📚 {knowledge['resposta']}")
            response_parts.append("")
        
        # Adicionar contexto do negócio
        if business_context["has_data"]:
            financial = business_context["financial_summary"]
            response_parts.append("**Contexto do Seu Negócio:**")
            response_parts.append(f"• Sua produção atual: {financial['total_production']:.0f} caixas")
            response_parts.append(f"• Margem atual: {financial['profit_margin']:.1f}%")
            
            if financial['first_quality_percent'] < 60:
                response_parts.append("• 💡 **Oportunidade**: Você pode aumentar a qualidade 1ª para melhorar seus rendimentos")
            
            if financial['profit_margin'] < 15:
                response_parts.append("• 💰 **Alerta**: Sua margem está baixa - considere otimizar custos")
        
        response_parts.append("\n**Próximos Passos Recomendados:**")
        response_parts.append("1. Implemente as práticas recomendadas pela Embrapa")
        response_parts.append("2. Monitore os resultados semanalmente")
        response_parts.append("3. Ajuste conforme as condições locais")
        
        return "\n".join(response_parts)
    
    def _generate_financial_response(self, question, business_context, scientific_knowledge):
        """Gera resposta para perguntas financeiras"""
        
        response_parts = ["💰 **Análise Financeira**\n\n"]
        
        if business_context["has_data"]:
            financial = business_context["financial_summary"]
            
            response_parts.append("**Seu Desempenho Atual:**")
            response_parts.append(f"• 📈 **Receita Total**: R$ {financial['total_revenue']:,.2f}")
            response_parts.append(f"• 💸 **Custos Totais**: R$ {financial['total_costs']:,.2f}")
            response_parts.append(f"• 🎯 **Lucro Líquido**: R$ {financial['profit']:,.2f}")
            response_parts.append(f"• 📊 **Margem de Lucro**: {financial['profit_margin']:.1f}%")
            response_parts.append(f"• 🌟 **Qualidade 1ª**: {financial['first_quality_percent']:.1f}% da produção")
            
            # Recomendações baseadas nos dados
            response_parts.append("\n**💡 Recomendações Financeiras:**")
            
            if financial['profit_margin'] < 10:
                response_parts.append("• **Ação Urgente**: Sua margem está crítica. Reveja custos e preços")
            elif financial['profit_margin'] < 20:
                response_parts.append("• **Otimização**: Há espaço para melhorar a margem. Foque em eficiência")
            else:
                response_parts.append("• **Excelente**: Margem saudável! Mantenha o bom trabalho")
            
            if financial['first_quality_percent'] < 50:
                response_parts.append("• **Qualidade**: Invista em práticas que aumentem a 1ª qualidade - tem alto retorno")
                
        else:
            response_parts.append("📊 **Para análises financeiras precisas, cadastre seus dados de produção e custos.**")
        
        # Adicionar conhecimento científico se relevante
        if isinstance(scientific_knowledge, list) and scientific_knowledge:
            response_parts.append("\n**Conhecimento Científico Aplicável:**")
            for knowledge in scientific_knowledge[:2]:
                response_parts.append(f"• {knowledge['resposta']}")
        
        return "\n".join(response_parts)
    
    def _generate_quality_response(self, question, business_context, scientific_knowledge):
        """Gera resposta para perguntas sobre qualidade"""
        
        response_parts = ["🎯 **Gestão de Qualidade**\n\n"]
        
        if business_context["has_data"]:
            financial = business_context["financial_summary"]
            
            response_parts.append(f"**Seu Desempenho de Qualidade:**")
            response_parts.append(f"• {financial['first_quality_percent']:.1f}% da sua produção é 1ª qualidade")
            
            if financial['first_quality_percent'] >= 70:
                response_parts.append("• ✅ **Excelente**! Sua qualidade está acima da média")
            elif financial['first_quality_percent'] >= 50:
                response_parts.append("• ⚠️ **Bom**, mas pode melhorar. Há espaço para crescimento")
            else:
                response_parts.append("• 🔄 **Precisa melhorar**. Foque em práticas que elevem a qualidade")
        
        # Conhecimento científico sobre qualidade
        if isinstance(scientific_knowledge, list) and scientific_knowledge:
            response_parts.append("\n**Técnicas Comprovadas para Qualidade:**")
            for knowledge in scientific_knowledge:
                response_parts.append(f"• {knowledge['resposta']}")
        else:
            response_parts.append("\n**Dicas Gerais para Melhorar Qualidade:**")
            response_parts.append("• Colha no ponto certo")
            response_parts.append("• Maneje adequadamente o solo")
            response_parts.append("• Controle pragas e doenças preventivamente")
            response_parts.append("• Invista em boas sementes/mudas")
        
        return "\n".join(response_parts)
    
    def _generate_problem_response(self, question, business_context, scientific_knowledge):
        """Gera resposta para problemas e doenças"""
        
        response_parts = ["🔍 **Análise de Problemas**\n\n"]
        
        response_parts.append("**Com base no conhecimento científico da Embrapa:**")
        
        if isinstance(scientific_knowledge, list) and scientific_knowledge:
            for knowledge in scientific_knowledge:
                response_parts.append(f"• {knowledge['resposta']}")
        else:
            response_parts.append("• Consulte um técnico agrícola para diagnóstico preciso")
            response_parts.append("• Coletar amostras para análise")
            response_parts.append("• Documentar sintomas e condições climáticas")
        
        response_parts.append("\n**Ações Recomendadas:**")
        response_parts.append("1. Identifique corretamente o problema")
        response_parts.append("2. Siga as recomendações técnicas validadas")
        response_parts.append("3. Monitore a evolução")
        response_parts.append("4. Registre os resultados para aprendizado futuro")
        
        if business_context["has_data"]:
            response_parts.append(f"\n💡 **Contexto da sua lavoura**: Você cultiva {business_context.get('main_crop', 'diversas culturas')}")
        
        return "\n".join(response_parts)
    
    def _generate_general_response(self, question, business_context, scientific_knowledge):
        """Gera resposta para perguntas gerais"""
        
        response_parts = ["🌾 **Assistência Agrícola Integral**\n\n"]
        
        # Conhecimento científico
        if isinstance(scientific_knowledge, list) and scientific_knowledge:
            response_parts.append("**Conhecimento Científico da Embrapa:**")
            for knowledge in scientific_knowledge:
                response_parts.append(f"• {knowledge['resposta']}")
        else:
            response_parts.append("• Estou aqui para ajudar com questões agrícolas baseadas em ciência")
        
        # Contexto do negócio
        if business_context["has_data"]:
            financial = business_context["financial_summary"]
            response_parts.append(f"\n**Resumo do Seu Negócio:**")
            response_parts.append(f"• Produção: {financial['total_production']:.0f} caixas")
            response_parts.append(f"• Lucro: R$ {financial['profit']:,.2f}")
            response_parts.append(f"• Margem: {financial['profit_margin']:.1f}%")
            
            if business_context["insights"]:
                response_parts.append(f"\n**Insights Importantes:**")
                for insight in business_context["insights"]:
                    response_parts.append(f"• {insight}")
        
        response_parts.append("\n**Como posso ajudar mais?** Pode me perguntar sobre:")
        response_parts.append("• Técnicas de plantio e manejo")
        response_parts.append("• Análise financeira da sua produção")
        response_parts.append("• Solução de problemas na lavoura")
        response_parts.append("• Melhoria de qualidade e produtividade")
        
        return "\n".join(response_parts)

# ================================
# CLASSES DE SUPORTE (MANTIDAS)
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
                return None
        except Exception:
            return None

class EmbrapaAPI:
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
            url = f"{self.base_url}/_search/template"
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            return response.json() if response.status_code == 200 else {"error": f"Erro {response.status_code}"}
        except Exception as e:
            return {"error": f"Erro de conexão: {str(e)}"}

class AgroDatabase:
    def __init__(self):
        self.config = DB_CONFIG
    
    def get_connection(self):
        try:
            return psycopg2.connect(**self.config)
        except Exception as e:
            st.error(f"❌ Erro ao conectar com o banco: {str(e)}")
            return None
    
    def load_productions(self):
        conn = self.get_connection()
        if conn is None:
            return pd.DataFrame()
        try:
            query = "SELECT * FROM productions ORDER BY date DESC"
            df = pd.read_sql_query(query, conn)
            return df
        except Exception:
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
        except Exception:
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
        except Exception:
            return pd.DataFrame()
        finally:
            conn.close()

# ================================
# INTERFACE PRINCIPAL
# ================================
def main():
    # Inicializar assistente
    if "assistant" not in st.session_state:
        st.session_state.assistant = AgroIntelligentAssistant()
    
    assistant = st.session_state.assistant
    
    # Header
    st.markdown('<h1 class="main-header">🧠 AgroAssistente IA</h1>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; color: #666; margin-bottom: 2rem;">Sistema Inteligente Integrado - Embrapa + Seus Dados</div>', unsafe_allow_html=True)
    
    # Layout principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Área de conversação
        st.markdown("### 💬 Conversa com o Especialista Agrícola")
        
        # Exibir histórico de conversa
        for message in assistant.conversation_history[-10:]:  # Últimas 10 mensagens
            st.markdown(f'<div class="user-message"><strong>Você:</strong> {message["user"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="assistant-message"><strong>Assistente:</strong> {message["assistant"]}</div>', unsafe_allow_html=True)
        
        # Input do usuário
        user_input = st.text_area(
            "**Faça sua pergunta sobre agricultura:**",
            placeholder="Ex: Como melhorar minha produtividade? Qual adubo usar? Analise meus custos...",
            height=100
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 Enviar Pergunta", use_container_width=True):
                if user_input.strip():
                    with st.spinner("🤔 Analisando sua pergunta com IA..."):
                        response = assistant.generate_intelligent_response(user_input)
                        st.rerun()
                else:
                    st.warning("Por favor, digite uma pergunta")
        
        with col_btn2:
            if st.button("🔄 Nova Conversa", use_container_width=True):
                assistant.conversation_history = []
                st.rerun()
    
    with col2:
        # Sidebar com informações contextuais
        st.markdown("### 📊 Contexto do Seu Negócio")
        
        business_context = assistant.get_business_context()
        
        if business_context["has_data"]:
            financial = business_context["financial_summary"]
            
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("📦 Produção Total", f"{financial['total_production']:.0f} cx")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("💰 Receita Total", f"R$ {financial['total_revenue']:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("🎯 Lucro Líquido", f"R$ {financial['profit']:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("📈 Margem", f"{financial['profit_margin']:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Insights rápidos
            st.markdown("### 💡 Insights Rápidos")
            for insight in business_context["insights"][:3]:
                st.info(insight)
                
            # Cultura principal
            st.markdown(f"**🌱 Cultura Principal:** {business_context.get('main_crop', 'Não identificada')}")
            
        else:
            st.info("💼 **Cadastre seus dados de produção** para análises personalizadas")
            st.markdown("""
            Com seus dados, posso ajudar com:
            • Análises financeiras precisas
            • Recomendações específicas
            • Acompanhamento de produtividade
            • Otimização de custos
            """)
        
        # Status do sistema
        st.markdown("---")
        st.markdown("### 🔧 Status do Sistema")
        
        # Testar conexão Embrapa
        if assistant.embrapa_api.ensure_valid_token():
            st.success("✅ API Embrapa: Conectada")
        else:
            st.error("❌ API Embrapa: Desconectada")
        
        # Testar conexão Banco
        conn = assistant.db.get_connection()
        if conn:
            st.success("✅ Banco de Dados: Conectado")
            conn.close()
        else:
            st.error("❌ Banco de Dados: Desconectado")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    <p>🚀 <strong>AGROASSISTENTE IA</strong> - Conhecimento Científico Embrapa + Análise de Dados em Tempo Real</p>
    <p>💡 Dica: Pergunte sobre técnicas, finanças, problemas ou análises do seu negócio</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
