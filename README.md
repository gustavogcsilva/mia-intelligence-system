# Mia - Diário de Bem-Estar 🌱

O **Mia** é um assistente pessoal de bem-estar integrado a uma Inteligência Artificial (Gemini) e a um banco de dados relacional (MySQL/Aiven). O projeto visa oferecer um espaço seguro, acolhedor e privado para que usuários possam registrar suas emoções, desabafar e receber recomendações personalizadas para melhorar seu estado mental.

## 🚀 Funcionalidades Principais

- **Diário Inteligente:** Registro diário de emoções e desabafos.
- **Análise da Mia:** Integração com a IA do Google (Gemini) para oferecer acolhimento empático e recomendações dinâmicas de livros e músicas.
- **Segurança Clínica:** Detecção automática de gatilhos críticos com suporte direto ao CVV (188).
- **Exportação:** Histórico completo disponível para download em formato CSV e páginas individuais em PDF.
- **Modo Seguro:** Sistema de *fallback* automático que garante que o usuário sempre receba uma sugestão vinda do banco de dados, mesmo em caso de falha da API.

## 🛠️ Tecnologias Utilizadas

- **Frontend:** Streamlit (Puro Python).
- **Inteligência Artificial:** Google Gemini API (gemini-1.5-flash).
- **Banco de Dados:** MySQL (hospedado no Aiven).
- **Processamento de Áudio:** SpeechRecognition + Audio Recorder Streamlit.
- **Relatórios:** FPDF e Pandas.

## ⚙️ Configuração para Produção

Para rodar este projeto, você precisará configurar as variáveis de ambiente (Secrets) no seu serviço de deploy:

| Chave | Descrição |
| :--- | :--- |
| `DB_HOST` | Host do seu banco MySQL (Aiven) |
| `DB_USER` | Usuário do banco |
| `DB_PASSWORD` | Senha do banco |
| `DB_NAME` | Nome do banco (defaultdb) |
| `DB_PORT` | Porta de conexão |
| `GOOGLE_API_KEY` | Sua chave de API do Google Gemini |

## 📦 Instalação Local

1. Clone o repositório:
   ```bash
   git clone [https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git](https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git)
  
