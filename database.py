import pymysql
import hashlib
import streamlit as st

def hash_senha(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def obter_conexao():
    try:
        host_limpo = st.secrets["DB_HOST"].strip()
        usuario_limpo = st.secrets["DB_USER"].strip()
        senha_limpa = st.secrets["DB_PASSWORD"].strip()
        banco_limpo = st.secrets["DB_NAME"].strip()
        porta_limpa = int(str(st.secrets["DB_PORT"]).strip())

        conexao = pymysql.connect(
            host=host_limpo,
            user=usuario_limpo,
            password=senha_limpa,
            database=banco_limpo,
            port=porta_limpa,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        
        with conexao.cursor() as cursor:
            # 1. Garante a tabela de usuários
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nome_usuario VARCHAR(50) NOT NULL UNIQUE,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    senha VARCHAR(64) NOT NULL,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # 2. Garante a tabela do caderno/humores
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS humores (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario_id INT NOT NULL,
                    data_desabafo DATE NOT NULL,
                    como_foi_dia TEXT NOT NULL,
                    o_que_melhorar TEXT NOT NULL,
                    desabafo_livre TEXT NOT NULL,
                    sentimento VARCHAR(50) DEFAULT 'Pendente',
                    insight_ia TEXT DEFAULT NULL,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
                );
            """)

            # 3. CRIAÇÃO AUTOMÁTICA DO ACERVO DE INDICAÇÕES
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS acervo_mia (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    categoria_humor VARCHAR(50) NOT NULL UNIQUE,
                    livro_sugerido VARCHAR(255) NOT NULL,
                    musica_sugerida VARCHAR(255) NOT NULL
                );
            """)

            # 4. ALIMENTAÇÃO AUTOMÁTICA (Apenas se a tabela estiver completamente vazia)
            cursor.execute("SELECT COUNT(*) AS total FROM acervo_mia;")
            if cursor.fetchone()['total'] == 0:
                sql_carga = """
                    INSERT INTO acervo_mia (categoria_humor, livro_sugerido, musica_sugerida) VALUES 
                    ('😊 Calmo/Feliz', '📚 Livro: O Obstáculo é o Caminho (Ryan Holiday)', '🎵 Música: Perfect Symphony (Ed Sheeran)'),
                    ('😐 Neutro', '📚 Livro: Foco (Daniel Goleman)', '🎵 Música: Evening Of Light (Quentin Sirjacq)'),
                    ('😰 Ansioso', '📚 Livro: O Poder do Agora (Eckhart Tolle)', '🎵 Música: Weightless (Marconi Union) - Frequência Anti-Ansiedade'),
                    ('😴 Cansado/Exausto', '📚 Livro: O Essencialismo (Greg McKeown)', '🎵 Música: Clair de Lune (Claude Devussy)'),
                    ('😔 Triste', '📚 Livro: Talvez você deva conversar com alguém (Lori Gottlieb)', '🎵 Música: Fix You (Coldplay)');
                """
                cursor.execute(sql_carga)
                print("✨ Banco de dados populado com o acervo inicial de indicações!")
                
        conexao.commit()
        return conexao
    except Exception as e:
        print(f"Erro na Conexão/Inicialização do Aiven: {e}")
        return None

def verificar_login(identificador, senha):
    conexao = obter_conexao()
    if conexao is None: 
        return None
    try:
        with conexao.cursor() as cursor:
            senha_crypto = hash_senha(senha)
            # Garantimos que os campos retornados sejam exatamente 'id' e 'nome'
            sql = """
                SELECT id, nome_usuario AS nome 
                FROM usuarios 
                WHERE (nome_usuario = %s OR email = %s) AND senha = %s
            """
            cursor.execute(sql, (identificador.strip(), identificador.strip().lower(), senha_crypto))
            resultado = cursor.fetchone()
            return resultado  # Retorna o dicionário com {'id': X, 'nome': 'Y'}
    except Exception as e:
        print(f"Erro interno no verificar_login: {e}")
        return None
    finally:
        if conexao and conexao.open: 
            conexao.close()

def cadastrar_usuario(nome, email, senha):
    conexao = obter_conexao()
    if conexao is None: return "erro"
    try:
        with conexao.cursor() as cursor:
            sql_check = "SELECT id FROM usuarios WHERE nome_usuario = %s OR email = %s"
            cursor.execute(sql_check, (nome.strip(), email.strip().lower()))
            if cursor.fetchone(): return "existe"
            
            sql_insert = "INSERT INTO usuarios (nome_usuario, email, senha) VALUES (%s, %s, %s)"
            cursor.execute(sql_insert, (nome.strip(), email.strip().lower(), hash_senha(senha)))
        conexao.commit()
        return True
    except Exception: return "erro"
    finally:
        if conexao and conexao.open: conexao.close()

def verificar_email_existente(email):
    conexao = obter_conexao()
    if conexao is None: return False
    try:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email.strip().lower(),))
            return bool(cursor.fetchone())
    except Exception: return False
    finally:
        if conexao and conexao.open: conexao.close()

def atualizar_senha(email, nova_senha):
    conexao = obter_conexao()
    if conexao is None: return False
    try:
        with conexao.cursor() as cursor:
            cursor.execute("UPDATE usuarios SET senha = %s WHERE email = %s", (hash_senha(nova_senha), email.strip().lower()))
        conexao.commit()
        return True
    except Exception: return False
    finally:
        if conexao and conexao.open: conexao.close()

def buscar_indicacao_por_humor(humor_procurado):
    conexao = obter_conexao()
    if conexao is None: 
        return None
    try:
        with conexao.cursor() as cursor:
            sql = "SELECT livro_sugerido, musica_sugerida FROM acervo_mia WHERE categoria_humor = %s LIMIT 1"
            cursor.execute(sql, (humor_procurado,))
            return cursor.fetchone() # Retorna o dicionário com o livro e a música
    except Exception as e:
        print(f"Erro ao buscar indicação: {e}")
        return None
    finally:
        if conexao and conexao.open: 
            conexao.close()

def listar_humores_do_acervo():
    conexao = obter_conexao()
    if conexao is None: 
        return []
    try:
        with conexao.cursor() as cursor:
            # Puxa apenas a coluna com os humores salvos no banco
            sql = "SELECT categoria_humor FROM acervo_mia ORDER BY id ASC"
            cursor.execute(sql)
            resultados = cursor.fetchall()
            # Transforma a lista de dicionários em uma lista simples de textos para o Selectbox
            return [r['categoria_humor'] for r in resultados]
    except Exception as e:
        print(f"Erro ao listar humores: {e}")
        return []
    finally:
        if conexao and conexao.open: 
            conexao.close()