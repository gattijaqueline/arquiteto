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
Extrator de Dados Inteligente - Microsoft Azure / Foundry
"""

import json
import traceback
import streamlit as st
from openai import AzureOpenAI, OpenAI

st.set_page_config(
    page_title="Extrator Inteligente | Azure AI",
    page_icon="⚡",
    layout="wide"
)

# -----------------------------------------------------------------------------
# Credenciais e Endpoint
# -----------------------------------------------------------------------------
DEFAULT_KEY = "6t2pTNsmNafDyo53MDAFIrvvQRBZXP7dLcr5j3TLxMS34LQVq3ZUJQQJ99CHACHYHv6XJ3w3AAAAACOGT7os"
DEFAULT_ENDPOINT = "https://marcelomaffeis-05082026-resource.services.ai.azure.com"
DEFAULT_DEPLOYMENT = "gpt-4.1-mini"

api_key = st.secrets.get("AZURE_OPENAI_API_KEY", DEFAULT_KEY).strip()
raw_endpoint = st.secrets.get("AZURE_OPENAI_ENDPOINT", DEFAULT_ENDPOINT)
deployment_name = st.secrets.get("AZURE_OPENAI_DEPLOYMENT", DEFAULT_DEPLOYMENT).strip()

# Limpeza rígida de endpoint
clean_endpoint = (
    str(raw_endpoint)
    .replace("&quot;", "")
    .replace('"', "")
    .replace("'", "")
    .strip()
    .rstrip("/")
)

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------
st.markdown("## ⚡ Extrator de Dados Inteligente (Microsoft AI)")
st.caption("Extração estruturada de entidades, urgência e sentimento.")

with st.sidebar:
    st.subheader("⚙️ Configurações Ativas")
    st.markdown(f"**Deployment / Modelo:** `{deployment_name}`")
    st.markdown(f"**Endpoint:**\n`{clean_endpoint}`")
    modo_conexao = st.radio(
        "Modo de Conexão:",
        ["AzureOpenAI Padrão", "Microsoft Foundry (OpenAI via /models)"],
        index=0
    )
    st.divider()
    st.caption("Se estiver em rede corporativa ou VPN, certifique-se de que a rota para o Azure não esteja bloqueada.")

user_text = st.text_area(
    "Insira o texto para processamento:",
    placeholder="Ex.: Olá, a entrega atrasou e o cliente está cobrando urgência. O Marcelo e a Fernanda já foram avisados.",
    height=150
)

if st.button("🚀 Processar", type="primary"):
    if not user_text.strip():
        st.warning("⚠️ Insira um texto para processamento.")
    else:
        system_instruction = (
            "Você é um analisador semântico. Analise o texto e retorne RIGOROSAMENTE apenas um JSON no formato:\n"
            "{\n"
            '  "sentimento": "Positivo" | "Neutro" | "Negativo",\n'
            '  "porcentagem_sentimento": float de 0 a 100,\n'
            '  "assunto_principal": "string concisa",\n'
            '  "pessoas_citadas": ["Nome 1"],\n'
            '  "nivel_de_urgencia": "Baixo" | "Medio" | "Alto"\n'
            "}\n"
            "Retorne apenas o JSON bruto sem markdown em volta."
        )

        try:
            with st.spinner("Conectando ao serviço da Microsoft..."):
                if modo_conexao == "AzureOpenAI Padrão":
                    client = AzureOpenAI(
                        api_key=api_key,
                        api_version="2024-06-01",
                        azure_endpoint=clean_endpoint,
                        timeout=20.0
                    )
                else:
                    # Conexão direta com Foundry Model Inference
                    client = OpenAI(
                        base_url=f"{clean_endpoint}/models",
                        api_key=api_key,
                        timeout=20.0
                    )

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

            st.success("✅ Processado com sucesso!")
            
            # Métricas
            col1, col2, col3 = st.columns(3)
            col1.metric("Sentimento", data.get("sentimento", "N/D"), f"{data.get('porcentagem_sentimento', 0):.1f}%")
            col2.metric("Nível de Urgência", data.get("nivel_de_urgencia", "N/D"))
            col3.metric("Pessoas Citadas", len(data.get("pessoas_citadas", [])))

            st.markdown(f"**🎯 Assunto:** {data.get('assunto_principal', 'N/D')}")
            st.markdown(f"**👥 Pessoas:** {', '.join(data.get('pessoas_citadas', [])) or 'Nenhuma citada'}")
            
            with st.expander("Ver JSON Completo"):
                st.json(data)

        except Exception as err:
            st.error(f"❌ Falha de Conexão: {err}")
            with st.expander("🛠️ Detalhes Técnicos do Erro (Traceback)", expanded=True):
                st.code(traceback.format_exc(), language="python")
                st.markdown(
                    """
                    **O que verificar:**
                    1. Troque o **Modo de Conexão** na barra lateral para testar a rota do Foundry (`/models`).
                    2. Verifique se o recurso do Azure ainda está ativo ou se a chave de acesso expirou.
                    3. Se estiver em rede corporativa/faculdade, teste conectando no 4G/roteador do celular para descartar bloqueio de firewall.
                    """
                )
