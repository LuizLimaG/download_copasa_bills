import os
import time
import pdfplumber
from pathlib import Path
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def generate_report(pdf_path, txt_dir, report_dir):
    pdf_name = Path(pdf_path).stem

    txt_path = Path(txt_dir) / f"{pdf_name}.txt"
    report_path = Path(report_dir) / f"{pdf_name}_relatorio.txt"

    os.makedirs(txt_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)

    with pdfplumber.open(pdf_path) as pdf, open(txt_path, 'w', encoding='utf-8') as f:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                f.write(text + '\n')
    print(f"Texto extraído salvo em: {txt_path}")

    with open(txt_path, 'r', encoding='utf-8') as f:
        text_data = f.read()

    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-lite', temperature=0.1)

    template = """
    RELATÓRIO DE ANÁLISE HIDRICA - COPASA

    Você é um analista especializado em faturas de água da COPASA.

    Extraia e organize as seguintes informações da fatura:

    IDENTIFICAÇÃO:
    • Condomínio/Edificação: 
    • Endereço: 
    • Código do Cliente: 

    FATURA ATUAL:
    • Data de Emissão: 
    • Período de Referência: 
    • Data de Vencimento: 

    CONSUMO:
    • Leitura Anterior: 
    • Leitura Atual: 
    • Consumo Total: 
    • Consumo Médio Diário: 

    VALORES:
    • Valor do Consumo: 
    • Taxa de Esgoto: 
    • TOTAL: 

    OBSERVAÇÕES:
    • [Análise do consumo e alertas se necessário]

    Dados da fatura:
    {text}
    """

    prompt = PromptTemplate(input_variables=['text'], template=template)
    chain = prompt | llm | StrOutputParser()

    time.sleep(4)
    print(f"Gerando relatório para: {pdf_name}")
    relatorio = chain.invoke({'text': text_data})

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(relatorio)

    print(f"Relatório salvo em: {report_path}")
    return str(report_path)

def generate_reports_from_folder(pasta_pdfs, pasta_txts, pasta_relat):
    os.makedirs(pasta_txts, exist_ok=True)
    os.makedirs(pasta_relat, exist_ok=True)

    for nome in os.listdir(pasta_pdfs):
        if nome.lower().endswith(".pdf"):
            caminho = os.path.join(pasta_pdfs, nome)
            try:
                generate_report(caminho, pasta_txts, pasta_relat)
            except Exception as e:
                print(f"[ERRO no relatório] {nome}: {e}")
