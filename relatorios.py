from fpdf import FPDF
import datetime

class RelatorioMia(FPDF):
    def header(self):
        try:
            # Logo da GCS
            self.image('logo_gcs.png', 10, 8, 33) 
        except:
            self.set_font('Arial', 'B', 12)
            self.set_text_color(33, 150, 243)
            self.cell(40, 10, 'GCS CORE', 0, 0, 'L')

        # Linha estética superior azul (Identidade GCS)
        self.set_draw_color(33, 150, 243)
        self.set_line_width(1)
        self.line(10, 25, 200, 25)
        self.ln(20) 

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        # CORREÇÃO NO RODAPÉ CONFORME SOLICITADO
        texto_rodape = t('Relatorio gerado pelo Sistema Help! | GCS Core System Intelligence | Pagina ') + str(self.page_no())
        self.cell(0, 10, texto_rodape, 0, 0, 'C')

def t(txt):
    """Tratamento de caracteres para FPDF latin-1."""
    if txt is None: return ""
    mapa = {'á':'a','é':'e','í':'i','ó':'o','ú':'u','ã':'a','õ':'o','ç':'c','ê':'e','ô':'o'}
    res = str(txt)
    for k, v in mapa.items(): 
        res = res.replace(k, v).replace(k.upper(), v.upper())
    return res.encode('latin-1', 'replace').decode('latin-1')

def gerar_pdf_completo(nome_usuario, dados, tipo="Relatorio"):
    pdf = RelatorioMia()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- CABEÇALHO DE TÍTULO ---
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(33, 150, 243)
    pdf.cell(0, 15, t("RELATORIO DE ACOMPANHAMENTO EMOCIONAL"), ln=True, align="L")
    
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 5, t("Projeto Help! - Assistencia Digital"), ln=True)
    
    # Faixa de informações do paciente
    pdf.set_fill_color(245, 249, 255)
    pdf.set_font("Arial", "", 10)
    data_ini = dados[-1]['data_registro'].strftime('%d/%m/%Y') if dados else "N/A"
    data_fim = dados[0]['data_registro'].strftime('%d/%m/%Y') if dados else "N/A"
    pdf.cell(0, 10, t(f" Paciente: {nome_usuario} | Periodo: {data_ini} a {data_fim}"), ln=True, fill=True)
    pdf.ln(5)

    # --- 1. ANÁLISE DE VARIAÇÃO EMOCIONAL (DATAFRAME DE HUMOR) ---
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(33, 150, 243)
    pdf.cell(0, 10, t("1. Analise de Variacao Emocional"), ln=True)

    if dados:
        fluxo_humor = []
        # Pega os últimos 7 registros para mostrar a evolução
        for d in reversed(dados[:7]):
            dia = d['data_registro'].strftime('%a')
            sentimento = d.get('sentimento', 'Nao informado')
            fluxo_humor.append(f"{dia}: {sentimento}")
        humores_timeline = "  |  ".join(fluxo_humor)
    else:
        humores_timeline = "Sem registros no periodo."

    # Box visual do fluxo
    pdf.set_draw_color(33, 150, 243)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 10, t(f" Sequencia registrada: [ {humores_timeline} ]"), border=1, align='C')

    pdf.set_font("Arial", "", 10)
    pdf.ln(2)
    pdf.multi_cell(0, 6, t("O historico acima demonstra os picos de variacao emocional. Mudancas bruscas sao monitoradas para identificar gatilhos e otimizar o suporte da Mia."))
    pdf.ln(5)

    # --- 2. DETALHAMENTO DIÁRIO E INSIGHTS DA MIA ---
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(33, 150, 243)
    pdf.cell(0, 10, t("2. Detalhamento Diario e Insights da Mia"), ln=True)
    pdf.ln(2)

    for item in dados:
        if pdf.get_y() > 240: pdf.add_page()
        
        # Linha de separação
        pdf.set_draw_color(33, 150, 243)
        pdf.set_line_width(0.3)
        pdf.cell(0, 0, '', 'T', ln=True)
        pdf.ln(2)
        
        # Data e Status Emocional (Destaque para picos)
        data_f = item['data_registro'].strftime('%d/%m/%Y')
        sentimento_dia = item.get('sentimento', 'Nao informado').upper()
        
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(33, 150, 243)
        pdf.cell(40, 6, t(f"DATA: {data_f}"), ln=0)
        
        # Define cor do pico: Vermelho para alertas, Verde para estabilidade
        if sentimento_dia in ["TRISTE", "SOBRECARREGADO", "ANSIOSO", "ESTRESSADO"]:
            pdf.set_text_color(200, 0, 0)
        else:
            pdf.set_text_color(46, 125, 50)
            
        pdf.cell(0, 6, t(f"STATUS: {sentimento_dia}"), ln=True)
        
        # Relato do dia
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, t(f"Relato: {item['resumo_dia']} | Desafio: {item.get('problema_dia', 'Nao informado')}"))
        
        # Box de Indicação da Mia
        indicacao = item.get('indicacao') or "Nao registrada."
        pdf.ln(1)
        pdf.set_fill_color(232, 245, 233) 
        pdf.set_draw_color(76, 175, 80)  
        pdf.set_font("Arial", "B", 9)
        pdf.set_text_color(46, 125, 50)
        pdf.cell(0, 6, t("  Sugerido pela Mia:"), ln=True, fill=True, border='TLR')
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(0, 6, t(f"  {indicacao}"), border='BLR', fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

    # --- 3. NOTA CLÍNICA ---
    if pdf.get_y() > 220: pdf.add_page()
    pdf.ln(5)
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(33, 150, 243)
    pdf.cell(0, 10, t("3. Nota para o Psicoterapeuta"), ln=True)
    
    pdf.set_fill_color(252, 252, 252)
    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 6, t("Prezado(a) terapeuta, este relatorio consolida os dados registrados no Sistema Help!. A analise de picos emocionais visa auxiliar na identificacao de padroes de comportamento e gatilhos externos."), border=1, fill=True)

    # --- RODAPÉ FINAL ---
    pdf.ln(10)
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 4, t("Este relatorio e um informativo gerado por GCS Core System Intelligence e nao substitui o acompanhamento profissional."), align='C')

    return pdf.output(dest='S').encode('latin-1')