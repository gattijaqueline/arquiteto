# MIT License
#
# Copyright (c) 2026
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Aplicativo Streamlit: Extrator de Dados Inteligente (Azure OpenAI)
==================================================================
Integração com Microsoft Azure OpenAI Service utilizando a biblioteca oficial openai
e formatação garantida em JSON através de Structured Outputs (response_format).
"""

import json
import streamlit as st
from openai import AzureOpenAI

# -----------------------------------------------------------------------------
# 1. Configuração da Página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Extrator Inteligente | Azure AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. Gestão de Credenciais e Conexão (Secrets vs. Fallback)
# -----------------------------------------------------------------------------
# Valores padrão fornecidos (utilizados como fallback caso não haja secrets.toml)
DEFAULT_KEY = "6t2pTNsmNafDyo53MDAFIrvvQRBZXP7dLcr5j3TLxMS34LQVq3ZUJQQJ99CHACHYHv6XJ3w3AAAAACOGT7os"
DEFAULT_ENDPOINT = "[https://marcelomaffeis-05082026-resource.services.ai.azure.com/](https://marcelomaffeis-05082026-resource.services.ai.azure.com/)"
DEFAULT_DEPLOYMENT = "gpt-4.1-mini"

# Prioriza st.secrets; se não encontrar, utiliza os fallbacks
api_key = st.secrets.get("AZURE_OPENAI_API_KEY", DEFAULT_KEY)
raw_endpoint = st.secrets.get("AZURE_OPENAI_ENDPOINT", DEFAULT_ENDPOINT)
deployment_name = st.secrets.get("AZURE_OPENAI_DEPLOYMENT", DEFAULT_DEPLOYMENT)

# Normalização do Endpoint para remover aspas residuais e barras extras
endpoint = raw_endpoint.strip().rstrip('&quot;').rstrip('"').rstrip("'")

@st.cache_resource(show_spinner=False)
def get_azure_client(key: str, ep: str) -> AzureOpenAI:
    """
    Inicializa o cliente AzureOpenAI em cache para otimizar 
    tempo de resposta e reutilização de conexões HTTP/TCP.
    """
    return AzureOpenAI(
        api_key=key,
        api_version="2024-06-01",
        azure_endpoint=ep
    )

# -----------------------------------------------------------------------------
# 3. Interface Visual do Usuário (UI)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0078D4; /* Azure Microsoft Blue */
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #555555;
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="main-header">⚡ Extrator de Dados Inteligente</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Análise textual, extração de entidades, urgência e sentimento via Azure OpenAI.</div>', unsafe_allow_html=True)

# Barra lateral com telemetria e documentação
with st.sidebar:
    st.subheader("⚙️ Configurações do Ambiente")
    st.markdown(f"**Deployment:** `{deployment_name}`")
    st.markdown(f"**Endpoint:** `{endpoint}`")
    st.caption("As credenciais podem ser desacopladas definindo `.streamlit/secrets.toml` localmente.")
    st.divider()
    st.info("💡 **Dica de uso:** Cole e-mails, atas de reuniões, mensagens de clientes ou relatórios para extrair informações instantaneamente.")

# Entrada de dados do usuário
user_text = st.text_area(
    "Insira o texto que deseja processar:",
    placeholder="Ex.: Olá equipe, aqui é a Mariana do Financeiro. O Roberto enviou o contrato final, mas faltam as assinaturas da diretoria. Precisamos resolver isso hoje com prioridade máxima!",
    height=160
)

col_action, _ = st.columns([1, 4])
with col_action:
    btn_processar = st.button("🚀 Processar", use_container_width=True, type="primary")

# -----------------------------------------------------------------------------
# 4. Processamento com Engenharia de Prompt e Azure OpenAI
# -----------------------------------------------------------------------------
if btn_processar:
    if not user_text.strip():
        st.warning("⚠️ Por favor, insira um texto antes de clicar em Processar.")
    else:
        # Instrução de Sistema rígida para garantia de contrato de saída (JSON)
        system_instruction = (
            "Você é um arquiteto especialista em processamento de linguagem natural e extração estruturada de dados.\n"
            "Analise criticamente o texto fornecido pelo usuário e retorne ESTRITAMENTE um objeto JSON válido "
            "com exatamente as seguintes chaves:\n"
            "{\n"
            '  "sentimento": "Positivo" | "Neutro" | "Negativo",\n'
            '  "porcentagem_sentimento": float entre 0.0 e 100.0 (nível de intensidade ou confiança do sentimento),\n'
            '  "assunto_principal": "Descrição concisa em uma frase sobre o tema central",\n'
            '  "pessoas_citadas": ["Nome Completo ou Primeiro Nome"],\n'
            '  "nivel_de_urgencia": "Baixo" | "Medio" | "Alto"\n'
            "}\n"
            "Não adicione nenhum texto introdutório, explicações ou blocos de formatação markdown. Retorne apenas o JSON bruto."
        )

        try:
            with st.spinner("Consultando Azure OpenAI Service..."):
                client = get_azure_client(api_key, endpoint)
                
                # Chamada com resposta JSON forçada pelo motor do modelo
                response = client.chat.completions.create(
                    model=deployment_name,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_text}
                    ],
                    temperature=0.1
                )
                
                raw_content = response.choices[0].message.content
                data = json.loads(raw_content)

            st.success("✅ Extração concluída com sucesso!")
            st.divider()

            # -----------------------------------------------------------------
            # 5. Exibição Estruturada dos Resultados
            # -----------------------------------------------------------------
            st.subheader("📊 Métricas e Resultados")

            col1, col2, col3 = st.columns(3)
            
            sentimento = data.get("sentimento", "N/D")
            porcentagem = data.get("porcentagem_sentimento", 0)
            urgencia = data.get("nivel_de_urgencia", "N/D")
            pessoas = data.get("pessoas_citadas", [])

            with col1:
                st.metric(
                    label="Sentimento",
                    value=sentimento,
                    delta=f"{porcentagem:.1f}% de intensidade"
                )

            with col2:
                st.metric(
                    label="Nível de Urgência",
                    value=urgencia
                )

            with col3:
                st.metric(
                    label="Pessoas Citadas",
                    value=len(pessoas)
                )

            # Detalhes de Assunto e Pessoas
            c_left, c_right = st.columns([3, 2])
            
            with c_left:
                st.markdown("#### 🎯 Assunto Principal")
                st.info(data.get("assunto_principal", "Não identificado"))

            with c_right:
                st.markdown("#### 👥 Pessoas Identificadas")
                if pessoas:
                    for pessoa in pessoas:
                        st.markdown(f"- 👤 **{pessoa}**")
                else:
                    st.caption("Nenhum nome próprio identificado no texto.")

            # Payload Bruto
            with st.expander("🔍 Inspecionar Payload JSON Bruto", expanded=False):
                st.json(data)

        except json.JSONDecodeError as jde:
            st.error(f"Erro ao converter a resposta em JSON: {jde}")
            if "raw_content" in locals():
                st.code(raw_content, language="json")
        except Exception as e:
            st.error(f"Falha na comunicação com o Azure OpenAI: {str(e)}")
