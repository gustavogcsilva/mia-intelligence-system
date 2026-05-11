import streamlit as st
import re
import base64
import time
from database import (
    verificar_login, 
    cadastrar_usuario, 
    verificar_email_existente, 
    atualizar_senha
)

# --- 1. FUNÇÃO DE ESTILO (MELHORADA) ---
def configurar_estilo_autenticacao(caminho_imagem):
    try:
        with open(caminho_imagem, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            /* Overlay para legibilidade */
            .stApp::before {{
                content: "";
                position: absolute;
                top: 0; left: 0; width: 100%; height: 100%;
                background-color: rgba(0, 0, 0, 0.5); 
                z-index: -1;
            }}
            [data-testid="stForm"] {{
                background-color: rgba(255, 255, 255, 0.98);
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.5);
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception:
        st.info("Nota: Fundo customizado não carregado.")

# --- 2. AUXILIARES ---
def validar_email(email):
    # Regex mais robusto para evitar caracteres maliciosos
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    return bool(re.match(regex, email.lower()))

# --- 3. TELAS ---

def tela_login():
    configurar_estilo_autenticacao("campo.jpeg.png")
    st.markdown("<h1 style='color: white; text-align: center;'>🔐 Login Mia</h1>", unsafe_allow_html=True)
    
    with st.form("login"):
        user = st.text_input("Usuário ou E-mail").strip()
        pw = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")
        
        if entrar:
            if user and pw:
                dados_usuario = verificar_login(user, pw)
                if dados_usuario:
                    st.session_state.auth_state = "logado"
                    st.session_state.usuario_id = dados_usuario['id']
                    st.session_state.usuario_nome = dados_usuario['nome']
                    st.success("Login realizado!")
                    time.sleep(0.5) # Experiência de usuário fluida
                    st.rerun()
                else:
                    time.sleep(1) # Anti-brute force: atrasa resposta de erro
                    st.error("Credenciais inválidas.")
            else:
                st.error("Campos obrigatórios vazios.")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✨ Criar Conta", use_container_width=True):
            st.session_state.auth_state = "cadastro"
            st.rerun()
    with col2:
        if st.button("🔑 Esqueci Senha", use_container_width=True):
            st.session_state.auth_state = "recuperacao"
            st.rerun()

def tela_cadastro():
    configurar_estilo_autenticacao("campo.jpeg.png")
    st.markdown("<h1 style='color: white; text-align: center;'>🌱 Cadastro Mia</h1>", unsafe_allow_html=True)
    
    with st.form("cadastro"):
        new_user = st.text_input("Nome de Usuário").strip()
        new_email = st.text_input("E-mail").strip()
        new_pw = st.text_input("Senha (mín. 8 caracteres)", type="password")
        conf_pw = st.text_input("Confirme a Senha", type="password")
        
        cadastrar = st.form_submit_button("Finalizar Cadastro")

        if cadastrar:
            if not new_user or not new_email or not new_pw:
                st.error("Preencha todos os campos.")
            elif not validar_email(new_email):
                st.error("E-mail inválido.")
            elif len(new_pw) < 8:
                st.error("A senha deve ter pelo menos 8 caracteres.")
            elif new_pw != conf_pw:
                st.error("Senhas não coincidem.")
            else:
                sucesso = cadastrar_usuario(new_user, new_email, new_pw)
                if sucesso == True:
                    st.success("Conta criada! Redirecionando...")
                    time.sleep(2)
                    st.session_state.auth_state = "login"
                    st.rerun()
                elif sucesso == "existe":
                    st.warning("Usuário ou e-mail já cadastrado.")
                else:
                    st.error("Erro interno. Tente novamente.")
    
    if st.button("Voltar ao Login"):
        st.session_state.auth_state = "login"
        st.rerun()

def tela_recuperacao():
    configurar_estilo_autenticacao("campo.jpeg.png")
    st.markdown("<h1 style='color: white; text-align: center;'>🔑 Redefinir Senha</h1>", unsafe_allow_html=True)
    
    with st.form("recuperar_senha"):
        email = st.text_input("E-mail cadastrado").strip()
        nova_pw = st.text_input("Nova Senha", type="password")
        conf_pw = st.text_input("Confirme a Nova Senha", type="password")
        enviar = st.form_submit_button("Redefinir Senha")

        if enviar:
            if not email or not nova_pw:
                st.error("Preencha todos os campos.")
            elif len(nova_pw) < 8:
                st.error("A nova senha deve ter 8+ caracteres.")
            elif nova_pw != conf_pw:
                st.error("Senhas não coincidem.")
            else:
                # Segurança: Verificamos se o e-mail existe antes
                if verificar_email_existente(email):
                    if atualizar_senha(email, nova_pw):
                        st.success("Senha atualizada!")
                        time.sleep(1)
                        st.session_state.auth_state = "login"
                        st.rerun()
                else:
                    # Mensagem genérica para evitar enumeração de usuários
                    st.error("Não foi possível processar a solicitação para este e-mail.")
    
    if st.button("Cancelar"):
        st.session_state.auth_state = "login"
        st.rerun()