import streamlit as st
import re
import datetime
import time
import pandas as pd
import base64
import os
from zoneinfo import ZoneInfo
from fpdf import FPDF
import re
import speech_recognition as sr  
from audio_recorder_streamlit import audio_recorder
import google.generativeai as genai

from database import (
    verificar_login, 
    cadastrar_usuario, 
    verificar_email_existente, 
    atualizar_senha,
    obter_conexao,
    buscar_indicacao_por_humor,
    listar_humores_do_acervo
)

# --- 1. CONFIGURAÇÃO INICIAL E API GEMINI ---
st.set_page_config(page_title="Mia - Diário de Bem-Estar", page_icon="🌱", layout="wide")
FUSO_BR = ZoneInfo("America/Recife")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception:
    pass 

# --- 2. CÉREBRO DA MIA (GERANDO DICAS DINÂMICAS) ---
def limpar_texto(texto):
    return re.sub(r'[<>"{}]', '', texto).strip()[:500]

def detectar_risco_critico(texto):
    gatilhos = [
        "suicídio", "me matar", "morrer", "desistir", "autoextermínio",
        "não quero mais viver", "vontade de sumir", "acabar com tudo",
        "sem sentido", "tirar minha vida", "não aguento mais"
    ]
    return any(gatilho in texto.lower() for gatilho in gatilhos)

def analisar_desabafo_ia(texto_usuario, humor_selecionado):
    if detectar_risco_critico(texto_usuario):
        return "🚨 **Alerta de Cuidado:** Mia identificou que você está passando por um momento de extrema angústia. Por favor, ligue agora para o 188 (CVV). Você não está sozinho e existe ajuda gratuita."

    texto_sanitizado = limpar_texto(texto_usuario)

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Você é a Mia, assistente do aplicativo Help. 
        O usuário selecionou o humor '{humor_selecionado}' e escreveu o seguinte desabafo: "{texto_sanitizado}".
        
        Sua tarefa:
        1. Escreva uma frase curta, empática e muito humana validando o que ele está sentindo.
        2. Recomende 1 livro (ou leitura curta) e 1 música que combinem com esse estado de espírito para ajudá-lo hoje. NÃO REPITA sugestões clichês. Seja criativa.
        
        Formato obrigatório:
        **Mia:** [Sua frase empática]
        
        **Indicações Especiais para Hoje:**
        * 📚 [Livro/Leitura e o motivo em 1 linha]
        * 🎵 [Música/Artista e o motivo em 1 linha]
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    
    except Exception:
        sugestao_db = buscar_indicacao_por_humor(humor_selecionado)
        if sugestao_db:
            texto_dica = f"* 📚 {sugestao_db.get('livro_sugerido', '')}\n* 🎵 {sugestao_db.get('musica_sugerida', '')}"
        else:
            texto_dica = "* Respire fundo e ouça sons da natureza."
            
        return f"**(Modo Seguro Mia):** Entendo que as coisas podem estar difíceis. Para esse momento de {humor_selecionado}, separei isso do meu acervo:\n\n**Indicações:**\n{texto_dica}"

