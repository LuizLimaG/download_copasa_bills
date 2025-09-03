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
    Tarefa: Gere o RELATÓRIO DE ANÁLISE HÍDRICA – COPASA apenas a partir do arquivo .txt fornecido (fatura COPASA). Não use conhecimento externo, não invente valores, não use “estimado”.

    Saída obrigatória (formato exato):

    RELATÓRIO DE ANÁLISE HIDRICA - COPASA

    IDENTIFICAÇÃO:
    • Condomínio/Edificação:  : Utilize as regras de execução abaixo
    • Endereço:  : Utilize as regras de execução abaixo
    • Código do Cliente:  : Utilize as regras de execução abaixo

    FATURA ATUAL:
    • Data de Emissão:  : Utilize as regras de execução abaixo
    • Período de Referência:  : Utilize as regras de execução abaixo
    • Data de Vencimento:  : Utilize as regras de execução abaixo

    CONSUMO:
    • Leitura Anterior: : Utilize as regras de execução abaixo
    • Leitura Atual:  : Utilize as regras de execução abaixo
    • Consumo Total:  : Utilize as regras de execução abaixo
    • Consumo Médio Diário:  : Utilize as regras de execução abaixo

    VALORES:
    • Valor do Consumo:  : Utilize as regras de execução abaixo
    • Taxa de Esgoto:  : Utilize as regras de execução abaixo
    • TOTAL:  : Utilize as regras de execução abaixo

    OBSERVAÇÕES:
    • [Análise do consumo e alertas se necessário] : Utilize as regras de execução abaixo
    • [Apenas as observações importantes presentes na fatura] : Utilize as regras de execução abaixo


    Regras de extração (seguir à risca):

    Condomínio/Edificação: texto após “COND”/“ED” ou nome do imóvel na área “TOTAL A PAGAR”.
    Endereço: concatenar logradouro + número + bairro + cidade/UF + CEP quando presentes (ex.: “RUA DOUTOR PLINIO MORAES, 464 – CIDADE NOVA, BELO HORIZONTE/MG – CEP 31170-170”).
    Código do Cliente: usar MATRÍCULA exatamente como aparece (ex.: “0 000 105 383 3”).
    Período de Referência / Emissão: na área “REFERÊNCIA DA CONTA”, mapear mês/ano, “Quando foi emitida?”, e “Data da apresentação”. Use “Data de Emissão” = Quando foi emitida.
    Vencimento: data na linha/coluna “VENCIMENTO”.
    Leituras do hidrômetro (m³): localizar dois padrões dd/mm/aaaa <inteiro>; a data mais antiga = Leitura Anterior, a mais recente = Leitura Atual (ex.: “01/07/2025 1058” e “31/07/2025 1092”). Não confundir com a tabela de consumo.
    Consumo Total: priorizar o valor explícito “34m3 (34.000 litros)” do mês de referência. Se não existir, calcular Leitura Atual − Leitura Anterior em m³.
    Consumo Médio Diário: na linha “SEU CONSUMO EM LITROS” do mês de referência, capturar o 3º número = litros/dia (ex.: “1.133”). Escreva “litros/dia”.
    Valores:
    Valor do Consumo (Água): linha “ABASTECIMENTO DE AGUA”.
    Taxa de Esgoto: linha “ESGOTO …”.
    TOTAL: usar o “TOTAL A PAGAR” ou o valor destacado ao fim (preferir o total final quando ambos existirem).
    Formatação:
    Números: respeitar separadores da fatura (ex.: “34.000”, “538,38”).
    Moeda: R$ e duas casas.
    Não escreva “estimado”, “aprox.” nem comentários fora de “OBSERVAÇÕES”.
    Validações (obrigatórias):
    Verificar se (Leitura Atual − Leitura Anterior) = Consumo Total (m³) quando ambos existirem; tolerância 1 m³.
    Confirmar que Consumo Médio Diário vem da tabela do mês (3º número).
    Se qualquer campo estiver ausente no texto, escreva “Não informado” (não invente).
    OBSERVAÇÕES:
    Comente brevemente se o consumo está dentro do histórico recente, acima ou abaixo (compare com meses anteriores da mesma tabela).
    Alerta de possível anomalia caso a validação de consumo não feche (>1 m³ de diferença) ou haja salto atípico (>40% vs. mediana dos 6 últimos meses).
    Adicione outras observações relevantes (ex.: “Conta com tarifa social”, “Hidrômetro novo instalado em xx/xxxx”).
    Adicione as observações presentes na fatura, se houver.
    Importante: Siga somente o texto do arquivo. Não inclua notas como “estimado”. Não mude o cabeçalho nem a ordem das seções.
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
