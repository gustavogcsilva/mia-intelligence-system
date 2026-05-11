import streamlit as st
import pandas as pd
import base64
from datetime import date, datetime
from streamlit_mic_recorder import speech_to_text
from mia_logic import analisar_desabafo_ia
from database import (
    salvar_diario,
    salvar_humor_atual,
    buscar_recomendacao_no_banco,
    buscar_dados_relatorio,
    salvar_desabafo_imediato
)
from relatorios import gerar_pdf_completo

# --- ESTILO E SEGURANÇA ---
def configurar_estilo_geral(caminho_imagem):
    try:
        with open(caminho_imagem, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{data}");
                background-size: cover;
                background-attachment: fixed;
            }}
            .stApp::before {{
                content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                background-color: rgba(255, 255, 255, 0.92); z-index: -1;
            }}
            .panic-button {{
                background-color: #ff4b4b !important;
                color: white !important;
                padding: 15px;
                border-radius: 12px;
                text-align: center;
                font-weight: bold;
                text-decoration: none;
                display: block;
                margin-bottom: 25px;
                border: 2px solid #b22222;
                box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
            }}
            </style>
        """, unsafe_allow_html=True)
    except Exception:
        st.warning("⚠️ Interface simplificada (Background não encontrado).")

def detectar_risco_critico(texto):
    gatilhos = ["suicídio", "me matar", "morrer", "desistir", "autoextermínio"]
    return any(palavra in texto.lower() for palavra in gatilhos)

# --- TELA PRINCIPAL ---
def tela_principal_acompanhamento():
    configurar_estilo_geral("campo.jpeg.png")

    if "usuario_id" not in st.session_state:
        st.error("⚠️ Sessão expirada. Faça login novamente.")
        st.stop()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Painel Mia")
        st.markdown(f"👤 **{st.session_state.usuario_nome}**")
        st.markdown(f"📅 {date.today().strftime('%d/%m/%Y')}")
        st.divider()
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.markdown('<a href="tel:188" class="panic-button">🚨 AJUDA IMEDIATA? LIGUE CVV 188</a>', unsafe_allow_html=True)
    st.title("🌟 Espaço Mia")

    # --- 1. SELEÇÃO DE HUMOR (ESSENCIAL PARA O FILTRO) ---
    st.subheader(" Como você definiria seu estado agora?")
    col_f, col_t, col_a, col_s, col_r = st.columns(5)
    
    with col_f:
        if st.button("😊 Feliz", use_container_width=True): st.session_state.humor_selecionado = "FELIZ"
    with col_t:
        if st.button("😢 Triste", use_container_width=True): st.session_state.humor_selecionado = "TRISTE"
    with col_a:
        if st.button("😰 Ansioso", use_container_width=True): st.session_state.humor_selecionado = "ANSIOSO"
    with col_s:
        if st.button("🤯 Sobrecarga", use_container_width=True): st.session_state.humor_selecionado = "SOBRECARREGADO"
    with col_r:
        if st.button("😡 Raiva", use_container_width=True): st.session_state.humor_selecionado = "RAIVA"

    if "humor_selecionado" in st.session_state:
        st.info(f"Estado selecionado: **{st.session_state.humor_selecionado}**")

    # --- 2. MEU DIÁRIO ---
    st.divider()
    st.subheader("📝 Meu Diário de Hoje")
    data_registro = st.date_input("Data do registro:", date.today())
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🌤️ Como foi o dia?**")
        v_res = speech_to_text(language='pt-BR', start_prompt="🎤 Voz", key='v_res')
        resumo_dia = st.text_area("Relato", value=v_res or "", placeholder="Hoje eu...", height=100)
    
    with c2:
        st.markdown("**⛈️ Desafios?**")
        v_prob = speech_to_text(language='pt-BR', start_prompt="🎤 Voz", key='v_prob')
        problema_dia = st.text_area("O que incomodou?", value=v_prob or "", placeholder="Senti que...", height=100)

    # BOTÃO ÚNICO DE SALVAMENTO (REGRAS DE NEGÓCIO APLICADAS)
    if st.button("💾 Salvar Registro e Ouvir a Mia", use_container_width=True):
        if "humor_selecionado" not in st.session_state:
            st.warning("⚠️ Selecione um humor nos botões coloridos acima primeiro.")
        elif resumo_dia.strip() and problema_dia.strip():
            if detectar_risco_critico(resumo_dia) or detectar_risco_critico(problema_dia):
                st.error("🚨 Mia detectou risco elevado. Por favor, ligue 188.")
            else:
                # FILTRO RÍGIDO: Busca recomendação baseada no BOTÃO clicado
                humor_atual = st.session_state.humor_selecionado
                dica_banco = buscar_recomendacao_no_banco(humor_atual)
                indicacao = dica_banco['texto']
                
                if salvar_diario(st.session_state.usuario_id, resumo_dia, problema_dia, data_registro, indicacao):
                    st.success(f"✅ Registro salvo! Mia filtrou uma dica para seu estado de {humor_atual.lower()}.")
                    with st.chat_message("assistant"):
                        st.write(indicacao)
                        if dica_banco.get('link') and dica_banco['link'] != "#":
                            st.link_button("🔗 Ver Recurso", dica_banco['link'])
                    # Limpa para o próximo uso
                    del st.session_state.humor_selecionado
                else:
                    st.error("Erro ao salvar no banco.")
        else:
            st.warning("⚠️ Preencha os campos de texto.")

    # --- 3. RELATÓRIOS ---
    st.divider()
    st.subheader("📊 Exportar Relatórios (PDF)")
    c_d, c_s, c_m = st.columns(3)

    with c_d:
        if st.button("📄 PDF Hoje", use_container_width=True):
            dados = buscar_dados_relatorio(st.session_state.usuario_id, dias=0)
            if dados:
                pdf = gerar_pdf_completo(st.session_state.usuario_nome, dados, "Diário")
                st.download_button("📥 Baixar", pdf, f"Diario_{date.today()}.pdf", "application/pdf")
            else: st.warning("Sem dados.")

    with c_s:
        if st.button("📅 PDF Semanal", use_container_width=True):
            dados = buscar_dados_relatorio(st.session_state.usuario_id, dias=7)
            if dados:
                pdf = gerar_pdf_completo(st.session_state.usuario_nome, dados, "Semanal")
                st.download_button("📥 Baixar", pdf, "Semanal.pdf", "application/pdf")
            else: st.warning("Sem dados.")

    with c_m:
        if st.button("🗓️ PDF Mensal", use_container_width=True):
            dados = buscar_dados_relatorio(st.session_state.usuario_id, dias=30)
            if dados:
                pdf = gerar_pdf_completo(st.session_state.usuario_nome, dados, "Mensal")
                st.download_button("📥 Baixar", pdf, "Mensal.pdf", "application/pdf")
            else: st.warning("Sem dados.")

    # --- 4. ESPAÇO DO GRITO ---
    st.divider()
    st.subheader("🔊 Espaço do Desabafo (Grito)")
    
    st.markdown("_Às vezes, as palavras faladas libertam mais que as escritas. Use o microfone ou digite abaixo._")
    
    # Botão de transcrição de voz para o Grito
    v_grito = speech_to_text(
        language='pt-BR', 
        start_prompt="🎤 Falar meu desabafo", 
        stop_prompt="🛑 Parar de ouvir",
        key='v_grito'
    )

    # A área de texto recebe o valor da voz (se houver) ou o que for digitado
    grito_texto = st.text_area(
        "SOLTE TUDO AQUI:", 
        value=v_grito or "", 
        height=150, 
        placeholder="Sem filtros... Solte o que está no seu peito agora."
    )

    if st.button("💥 SOLTAR PESO", use_container_width=True):
        if grito_texto.strip():
            if not detectar_risco_critico(grito_texto):
                # Salva o desabafo no banco de dados
                salvar_desabafo_imediato(st.session_state.usuario_id, grito_texto)
                st.success("🔥 Energia solta! O peso foi deixado para trás.")
                
                # Mia analisa o sentimento do grito via IA
                with st.spinner("Mia está processando sua energia..."):
                    etiqueta = analisar_desabafo_ia(grito_texto)
                    dica = buscar_recomendacao_no_banco(etiqueta)
                
                # Exibe o insight da Mia
                st.info(f"**Dica rápida da Mia:** {dica['texto']}")
                
                if dica.get('link') and dica['link'] != "#":
                    st.link_button("🔗 Recurso de apoio", dica['link'])
            else:
                st.error("🚨 Mia detectou um nível de angústia muito elevado no seu desabafo. Por favor, não passe por isso sozinho. Ligue para o CVV no 188 ou procure um profissional agora.")
        else:
            st.warning("⚠️ O espaço está vazio. Escreva ou fale algo para soltar o peso.")