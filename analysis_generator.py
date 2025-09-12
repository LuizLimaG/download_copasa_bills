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
    Tarefa: Gere o RELATÓRIO DE ANÁLISE HÍDRICA – COPASA exclusivamente a partir do arquivo .txt fornecido (fatura COPASA). 
    ⚠️ Importante: Não use conhecimento externo, não invente valores, não use “estimado” ou “aprox.”. Apenas o que consta no arquivo.

    Saída obrigatória (formato exato):

    RELATÓRIO DE ANÁLISE HIDRICA - COPASA

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
    • Valor do Consumo (Água):  
    • Taxa de Esgoto:  
    • TOTAL:  

    OBSERVAÇÕES:
    • [Alertas obrigatórios]  
    • [Apenas as observações importantes presentes na fatura]  

    =====================================
    Regras detalhadas de extração e validação:

    🔹 Identificação
    - **Condomínio/Edificação**: capturar o nome após “COND”/“ED” ou, se não existir, usar o nome do imóvel presente na área “TOTAL A PAGAR”.
    - **Endereço**: concatenar logradouro + número + bairro + cidade/UF + CEP, sempre que todos os elementos estiverem disponíveis. 'FORMATO: Rua <Nome da rua>, <número>, <Bairro>, <Cidade/UF>, CEP.'
    - **Código do Cliente**: usar MATRÍCULA exatamente como aparece, com espaços.

    🔹 Fatura Atual
    - **Período de Referência**: do campo “REFERÊNCIA DA CONTA”.
    - **Data de Emissão**: do campo “Quando foi emitida?”.
    - **Data de Vencimento**: da linha/coluna “VENCIMENTO”.

    🔹 Consumo
    - **Leituras**: identificar dois padrões `dd/mm/aaaa <inteiro>`.  
    - A data mais antiga = Leitura Anterior  
    - A data mais recente = Leitura Atual  
    - **Consumo Total**: se houver linha explícita “XXm³ (XX.XXX litros)”, usar esse valor. Se não houver, calcular: Leitura Atual − Leitura Anterior.  
    - **Validação**: verificar se (Leitura Atual − Leitura Anterior) ≈ Consumo Total (tolerância de 1m³).  
    - **Consumo Médio Diário**: capturar o 3º número da linha “SEU CONSUMO EM LITROS” correspondente ao mês de referência. Acrescentar “litros/dia”.

    🔹 Valores
    - **Valor do Consumo (Água)**: linha “ABASTECIMENTO DE AGUA”.  
    - **Taxa de Esgoto**: linha iniciada com “ESGOTO…”.  
    - **TOTAL**: valor da área “TOTAL A PAGAR” (preferir o total final).

    🔹 Observações
    - Compare o consumo atual com os últimos 6 meses:  
    - Se variação > +40% em relação à mediana, alertar “Consumo atípico (acima do histórico)”.  
    - Se variação < −40%, alertar “Consumo atípico (abaixo do histórico)”.  
    - Se a validação das leituras não fechar (>1 m³ diferença), sinalizar “Possível anomalia no registro de consumo”.
    - Obrigatório informar se foi feito por média.                                      - INFORMAR EM UPPERCASE : NÃO COLOQUE: NÃO INFORMADO, só coloque as informações se existirem.
    - Obrigatório informar se houve problema na coleta.                                 - INFORMAR EM UPPERCASE : NÃO COLOQUE: NÃO INFORMADO, só coloque as informações se existirem.
    - Obrigatório informar se houve uso atípico de água.                                - INFORMAR EM UPPERCASE : NÃO COLOQUE: NÃO INFORMADO, só coloque as informações se existirem.
    - Obrigatório informar se foi feito pelo uso do consumo hídrico.                    - INFORMAR EM UPPERCASE : NÃO COLOQUE: NÃO INFORMADO, só coloque as informações se existirem.
    - Obrigatório informar se tem possibilidade de vazamento ou problema com a leitura. - INFORMAR EM UPPERCASE : NÃO COLOQUE: NÃO INFORMADO, só coloque as informações se existirem.
    - Incluir avisos da fatura (ex.: “Tarifa social”, “Consulta pública ANA”, “Hidrômetro novo instalado”).  
    - Se não houver observações, escrever: “Não informado”.

    🔹 Formatação
    - Números: respeitar separadores como na fatura (ex.: “XX.XXX”, “XXX,XX”).  
    - Moeda: sempre “R$” seguido de duas casas decimais.  
    - Não acrescentar notas ou comentários fora da seção **OBSERVAÇÕES**.  
    - Se qualquer campo não existir no texto, escrever exatamente “Não informado”.

    =====================================
    ⚠️ Nota final: Este relatório foi gerado automaticamente por Inteligência Artificial com base na fatura fornecida e **pode conter erros**.
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
