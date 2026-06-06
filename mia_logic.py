import google.generativeai as genai
import streamlit as st
import re
from database import buscar_indicacao_por_humor # Importação corrigida

# Configuração da IA
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"Erro de Configuração da API: {e}")

# --- 1. SEGURANÇA E HIGIENIZAÇÃO ---
def limpar_texto(texto):
    """Remove caracteres de injeção de prompt e limita o tamanho."""
    return re.sub(r'[<>"{}]', '', texto).strip()[:500]

def detectar_risco_critico(texto):
    """Verifica gatilhos de segurança de forma ampla e sem gastar tokens."""
    # Lista expandida para maior segurança clínica
    gatilhos = [
        "suicídio", "me matar", "morrer", "desistir", "autoextermínio",
        "não quero mais viver", "vontade de sumir", "acabar com tudo",
        "sem sentido", "tirar minha vida", "não aguento mais"
    ]
    texto_min = texto.lower()
    return any(gatilho in texto_min for gatilho in gatilhos)

# --- 2. LÓGICA PRINCIPAL COM VÁLVULA DE ESCAPE ---
def analisar_desabafo_ia(texto_usuario):
    """Analisa o diário com fallback automático para o banco de dados."""
    
    # Passo 1: Segurança Clínica Local (Custo Zero e Imediato)
    if detectar_risco_critico(texto_usuario):
        return "🚨 **Alerta de Cuidado:** Mia identificou que você está passando por um momento de extrema angústia. Por favor, ligue agora para o 188 (CVV). Você não está sozinho e existe ajuda gratuita e anônima."

    texto_sanitizado = limpar_texto(texto_usuario)

    try:
        # Passo 2: Tentativa com IA (Flash)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt_estruturado = f"""
        Você é a Mia, assistente de bem-estar.
        Analise o desabafo abaixo e classifique o sentimento em estritamente UMA destas palavras: 
        FELIZ, TRISTE, ANSIOSO, SOBRECARREGADO, RAIVA.

        REGRAS DE SEGURANÇA:
        - Se o texto indicar risco de vida ou auto-flagelação velada, responda APENAS a palavra: CRISE.
        - Não escreva nenhuma outra palavra além da categoria escolhida.

        DESABAFO: "{texto_sanitizado}"
        """
        
        response = model.generate_content(prompt_estruturado)
        resposta_ia = response.text.strip().upper()

        # Extração segura: Procura a palavra-chave dentro da resposta da IA
        categorias_validas = ["FELIZ", "TRISTE", "ANSIOSO", "SOBRECARREGADO", "RAIVA", "CRISE"]
        humor_detectado = "ANSIOSO" # Fallback preventivo
        
        for cat in categorias_validas:
            if cat in resposta_ia:
                humor_detectado = cat
                break

        if humor_detectado == "CRISE":
            return "🚨 **Atenção:** Identificamos um nível de angústia elevado no seu relato. Por favor, pare um momento e ligue para o 188 (CVV). Falar ajuda."

        # Passo 3: Busca a Recomendação no Banco de Dados Corrigido
        sugestao = buscar_indicacao_por_humor(humor_detectado)
        
        if sugestao:
            dicas = f"📚 Livro: {sugestao.get('livro_sugerido', 'N/A')}\n🎵 Música: {sugestao.get('musica_sugerida', 'N/A')}"
        else:
            dicas = "Respire fundo. Descanse a mente por 10 minutos."

        return f"**Mia:** Sinto que você está lidando com sentimentos ligados a **{humor_detectado.capitalize()}**. \n\n**Indicações para hoje:**\n{dicas}"

    except Exception as e:
        # --- VÁLVULA DE ESCAPE ---
        humores_fallback = {
            "triste": "TRISTE", "chora": "TRISTE", "melancol": "TRISTE",
            "ansied": "ANSIOSO", "nervos": "ANSIOSO", "medo": "ANSIOSO",
            "cansad": "SOBRECARREGADO", "exausto": "SOBRECARREGADO",
            "raiva": "RAIVA", "ódio": "RAIVA", "irritad": "RAIVA",
            "feliz": "FELIZ", "contente": "FELIZ", "bem": "FELIZ"
        }
        
        humor_manual = "ANSIOSO" 
        for chave, valor in humores_fallback.items():
            if chave in texto_sanitizado.lower():
                humor_manual = valor
                break
        
        sugestao = buscar_indicacao_por_humor(humor_manual)
        dicas = f"📚 Livro: {sugestao.get('livro_sugerido', '')}\n🎵 Música: {sugestao.get('musica_sugerida', '')}" if sugestao else "Tire um momento de pausa."
        
        return f"**(Modo de Segurança Mia)** Identificamos seu momento como {humor_manual.lower()}. \n\n**Recomendações:**\n{dicas}"

def gerar_recomendacao_humor(humor):
    """Recomendação rápida com fallback imediato."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash') 
        prompt = f"Como assistente Mia, dê uma saudação empática e curta (máximo 15 palavras) para alguém que está {humor}."
        response = model.generate_content(prompt)
        validacao_ia = response.text.strip()
        
        sugestao = buscar_indicacao_por_humor(humor.upper())
        dicas = f"📚 {sugestao.get('livro_sugerido', '')} | 🎵 {sugestao.get('musica_sugerida', '')}" if sugestao else ""
        
        return f"**Mia:** {validacao_ia} \n\n**Sugestão do Acervo:** {dicas}"
        
    except Exception:
        sugestao = buscar_indicacao_por_humor(humor.upper())
        dicas = f"📚 {sugestao.get('livro_sugerido', '')} | 🎵 {sugestao.get('musica_sugerida', '')}" if sugestao else ""
        return f"**Mia:** Entendo que você está {humor}. \n\n**Recomendação:** {dicas}"