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
    1. Se o imóvel for um CONDOMÍNIO, use o prefixo "Condominio".
    2. Se o imóvel for um EDIFÍCIO, use o prefixo "Edificio".
    3. Se houver identificação de BLOCO, inclua-o após o nome. Exemplo: "BlocoA".
    4. Se NÃO houver bloco, omita essa parte.
    5. A data deve estar no formato mês-ano (MM-AAAA).
    6. Use apenas letras e números, sem acentos, espaços ou caracteres especiais. Substitua espaços por underline `_`.
    7. Retorne APENAS o nome do arquivo final, sem explicações adicionais.

    Exemplo esperado:
    CONDOMINIO SOL BLOCO-A 01-2024.pdf
    EDIFICIO CENTRAL 07-2023.pdf

    Conteúdo da fatura:
    {text}
    """


    prompt = PromptTemplate(input_variables=['text'], template=template)
    chain = prompt | llm | StrOutputParser()

    time.sleep(4)
    novo_nome = chain.invoke({'text': text_data}).strip()
    return novo_nome

def check_duplicate_exists(pasta, novo_nome):
    """
    Verifica se já existe um arquivo com o mesmo nome na pasta.
    """
    caminho_completo = os.path.join(pasta, novo_nome)
    return os.path.exists(caminho_completo)

def rename_pdf(pdf_path):
    """
    Renomeia um PDF individual, verificando duplicatas antes.
    """
    diretorio = os.path.dirname(pdf_path)
    nome_atual = os.path.basename(pdf_path)
    
    try:
        novo_nome = get_new_filename_from_pdf(pdf_path)
        
        if check_duplicate_exists(diretorio, novo_nome):
            print(f"[DUPLICATA ENCONTRADA] {nome_atual} seria renomeado para {novo_nome}, mas já existe. Removendo duplicata...")
            os.remove(pdf_path)  # Remove o arquivo duplicado
            return None
        
        novo_caminho = os.path.join(diretorio, novo_nome)
        shutil.move(pdf_path, novo_caminho)
        print(f"[RENOMEADO] {nome_atual} -> {novo_nome}")
        return novo_caminho
        
    except Exception as e:
        print(f"[ERRO ao processar] {nome_atual}: {e}")
        return None

def rename_all_pdfs(pasta):
    """
    Processa todos os PDFs da pasta, removendo duplicatas e renomeando os únicos.
    """
    arquivos_processados = []
    arquivos_removidos = 0
    
    pdfs_para_processar = []
    for nome in os.listdir(pasta):
        if nome.lower().endswith(".pdf"):
            caminho = os.path.join(pasta, nome)
            pdfs_para_processar.append(caminho)
    
    print(f"[INFO] Encontrados {len(pdfs_para_processar)} PDFs para processar")
    
    for caminho in pdfs_para_processar:
        nome_atual = os.path.basename(caminho)
        resultado = rename_pdf(caminho)
        
        if resultado is None:
            if not os.path.exists(caminho):  # Se não existe mais, foi removido
                arquivos_removidos += 1
        else:
            arquivos_processados.append(resultado)
    
    print(f"\n[RESUMO]")
    print(f"Arquivos processados com sucesso: {len(arquivos_processados)}")
    print(f"Duplicatas removidas: {arquivos_removidos}")
    print(f"Total de arquivos originais: {len(pdfs_para_processar)} \n")
    
    return arquivos_processados

def rename_all_pdfs_safe_mode(pasta):
    """
    Versão mais segura que move duplicatas para uma pasta separada ao invés de deletar.
    """
    arquivos_processados = []
    arquivos_movidos = 0
    
    pasta_duplicatas = os.path.join(pasta, "duplicatas")
    os.makedirs(pasta_duplicatas, exist_ok=True)
    
    pdfs_para_processar = []
    for nome in os.listdir(pasta):
        if nome.lower().endswith(".pdf"):
            caminho = os.path.join(pasta, nome)
            pdfs_para_processar.append(caminho)
    
    print(f"[INFO] Encontrados {len(pdfs_para_processar)} PDF's baixados\n")
    
    nomes_ja_processados = set()
    
    arquivos_ja_renomeados = []
    for caminho in pdfs_para_processar[:]:
        nome_atual = os.path.basename(caminho)
        if '_' in nome_atual and not nome_atual.startswith(('temp', 'download', 'fatura')):
            nomes_ja_processados.add(nome_atual)
            arquivos_ja_renomeados.append(caminho)
            pdfs_para_processar.remove(caminho)
    
    for caminho in pdfs_para_processar:
        nome_atual = os.path.basename(caminho)
        diretorio = os.path.dirname(caminho)
        
        try:
            print(f"[PROCESSANDO] {nome_atual}...")
            novo_nome = get_new_filename_from_pdf(caminho)
            
            if novo_nome in nomes_ja_processados or check_duplicate_exists(diretorio, novo_nome):
                caminho_duplicata = os.path.join(pasta_duplicatas, nome_atual)
                contador = 1
                nome_base, ext = os.path.splitext(nome_atual)
                while os.path.exists(caminho_duplicata):
                    novo_nome_duplicata = f"{nome_base}_{contador}{ext}"
                    caminho_duplicata = os.path.join(pasta_duplicatas, novo_nome_duplicata)
                    contador += 1
                
                shutil.move(caminho, caminho_duplicata)
                print(f"[DUPLICATA MOVIDA] {nome_atual} -> duplicatas/{os.path.basename(caminho_duplicata)} (nome seria: {novo_nome})\n")
                arquivos_movidos += 1
            else:
                novo_caminho = os.path.join(diretorio, novo_nome)
                shutil.move(caminho, novo_caminho)
                nomes_ja_processados.add(novo_nome)
                print(f"[RENOMEADO] {nome_atual} -> {novo_nome}\n")
                arquivos_processados.append(novo_caminho)
                
        except Exception as e:
            print(f"[ERRO ao processar] {nome_atual}: {e}")
    
    print(f"[RESUMO]")
    print(f"Arquivos já processados anteriormente: {len(arquivos_ja_renomeados)}")
    print(f"Arquivos processados com sucesso: {len(arquivos_processados)}")
    print(f"Duplicatas movidas para pasta 'duplicatas': {arquivos_movidos}")
    print(f"Total de arquivos analisados: {len(pdfs_para_processar) + len(arquivos_ja_renomeados)}\n")
    print(f"{"="*30}\n")
    
    return arquivos_processados + arquivos_ja_renomeados
    