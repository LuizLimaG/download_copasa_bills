import os
import time
import shutil
import pdfplumber
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def get_new_filename_from_pdf(pdf_path):
    """
    Usa LLM para extrair o novo nome do arquivo a partir do conteúdo do PDF.
    """  
    with pdfplumber.open(pdf_path) as pdf:
        text_data = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_data += text + '\n'

    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-lite', temperature=0.2)

    template = """
    Você receberá o conteúdo textual de uma fatura da Copasa.

    Sua tarefa é gerar APENAS um nome de arquivo no seguinte formato:

    <nome_condominio_ou_edificio>_<bloco_se_existir>_<MM-AAAA>.pdf

    Regras:
    1. Se o imóvel for um CONDOMÍNIO, use o prefixo "CONDOMINIO".
    2. Se o imóvel for um EDIFÍCIO, use o prefixo "EDIFICIO".
    3. Se houver identificação de BLOCO, inclua-o após o nome. Exemplo: "BLOCOA".
    4. Se NÃO houver bloco, omita essa parte.
    5. A data deve estar no formato mês-ano (MM-AAAA).
    6. Use apenas letras e números, sem acentos, espaços ou caracteres especiais. Substitua espaços por underline `_`.
    7. Retorne APENAS o nome do arquivo final, sem explicações adicionais.

    Exemplo esperado:
    CONDOMINIO_SOL_BLOCO-A_01-2024.pdf
    EDIFICIO_CENTRAL_07-2023.pdf

    Conteúdo da fatura:
    {text}
    """

    prompt = PromptTemplate(input_variables=['text'], template=template)
    chain = prompt | llm | StrOutputParser()

    time.sleep(4)
    novo_nome = chain.invoke({'text': text_data}).strip()
    return novo_nome

def already_renamed(nome_arquivo):
    """
    Verifica se o arquivo já está no padrão esperado.
    """
    # Critério: deve conter "_" e terminar em ".pdf"

    nome_upper = nome_arquivo.upper()

    return (
        nome_arquivo.endswith('.pdf')
        and "_" in nome_arquivo
        and ("CONDOMINIO" in nome_upper or "EDIFICIO" in nome_upper)
    )

def rename_only_new(pasta):
    """
    Renomeia apenas os PDFs que ainda não estão no padrão.
    """
    arquivos_processados = []
    arquivos_pulados = []

    pdfs_para_processar = [
        os.path.join(pasta, nome) 
        for nome in os.listdir(pasta) 
        if nome.lower().endswith(".pdf")
    ]

    print(f"[INFO] Encontrados {len(pdfs_para_processar)} PDFs\n")

    for caminho in pdfs_para_processar:
        nome_atual = os.path.basename(caminho)

        if already_renamed(nome_atual):
            print(f"[PULADO] {nome_atual} (já está no padrão)")
            arquivos_pulados.append(caminho)
            continue

        try:
            print(f"[PROCESSANDO] {nome_atual}...")
            novo_nome = get_new_filename_from_pdf(caminho)
            novo_caminho = os.path.join(pasta, novo_nome)

            if os.path.exists(novo_caminho):
                print(f"[JÁ EXISTE] {novo_nome} -> não renomeado")
                continue

            shutil.move(caminho, novo_caminho)
            print(f"[RENOMEADO] {nome_atual} -> {novo_nome}")
            arquivos_processados.append(novo_caminho)

        except Exception as e:
            print(f"[ERRO ao processar] {nome_atual}: {e}")

    print(f"\n[RESUMO]")
    print(f"Arquivos renomeados: {len(arquivos_processados)}")
    print(f"Arquivos já no padrão (pulados): {len(arquivos_pulados)}")
    print(f"Total de arquivos analisados: {len(pdfs_para_processar)}\n")

    return arquivos_processados + arquivos_pulados
