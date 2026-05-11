import streamlit as st
import re
import base64
import time
import streamlit.components.v1 as components
from database import (
    verificar_login, 
    cadastrar_usuario, 
    verificar_email_existente, 
    atualizar_senha
)

# --- 1. CONFIGURAÇÃO INICIAL (OBRIGATÓRIO SER A PRIMEIRA LINHA) ---
st.set_page_config(page_title="Mia - Bem Estar", page_icon="🌱", layout="centered")

# --- 2. INJEÇÃO DE JAVASCRIPT (O SEU FOCO) ---
def injetar_js_interativo():
    """ Injeta scripts para melhorar a reatividade da interface """
    components.html(
        """
        <script>
        // Acessa o documento pai (fora do iframe do Streamlit)
        const doc = window.parent.document;
        
        // Efeito de feedback nos botões
        const botoes = doc.querySelectorAll('button');
        botoes.forEach(btn => {
            btn.addEventListener('click', () => {
                btn.style.transform = 'scale(0.95)';
                btn.style.transition = '0.2s';
                setTimeout(() => btn.style.transform = 'scale(1)', 200);
            });
        });

        // Exemplo de log no console para debug do desenvolvedor
        console.log("Interface da Mia carregada com sucesso.");
        </script>
        """,
        height=0
    )

# --- 3. ESTILIZAÇÃO CSS ---
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
                background-color: rgba(0, 0, 0, 0.4); 
                z-index: -1;
            }}
            [data-testid="stForm"] {{
                background-color: rgba(255, 255, 255, 0.95);
                padding: 2.5rem;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            }}
            h1 {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception:
        st.info("Fundo padrão carregado.")

# --- 4. FUNÇÕES AUXILIARES ---
def validar_email(email):
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    return bool(re.match(regex, email.lower()))

# --- 5. TELAS DE NAVEGAÇÃO ---

def tela_login():
    configurar_estilo_autenticacao("campo.jpeg.png")
    st.markdown("<h1 style='color: white; text-align: center;'>🔐 Login Mia</h1>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        user = st.text_input("Usuário ou E-mail").strip()
        pw = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar", use_container_width=True)
        
        if entrar:
            if user and pw:
                dados = verificar_login(user, pw)
                if dados:
                    st.session_state.auth_state = "logado"
                    st.session_state.usuario_id = dados['id']
                    st.session_state.usuario_nome = dados['nome']
                    st.success(f"Bem-vindo de volta, {dados['nome']}!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
            else:
                st.warning("Por favor, preencha todos os campos.")

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
    st.markdown("<h1 style='color: white; text-align: center;'>🌱 Começar Jornada</h1>", unsafe_allow_html=True)
    
    with st.form("cadastro_form"):
        new_user = st.text_input("Como quer ser chamado?").strip()
        new_email = st.text_input("Seu melhor e-mail").strip()
        new_pw = st.text_input("Crie uma senha (mín. 8 chars)", type="password")
        conf_pw = st.text_input("Confirme a senha", type="password")
        cadastrar = st.form_submit_button("Finalizar Cadastro", use_container_width=True)

        if cadastrar:
            if not new_user or not new_email or not new_pw:
                st.error("Preencha todos os campos.")
            elif not validar_email(new_email):
                st.error("Formato de e-mail inválido.")
            elif len(new_pw) < 8:
                st.error("A senha deve ter pelo menos 8 caracteres.")
            elif new_pw != conf_pw:
                st.error("As senhas não coincidem.")
            else:
                resultado = cadastrar_usuario(new_user, new_email, new_pw)
                if resultado == True:
                    st.success("Conta criada com sucesso!")
                    time.sleep(1)
                    st.session_state.auth_state = "login"
                    st.rerun()
                elif resultado == "existe":
                    st.warning("Este usuário ou e-mail já está em uso.")
                else:
                    st.error("Erro técnico ao cadastrar. Tente novamente.")
    
    if st.button("Voltar ao Login"):
        st.session_state.auth_state = "login"
        st.rerun()

def tela_recuperacao():
    configurar_estilo_autenticacao("campo.jpeg.png")
    st.markdown("<h1 style='color: white; text-align: center;'>🔑 Recuperar Acesso</h1>", unsafe_allow_html=True)
    
    with st.form("recuperar_form"):
        email = st.text_input("Digite seu e-mail cadastrado").strip()
        nova_pw = st.text_input("Nova Senha", type="password")
        conf_pw = st.text_input("Confirme a Nova Senha", type="password")
        enviar = st.form_submit_button("Redefinir Senha", use_container_width=True)

        if enviar:
            if not email or not nova_pw:
                st.error("Preencha os campos necessários.")
            elif len(nova_pw) < 8:
                st.error("A senha deve ter 8+ caracteres.")
            elif nova_pw != conf_pw:
                st.error("Senhas não conferem.")
            else:
                if verificar_email_existente(email):
                    if atualizar_senha(email, nova_pw):
                        st.success("Senha atualizada com sucesso!")
                        time.sleep(1)
                        st.session_state.auth_state = "login"
                        st.rerun()
                else:
                    st.error("E-mail não encontrado em nossa base.")
    
    if st.button("Cancelar"):
        st.session_state.auth_state = "login"
        st.rerun()

# --- 6. EXECUÇÃO PRINCIPAL ---

def main():
    # Inicializa o estado de autenticação
    if 'auth_state' not in st.session_state:
        st.session_state.auth_state = "login"

    # Injeta o JavaScript em todas as telas
    injetar_js_interativo()

    if st.session_state.auth_state == "login":
        tela_login()
    elif st.session_state.auth_state == "cadastro":
        tela_cadastro()
    elif st.session_state.auth_state == "recuperacao":
        tela_recuperacao()
    elif st.session_state.auth_state == "logado":
        # Painel Principal após Login
        st.sidebar.title(f"Olá, {st.session_state.usuario_nome}")
        if st.sidebar.button("Encerrar Sessão"):
            st.session_state.clear()
            st.rerun()
        
        st.write(f"## Bem-vindo ao Espaço Mia")
        st.info("O sistema está pronto para as próximas implementações de JavaScript.")

if __name__ == "__main__":
    main()