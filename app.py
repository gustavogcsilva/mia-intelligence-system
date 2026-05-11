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

# --- CONFIGURAÇÃO INICIAL (DEVE SER A PRIMEIRA COISA) ---
st.set_page_config(page_title="Mia - Bem Estar", page_icon=":D", layout="centered")

# --- 1. FUNÇÃO DE ESTILO ---
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
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    return bool(re.match(regex, email.lower()))

# --- 3. TELAS DE AUTENTICAÇÃO ---

def tela_login():
    configurar_estilo_autenticacao("campo.jpeg.png")
    st.markdown("<h1 style='color: white; text-align: center;'>🔐 Login Mia</h1>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        user = st.text_input("Usuário ou E-mail").strip()
        pw = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar", use_container_width=True)
        
        if entrar:
            if user and pw:
                dados_usuario = verificar_login(user, pw)
                if dados_usuario:
                    st.session_state.auth_state = "logado"
                    st.session_state.usuario_id = dados_usuario['id']
                    st.session_state.usuario_nome = dados_usuario['nome']
                    st.success("Login realizado!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    time.sleep(0.5)
                    st.error("Credenciais inválidas.")
            else:
                st.error("Preencha os campos.")

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
    
    with st.form("cadastro_form"):
        new_user = st.text_input("Nome de Usuário").strip()
        new_email = st.text_input("E-mail").strip()
        new_pw = st.text_input("Senha (mín. 8 caracteres)", type="password")
        conf_pw = st.text_input("Confirme a Senha", type="password")
        cadastrar = st.form_submit_button("Finalizar Cadastro", use_container_width=True)

        if cadastrar:
            if not new_user or not new_email or not new_pw:
                st.error("Preencha todos os campos.")
            elif not validar_email(new_email):
                st.error("E-mail inválido.")
            elif len(new_pw) < 8:
                st.error("Mínimo 8 caracteres.")
            elif new_pw != conf_pw:
                st.error("Senhas não coincidem.")
            else:
                sucesso = cadastrar_usuario(new_user, new_email, new_pw)
                if sucesso == True:
                    st.success("Conta criada! Redirecionando...")
                    time.sleep(1)
                    st.session_state.auth_state = "login"
                    st.rerun()
                elif sucesso == "existe":
                    st.warning("Usuário/E-mail já existe.")
                else:
                    st.error("Erro no servidor.")
    
    if st.button("Voltar ao Login"):
        st.session_state.auth_state = "login"
        st.rerun()

def tela_recuperacao():
    configurar_estilo_autenticacao("campo.jpeg.png")
    st.markdown("<h1 style='color: white; text-align: center;'>🔑 Redefinir Senha</h1>", unsafe_allow_html=True)
    
    with st.form("recuperar_form"):
        email = st.text_input("E-mail cadastrado").strip()
        nova_pw = st.text_input("Nova Senha", type="password")
        conf_pw = st.text_input("Confirme a Nova Senha", type="password")
        enviar = st.form_submit_button("Redefinir Senha", use_container_width=True)

        if enviar:
            if not email or not nova_pw:
                st.error("Preencha todos os campos.")
            elif len(nova_pw) < 8:
                st.error("A nova senha deve ter 8+ caracteres.")
            elif nova_pw != conf_pw:
                st.error("Senhas não coincidem.")
            else:
                if verificar_email_existente(email):
                    if atualizar_senha(email, nova_pw):
                        st.success("Senha atualizada!")
                        time.sleep(1)
                        st.session_state.auth_state = "login"
                        st.rerun()
                else:
                    st.error("E-mail não encontrado.")
    
    if st.button("Cancelar"):
        st.session_state.auth_state = "login"
        st.rerun()

# --- 4. LÓGICA PRINCIPAL (MAIN) ---

def main():
    # Inicializa o estado de autenticação se não existir
    if 'auth_state' not in st.session_state:
        st.session_state.auth_state = "login"

    # Navegação entre telas
    if st.session_state.auth_state == "login":
        tela_login()
    elif st.session_state.auth_state == "cadastro":
        tela_cadastro()
    elif st.session_state.auth_state == "recuperacao":
        tela_recuperacao()
    elif st.session_state.auth_state == "logado":
        st.sidebar.success(f"Logado como: {st.session_state.usuario_nome}")
        if st.sidebar.button("Sair"):
            st.session_state.clear()
            st.rerun()
        
        # AQUI VOCÊ CHAMA SUA FUNÇÃO DO APP PRINCIPAL
        st.write(f"### Bem vindo ao painel principal, {st.session_state.usuario_nome}!")

if __name__ == "__main__":
    main()