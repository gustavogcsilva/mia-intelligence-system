import streamlit as st
from supabase import create_client, Client

# --- CONEXÃO ---
URL = st.secrets.get("SUPABASE_URL")
KEY = st.secrets.get("SUPABASE_KEY")

@st.cache_resource
def conectar_supabase() -> Client:
    if not URL or not KEY:
        st.error("❌ Configuração ausente nos Secrets.")
        st.stop()
    return create_client(URL, KEY)

supabase = conectar_supabase()

# --- FUNÇÕES DE AUTENTICAÇÃO ---

def verificar_login(identificador, senha):
    try:
        res = supabase.table("usuarios").select("*").or_(
            f"email.eq.{identificador.lower()},nome.eq.{identificador}"
        ).execute()
        if res.data:
            user_db = res.data[0]
            if user_db['senha'] == senha:
                return user_db
        return None
    except Exception as e:
        print(f"Erro login: {e}")
        return None

def cadastrar_usuario(nome, email, senha):
    try:
        email_limpo = email.strip().lower()
        # Verifica se já existe
        check = supabase.table("usuarios").select("id").or_(
            f"email.eq.{email_limpo},nome.eq.{nome.strip()}"
        ).execute()
        if check.data:
            return "existe"
        
        # Insere
        resposta = supabase.table("usuarios").insert({
            "nome": nome.strip(),
            "email": email_limpo,
            "senha": senha
        }).execute()
        return len(resposta.data) > 0
    except Exception as e:
        print(f"Erro cadastro: {e}")
        return "erro"

def verificar_email_existente(email):
    """Necessária para a tela de recuperação"""
    try:
        res = supabase.table("usuarios").select("id").eq("email", email.strip().lower()).execute()
        return len(res.data) > 0
    except:
        return False

def atualizar_senha(email, nova_senha):
    """Necessária para a tela de recuperação"""
    try:
        res = supabase.table("usuarios").update({"senha": nova_senha}).eq("email", email.strip().lower()).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"Erro update senha: {e}")
        return False    