# --- 3. IMAGEM, ÁUDIO E CORES (CSS AJUSTADO PARA 50%) ---
def set_fundo_tela(image_file):
    """Fundo com imagem para a Landing Page e quadros reduzidos a 50%"""
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url(data:image/png;base64,{encoded_string});
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            /* Restringe o conteúdo principal para 50% da largura da tela */
            .main .block-container {{
                max-width: 50% !important;
            }}
            .caixa-branca {{
                background-color: rgba(255, 255, 255, 0.90);
                padding: 2.5rem;
                border-radius: 15px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                margin: auto;
            }}
            div[data-testid="stForm"] {{
                background-color: rgba(255, 255, 255, 0.95);
                padding: 2rem;
                border-radius: 10px;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

def set_fundo_cor_leve():
    """Fundo gradiente (Azul Bebê/Verde) sem imagem e layout 50% para o Diário"""
    st.markdown(
        """
        <style>
        .stApp {
            background-image: none !important;
            /* Junção de Azul Bebê com Verde Suave */
            background: linear-gradient(135deg, #E1F5FE 0%, #E8F5E9 100%) !important; 
        }
        /* Restringe o conteúdo principal (quadros) para 50% da largura da tela */
        .main .block-container {
            max-width: 50% !important;
            padding-top: 2rem;
        }
        .caixa-branca {
            background-color: #FFFFFF;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin: auto;
        }
        /* Ajuste nas bordas das caixas de texto */
        div[data-baseweb="textarea"] > div, div[data-baseweb="input"] > div {
            background-color: #FAFAFA !important; 
            border: 1px solid #B2DFDB !important;
            border-radius: 8px !important;
        }
        div[data-baseweb="textarea"] textarea {
            color: #2E7D32 !important;
            font-size: 15px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def processar_audio_web(bytes_audio):
    if bytes_audio:
        try:
            with open("temp_audio.wav", "wb") as f:
                f.write(bytes_audio)
            reconhecedor = sr.Recognizer()
            with sr.AudioFile("temp_audio.wav") as fonte:
                dados_audio = reconhecedor.record(fonte)
                return reconhecedor.recognize_google(dados_audio, language='pt-BR')
        except Exception:
            st.warning("⚠️ Áudio não compreendido. Tente falar um pouco mais perto.")
    return ""

# --- 4. FUNÇÕES DE BANCO E PDF ---

def gerar_pdf_pagina_bytes(reg):
    pdf = FPDF()
    pdf.add_page()
    
    # Use 'helvetica' (ou 'arial'), a fpdf2 gerencia o Unicode internamente
    # Sem precisar carregar arquivos .ttf externos
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Caderno Terapeutico Mia", ln=True, align="C")
    pdf.ln(4)
    
    pdf.set_font("helvetica", "", 10)
    texto_cabecalho = f"Data: {reg.get('data_f', '')} | Horario: {reg.get('hora_f', '')} | Humor: {reg.get('sentimento', '')}"
    pdf.cell(0, 6, texto_cabecalho, ln=True)
    
    pdf.line(10, 28, 200, 28)
    pdf.ln(6)
    
    # Se precisar de negrito em partes do texto
    for title, val in [("1. Como foi o dia hoje?", reg.get('como_foi_dia', '')), 
                       ("2. O que pode melhorar amanha?", reg.get('o_que_melhorar', '')), 
                       ("3. Desabafo Livre:", reg.get('desabafo_livre', ''))]:
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 8, title, ln=True)
        pdf.set_font("helvetica", "", 10)
        # Use o método multi_cell normalmente
        pdf.multi_cell(0, 6, str(val))
        pdf.ln(3)

    return pdf.output()

def salvar_caderno_completo(usuario_id, data, como_foi, melhorar, desabafo, sentimento, insight):
    conexao = obter_conexao()
    if not conexao: return False
    try:
        with conexao.cursor() as cursor:
            agora_br = datetime.datetime.now(FUSO_BR).strftime('%Y-%m-%d %H:%M:%S')
            data_str = data.strftime('%Y-%m-%d')
            sql = "INSERT INTO humores (usuario_id, data_desabafo, como_foi_dia, o_que_melhorar, desabafo_livre, sentimento, insight_ia, criado_em) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (usuario_id, data_str, como_foi, melhorar, desabafo, sentimento, insight, agora_br))
        conexao.commit()
        return True
    except Exception as e: return False
    finally:
        if conexao.open: conexao.close()

def carregar_relatorio_historico(usuario_id):
    conexao = obter_conexao()
    if not conexao: return []
    try:
        # Consulta intacta para manter a leitura funcionando perfeitamente
        with conexao.cursor() as cursor:
            cursor.execute("SELECT data_desabafo, como_foi_dia, o_que_melhorar, desabafo_livre, sentimento, insight_ia, criado_em FROM humores WHERE usuario_id = %s ORDER BY criado_em DESC", (usuario_id,))
            return cursor.fetchall()
    except Exception as e: 
        print(f"Erro ao carregar histórico: {e}")
        return []
    finally:
        if conexao.open: conexao.close()

def gerar_csv_indicacoes(registros):
    df = pd.DataFrame(registros)
    if not df.empty:
        df = df[['data_f', 'sentimento', 'insight_ia']].rename(columns={'data_f': 'Data', 'sentimento': 'Humor', 'insight_ia': 'Indicações'})
    return df.to_csv(index=False).encode('utf-8')

# --- 5. TELA INICIAL: APRESENTAÇÃO E NAVEGAÇÃO ---
def tela_entrada():
    set_fundo_tela("calmaria.jpeg.png")
    
    st.sidebar.title("Bem-vindo ao Help 🌱")
    menu = st.sidebar.radio("Navegação:", ["Conheça a Mia", "Fazer Login", "Criar Conta", "Recuperar Senha"])
    
    st.sidebar.divider()
    st.sidebar.info("Um espaço seguro para cuidar da sua mente.")

    if menu == "Conheça a Mia":
        st.markdown("""
        <div class='caixa-branca'>
            <h1 style='text-align: center; color: #1B5E20; font-family: Georgia, serif;'>Olá, eu sou a Mia! 🌿</h1>
            <h4 style='text-align: center; color: #388E3C; font-weight: normal;'>Sua assistente pessoal de bem-estar.</h4>
            <hr>
            <p style='font-size: 16px; color: #37474F; line-height: 1.6;'>
            O <b>Help</b> não é apenas um aplicativo; é um refúgio digital. Minha missão como Mia é te ouvir sem julgamentos, oferecer um espaço para você transbordar o que está no coração e organizar seus pensamentos.
            </p>
            <p style='font-size: 16px; color: #37474F; line-height: 1.6;'>
            <b>Por que escrever no diário faz a diferença?</b><br>
            Anotar seus sentimentos reduz a carga mental e diminui a ansiedade. Sempre que você fizer um registro, prepararei indicações sob medida para acolher exatamente a emoção que você está vivendo.
            </p>
            <p style='text-align: center; font-size: 16px; color: #2E7D32; font-weight: bold;'>
            👈 Acesse o menu lateral para iniciar sua jornada.
            </p>
        </div>
        """, unsafe_allow_html=True)

    elif menu == "Fazer Login":
        st.markdown("<div class='caixa-branca'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #1B5E20;'>🔐 Fazer Login</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            user = st.text_input("Usuário ou E-mail").strip()
            pw = st.text_input("Senha", type="password")
            if st.form_submit_button("Abrir Meu Diário", use_container_width=True):
                dados = verificar_login(user, pw)
                if dados:
                    st.session_state.auth_state = "logado"
                    st.session_state.usuario_id = dados['id']
                    st.session_state.usuario_nome = dados['nome']
                    st.rerun()
                else: st.error("Dados incorretos.")
        st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "Criar Conta":
        st.markdown("<div class='caixa-branca'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #1B5E20;'>🌱 Nova Conta</h2>", unsafe_allow_html=True)
        with st.form("cadastro_form"):
            new_user = st.text_input("Como quer ser chamado?").strip()
            new_email = st.text_input("Seu melhor e-mail").strip()
            new_pw = st.text_input("Crie uma senha (mín. 8 chars)", type="password")
            conf_pw = st.text_input("Confirme a senha", type="password")
            if st.form_submit_button("Eternizar Cadastro", use_container_width=True):
                if new_pw == conf_pw and re.match(r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$', new_email.lower()) and len(new_pw) >= 8:
                    if cadastrar_usuario(new_user, new_email, new_pw):
                        st.success("Sua conta foi aberta com sucesso! Vá para Fazer Login.")
                else: st.error("Valide se os campos atendem os critérios de segurança.")
        st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "Recuperar Senha":
        st.markdown("<div class='caixa-branca'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #1B5E20;'>🔑 Recuperar Acesso</h2>", unsafe_allow_html=True)
        with st.form("rec_form"):
            email = st.text_input("E-mail cadastrado").strip()
            nova_pw = st.text_input("Nova Senha", type="password")
            conf_pw = st.text_input("Confirme a Nova Senha", type="password")
            if st.form_submit_button("Redefinir Senha", use_container_width=True):
                if verificar_email_existente(email) and nova_pw == conf_pw and len(nova_pw) >= 8:
                    if atualizar_senha(email, nova_pw):
                        st.success("Sua senha foi renovada! Vá para Fazer Login.")
                else: st.error("Erro nos dados fornecidos para redefinição.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. INTERFACE PRINCIPAL (DIÁRIO LOGADO) ---
def tela_principal_mia():
    # Remove imagem e aplica gradiente azul/verde e reduz layout para 50%
    set_fundo_cor_leve()
    
    st.sidebar.title("🌿 Meu Refúgio")
    st.sidebar.markdown(f"👤 **Usuário:** `{st.session_state.usuario_nome}`")
    st.sidebar.markdown(f"📅 **Hoje:** {datetime.datetime.now(FUSO_BR).strftime('%d/%m/%Y')}")
    st.sidebar.divider()
    
    if st.sidebar.button("📞 Preciso de Apoio (CVV 188)", use_container_width=True):
        st.sidebar.warning("Você não está sozinho. Ligue 188 (Gratuito).")
    if st.sidebar.button("🔒 Fechar Diário", use_container_width=True):
        st.session_state.clear()
        st.rerun()
        
    st.markdown("<h1 style='text-align: center; color: #1B5E20; margin-bottom: 0px;'>Diário Mia</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #2E7D32; font-weight:normal; font-size: 15px;'>Um espaço seguro para desacelerar, respirar e registrar a sua mente.</p>", unsafe_allow_html=True)
    st.divider()

    aba_caderno, aba_relatorio = st.tabs(["✍️ Escrever no Diário", "📖 Ler Meu Caderno"])
    
    with aba_caderno:
        st.markdown("<div class='caixa-branca'>", unsafe_allow_html=True)
        for chave in ["input_dia", "input_melhorar", "input_livre", "last_audio_dia", "last_audio_mel", "last_audio_liv"]:
            if chave not in st.session_state: st.session_state[chave] = "" if "input" in chave else None

        if st.session_state.get('modo_sucesso'):
            st.success("Sua página foi guardada com segurança no banco de dados. 📖")
            st.info(st.session_state.ultimo_insight)
            if st.button("Nova Página em Branco", type="primary", use_container_width=True):
                for k in ["input_dia", "input_melhorar", "input_livre", "last_audio_dia", "last_audio_mel", "last_audio_liv"]:
                    st.session_state[k] = "" if "input" in k else None
                st.session_state.modo_sucesso = False
                st.rerun()
        else:
            try: humores_banco = listar_humores_do_acervo()
            except Exception: humores_banco = ["Triste", "Feliz", "Ansioso", "Cansado"]

            humor_selecionado = st.selectbox("🎭 Meu estado de espírito agora:", ["-- Selecione --"] + humores_banco)
            data_caderno = st.date_input("📅 Data do Registro:", datetime.date.today())
            st.divider()
            
            # --- CAMPO 1 ---
            col1, col2 = st.columns([0.8, 0.2], gap="small")
            with col1: st.markdown("<h4 style='color: #2E7D32; font-size: 18px;'>1. Como foi seu dia?</h4>", unsafe_allow_html=True)
            with col2:
                audio_dia = audio_recorder(text="🎙️ Gravar", recording_color="#D32F2F", neutral_color="#4CAF50", icon_size="1x", key="rec_dia")
                if audio_dia and audio_dia != st.session_state.last_audio_dia:
                    st.session_state.last_audio_dia = audio_dia
                    with st.spinner("⏳"):
                        texto = processar_audio_web(audio_dia)
                        if texto:
                            st.session_state["input_dia"] = (st.session_state["input_dia"] + " " + texto).strip()
                            st.rerun()
            st.text_area("Resumo:", key="input_dia", label_visibility="collapsed", height=50)
            st.write("") 

            # --- CAMPO 2 ---
            col3, col4 = st.columns([0.8, 0.2], gap="small")
            with col3: st.markdown("<h4 style='color: #2E7D32; font-size: 18px;'>2. O que pode melhorar?</h4>", unsafe_allow_html=True)
            with col4:
                audio_mel = audio_recorder(text="🎙️ Gravar", recording_color="#D32F2F", neutral_color="#4CAF50", icon_size="1x", key="rec_mel")
                if audio_mel and audio_mel != st.session_state.last_audio_mel:
                    st.session_state.last_audio_mel = audio_mel
                    with st.spinner("⏳"):
                        texto = processar_audio_web(audio_mel)
                        if texto:
                            st.session_state["input_melhorar"] = (st.session_state["input_melhorar"] + " " + texto).strip()
                            st.rerun()
            st.text_area("Ações:", key="input_melhorar", label_visibility="collapsed", height=50)
            st.write("") 

            # --- CAMPO 3 ---
            col5, col6 = st.columns([0.8, 0.2], gap="small")
            with col5: st.markdown("<h4 style='color: #2E7D32; font-size: 18px;'>3. Espaço Livre (Desabafo)</h4>", unsafe_allow_html=True)
            with col6:
                audio_liv = audio_recorder(text="🎙️ Gravar", recording_color="#D32F2F", neutral_color="#4CAF50", icon_size="1x", key="rec_liv")
                if audio_liv and audio_liv != st.session_state.last_audio_liv:
                    st.session_state.last_audio_liv = audio_liv
                    with st.spinner("⏳"):
                        texto = processar_audio_web(audio_liv)
                        if texto:
                            st.session_state["input_livre"] = (st.session_state["input_livre"] + " " + texto).strip()
                            st.rerun()
            st.text_area("Desabafo:", key="input_livre", label_visibility="collapsed", height=75)
            
            st.divider()
            
            # --- SALVAR E CONECTAR COM A MIA ---
            if st.button("💾 Fechar Página e Analisar com Mia", type="primary", use_container_width=True):
                dia_input = st.session_state["input_dia"].strip()
                melhorar_input = st.session_state["input_melhorar"].strip()
                livre_input = st.session_state["input_livre"].strip()
                texto_completo = f"{dia_input} {melhorar_input} {livre_input}"
                
                if humor_selecionado == "-- Selecione --":
                    st.error("Por favor, selecione seu estado de espírito no início da página.")
                elif texto_completo.strip():
                    with st.status("Mia está lendo seu caderno...", expanded=True) as status:
                        insight_gerado = analisar_desabafo_ia(texto_completo, humor_selecionado)
                        
                        if salvar_caderno_completo(st.session_state.usuario_id, data_caderno, dia_input, melhorar_input, livre_input, humor_selecionado, insight_gerado):
                            status.update(label="Caderno salvo com sucesso!", state="complete", expanded=False)
                            st.session_state.ultimo_insight = insight_gerado
                            st.session_state.modo_sucesso = True
                            st.rerun()
                        else:
                            status.update(label="Falha de conexão", state="error")
                            st.error("Erro crítico ao gravar os dados na nuvem MySQL.")
                else:
                    st.warning("Escreva ao menos uma palavra no seu diário para a Mia analisar.")
        st.markdown("</div>", unsafe_allow_html=True)

    with aba_relatorio:
        st.markdown("<div class='caixa-branca'>", unsafe_allow_html=True)
        registros = carregar_relatorio_historico(st.session_state.usuario_id)
        if registros:
            for r in registros:
                try:
                    r['data_f'] = pd.to_datetime(r['data_desabafo']).strftime('%d/%m/%Y')
                    r['hora_f'] = pd.to_datetime(r['criado_em']).strftime('%H:%M:%S')
                except Exception:
                    r['data_f'] = str(r['data_desabafo'])
                    r['hora_f'] = str(r['criado_em'])

            st.download_button("📊 Baixar Acervo Completo (CSV)", data=gerar_csv_indicacoes(registros), file_name="historico_mia.csv", mime="text/csv", use_container_width=True)
            st.divider()

            opcoes = {f"📅 {r['data_f']} às {r['hora_f']} - Humor: {r['sentimento']}": r for r in registros}
            sel = st.selectbox("📖 Escolha uma página do passado para reler:", list(opcoes.keys()))
            
            if sel:
                reg = opcoes[sel]
                st.info(f"**Data:** {reg['data_f']} | 🕒 {reg['hora_f']} | 🎭 **{reg['sentimento']}**")
                if reg['como_foi_dia']: st.write(f"**Meu dia:**\n{reg['como_foi_dia']}")
                if reg['o_que_melhorar']: st.write(f"**Para melhorar:**\n{reg['o_que_melhorar']}")
                if reg['desabafo_livre']: st.write(f"**Desabafo:**\n{reg['desabafo_livre']}")
                if reg['insight_ia']: st.markdown(f"{reg['insight_ia'].replace('**', '')}")
                
                st.download_button("📥 Exportar PDF", data=gerar_pdf_pagina_bytes(reg), file_name=f"diario.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.info("O seu diário ainda não possui folhas escritas.")
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    if 'auth_state' not in st.session_state: st.session_state.auth_state = "deslogado"
    
    if st.session_state.auth_state == "logado":
        tela_principal_mia()
    else:
        tela_entrada()