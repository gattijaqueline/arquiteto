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

Configuração Segura (.streamlit/secrets.toml):
----------------------------------------------
Crie a pasta `.streamlit` e dentro dela o arquivo `secrets.toml`:

    AZURE_OPENAI_API_KEY = "sua_chave_aqui"
    AZURE_OPENAI_ENDPOINT = "[https://seu-recurso.services.ai.azure.com](https://seu-recurso.services.ai.azure.com)"
    AZURE_OPENAI_DEPLOYMENT = "gpt-4.1-mini"
"""

import json
import streamlit as st
from openai import AzureOpenAI

# -----------------------------------------------------------------------------
# 1. Configurações da Página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Extrator Inteligente | Azure AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. Tratamento Robusto de Credenciais e Endpoint
# -----------------------------------------------------------------------------
DEFAULT_KEY = "6t2pTNsmNafDyo53MDAFIrvvQRBZXP7dLcr5j3TLxMS34LQVq3ZUJQQJ99CHACHYHv6XJ3w3AAAAACOGT7os"
DEFAULT_ENDPOINT = "[https://marcelomaffeis-05082026-resource.services.ai.azure.com](https://marcelomaffeis-05082026-resource.services.ai.azure.com)"
DEFAULT_DEPLOYMENT = "gpt-4.1-mini"

# Obtém credenciais (secrets.toml tem prioridade sobre os padrões)
api_key = st.secrets.get("AZURE_OPENAI_API_KEY", DEFAULT_KEY).strip()
raw_endpoint = st.secrets.get("AZURE_OPENAI_ENDPOINT", DEFAULT_ENDPOINT)
deployment_name = st.secrets.get("AZURE_OPENAI_DEPLOYMENT", DEFAULT_DEPLOYMENT).strip()

# Sanitização estrita do endpoint: remove entidades HTML (&quot;), aspas e barras finais
endpoint = (
    str(raw_endpoint)
    .replace("&quot;", "")
    .replace('"', "")
    .replace("'", "")
    .strip()
    .rstrip("/")
)

@st.cache_resource(show_spinner=False)
def get_azure_client(key: str, ep: str) -> AzureOpenAI:
    """Inicializa o cliente Azure OpenAI com timeout e versão de API estável."""
    return AzureOpenAI(
        api_key=key,
        api_version="2024-06-01",
        azure_endpoint=ep,
        timeout=30.0
    )

# -----------------------------------------------------------------------------
# 3. Interface do Usuário (UI)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0078D4;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4A4A4A;
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="main-title">⚡ Extrator de Dados Inteligente</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Extração automatizada de entidades, urgência e análise de sentimento via Azure OpenAI.</div>', unsafe_allow_html=True)

# Painel Lateral
with st.sidebar:
    st.subheader("⚙️ Infraestrutura Microsoft Azure")
    st.markdown(f"**Deployment:** `{deployment_name}`")
    st.markdown(f"**Endpoint Conectado:**\n`{endpoint}`")
    st.caption("Recomendado: utilize `.streamlit/secrets.toml` em ambientes de desenvolvimento e produção.")
    st.divider()
    st.markdown("💡 **Exemplos de entrada:** E-mails operacionais, chamados de suporte, atas de reunião ou reclamações de clientes.")

# Caixa de Entrada de Texto
user_text = st.text_area(
    "Insira o texto para análise:",
    placeholder="Ex.: Olá, a equipe de logística informou que a carga do fornecedor atrasou e os clientes estão cobrando uma posição urgente. O Carlos e a Mariana estão tentando contornar a situação, mas precisamos de aprovação imediata da diretoria!",
    height=170
)

col_action, _ = st.columns([1, 4])
with col_action:
    btn_processar = st.button("🚀 Processar", use_container_width=True, type="primary")

# -----------------------------------------------------------------------------
# 4. Processamento do Modelo e Extração em JSON
# -----------------------------------------------------------------------------
if btn_processar:
    if not user_text.strip():
        st.warning("⚠️ Por favor, digite ou cole um texto antes de processar.")
    else:
        system_instruction = (
            "Você é um arquiteto especialista em extração e processamento de linguagem natural.\n"
            "Analise criticamente o texto fornecido pelo usuário e retorne ESTRITAMENTE um objeto JSON válido "
            "com exatamente as seguintes chaves:\n"
            "{\n"
            '  "sentimento": "Positivo" | "Neutro" | "Negativo",\n'
            '  "porcentagem_sentimento": float entre 0.0 e 100.0 (confiança ou intensidade do sentimento detectado),\n'
            '  "assunto_principal": "Descrição concisa em uma frase sobre o tema principal do texto",\n'
            '  "pessoas_citadas": ["Nome 1", "Nome 2"],\n'
            '  "nivel_de_urgencia": "Baixo" | "Medio" | "Alto"\n'
            "}\n"
            "Importante: Não use formatações markdown em volta do JSON (como ```json). Retorne apenas o JSON bruto puro."
        )

        try:
            with st.spinner("Conectando ao Azure OpenAI e processando dados..."):
                client = get_azure_client(api_key, endpoint)

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
            st.subheader("📊 Resultados da Análise")

            # Métricas em colunas
            c1, c2, c3 = st.columns(3)

            sentimento = data.get("sentimento", "N/D")
            porcentagem = float(data.get("porcentagem_sentimento", 0.0))
            urgencia = data.get("nivel_de_urgencia", "N/D")
            pessoas = data.get("pessoas_citadas", [])

            with c1:
                st.metric(
                    label="Sentimento Detectado",
                    value=sentimento,
                    delta=f"{porcentagem:.1f}% de intensidade"
                )

            with c2:
                st.metric(
                    label="Nível de Urgência",
                    value=urgencia
                )

            with c3:
                st.metric(
                    label="Pessoas Citadas",
                    value=len(pessoas)
                )

            # Detalhamento de Assunto e Pessoas
            col_esq, col_dir = st.columns([3, 2])

            with col_esq:
                st.markdown("#### 🎯 Assunto Principal")
                st.info(data.get("assunto_principal", "Não identificado"))

            with col_dir:
                st.markdown("#### 👥 Pessoas Identificadas")
                if pessoas:
                    for p in pessoas:
                        st.markdown(f"- 👤 **{p}**")
                else:
                    st.caption("Nenhum nome citado no texto.")

            # Visão completa em JSON
            with st.expander("🔍 Visualizar Payload JSON Completo", expanded=False):
                st.json(data)

        except json.JSONDecodeError as jde:
            st.error(f"Erro ao interpretar a resposta JSON do modelo: {jde}")
            if "raw_content" in locals():
                st.code(raw_content, language="json")
        except Exception as e:
            st.error(f"Falha na comunicação com o Azure OpenAI: {str(e)}")
            st.info(
                "💡 **Dica de Solução de Problemas:**\n"
                "- Certifique-se de que o endpoint não contenha aspas ou barras extras.\n"
                "- Verifique se a sua rede corporativa ou VPN não está bloqueando requisições HTTPS para `services.ai.azure.com`.")
