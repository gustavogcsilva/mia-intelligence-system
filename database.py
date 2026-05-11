import streamlit as st
from supabase import create_client, Client
import os

# --- CONEXÃO E SEGURANÇA ---
# Busca credenciais dos Secrets (Streamlit Cloud ou .streamlit/secrets.toml)
URL = st.secrets.get("SUPABASE_URL")
KEY = st.secrets.get("SUPABASE_KEY")

@st.cache_resource
def conectar_supabase() -> Client:
    """
    Estabelece a conexão uma única vez e a mantém em cache.
    Isso economiza recursos e evita o erro 'Invalid URL'.
    """
    if not URL or not KEY:
        st.error("❌ Configuração ausente: Verifique os Secrets do Streamlit.")
        st.stop()
    
    try:
        return create_client(URL, KEY)
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao banco de dados: {e}")
        st.stop()

# Inicialização Global
supabase = conectar_supabase()

# --- FUNÇÕES DE AUTENTICAÇÃO ---

def cadastrar_usuario(nome, email, senha):
    """Realiza o cadastro tratando duplicidades de forma limpa."""
    try:
        email_limpo = email.strip().lower()
        
        # 1. Checagem unificada de existência
        check = supabase.table("usuarios").select("id").or_(
            f"email.eq.{email_limpo},nome.eq.{nome.strip()}"
        ).execute()

        if check.data:
            return "existe"

        # 2. Inserção
        dados = {
            "nome": nome.strip(),
            "email": email_limpo,
            "senha": senha  # Nota: futuramente use bcrypt aqui
        }
        
        resposta = supabase.table("usuarios").insert(dados).execute()
        return len(resposta.data) > 0

    except Exception as e:
        print(f"Erro no cadastro: {e}")
        return "erro"

def verificar_login(identificador, senha):
    """Valida login por email ou username."""
    try:
        id_limpo = identificador.strip().lower()
        res = supabase.table("usuarios").select("*").or_(
            f"email.eq.{id_limpo},nome.eq.{identificador.strip()}"
        ).execute()

        if res.data:
            usuario = res.data[0]
            if usuario['senha'] == senha:
                return usuario
        return None
    except Exception as e:
        print(f"Erro no login: {e}")
        return None

# --- FUNÇÕES DE OPERAÇÃO (MIA) ---

def salvar_diario(usuario_id, resumo, problema, data, indicacao):
    """Registra o diário vinculado ao usuário."""
    try:
        payload = {
            "usuario_id": usuario_id,
            "resumo": resumo,
            "desafios": problema,
            "data_registro": str(data),
            "recomendacao_mia": indicacao
        }
        res = supabase.table("diario").insert(payload).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"Erro ao salvar diário: {e}")
        return False

def buscar_recomendacao_no_banco(humor):
    """Busca uma dica aleatória baseada no humor."""
    try:
        res = supabase.table("dicas_mia").select("*").eq("humor", humor.upper()).execute()
        if res.data:
            import random
            return random.choice(res.data)
        
        return {"texto": "Respire fundo. Estou aqui com você.", "link": "#"}
    except Exception:
        return {"texto": "Continue firme na sua jornada.", "link": "#"}

def salvar_desabafo_imediato(usuario_id, texto):
    """Salva o 'Grito' no banco de dados."""
    try:
        if texto.strip():
            supabase.table("desabafos_grito").insert({
                "usuario_id": usuario_id,
                "conteudo": texto.strip()
            }).execute()
            return True
    except Exception as e:
        print(f"Erro no grito: {e}")
        return False