import os
import shutil
import pdfplumber
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def rename_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text_data = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_data += text + '\n'

    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-lite', temperature=0.2)

    template = """
    Você recebe o conteúdo de uma fatura da Copasa e deve retornar APENAS:
    Um nome de arquivo no formato: <nomecondominio>_<bloco>_<MM-AAAA>.pdf

    Exemplo: CondominioSol_BlocoA_01-2024.pdf SE CASO NAO HOUVER BLOCO REMOVA 'BLOCO' DO NOME

    Retorne APENAS o nome do arquivo, sem explicação adicional.

    Conteúdo da fatura:
    {text}
    """

    prompt = PromptTemplate(input_variables=['text'], template=template)
    chain = prompt | llm | StrOutputParser()

    novo_nome = chain.invoke({'text': text_data}).strip()
    diretorio = os.path.dirname(pdf_path)
    novo_caminho = os.path.join(diretorio, novo_nome)

    shutil.move(pdf_path, novo_caminho)
    print(f"PDF renomeado para: {novo_nome}")
    return novo_caminho

def rename_all_pdfs(pasta):
    arquivos = []
    for nome in os.listdir(pasta):
        if nome.lower().endswith(".pdf"):
            caminho = os.path.join(pasta, nome)
            try:
                novo = rename_pdf(caminho)
                arquivos.append(novo)
            except Exception as e:
                print(f"[ERRO ao renomear] {nome}: {e}")
    return arquivos