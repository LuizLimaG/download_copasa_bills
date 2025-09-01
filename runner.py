import os 
from main import main
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

today = datetime.now().day
webmail_host = os.environ['webmail_host']
cpf_contato = os.getenv('COPASA_USER_CONTATO')
cpf_financeiro = os.getenv('COPASA_USER_FINANCEIRO')

cpf_per_identifiers = {
    cpf_contato: {
        1: ['34392442', '211388494', '3250498', '49863660', '3320768', '235628954', '139834451', '23639104', '133029930', '23640148', '172284473', '120638622', '221105912', '147404983'],
        2: ['135631831', '169966097', '1198606', '23668058', '103267878', '154721956', '53380284', '48680512', '155368737'],
        3: ['132325195', '128133252'],
        8: ['27040862', '122089910'],
        11: ['6713062'],
        31: ['46784676'],
    },
    cpf_financeiro: {
    }
}

DOWNLOAD_MODE = os.getenv("DOWNLOAD_MODE", "all")

hits = [
    {
        'cpf': cpf_contato,
        'password': os.getenv('COPASA_PASSWORD_CONTATO'),
        'webmail_user': os.getenv('WEBMAIL_USER_CONTATO'),
        'webmail_password': os.getenv('WEBMAIL_PASSWORD_CONTATO'),
        'matriculas_key': cpf_contato
    },
    {
        'cpf': cpf_financeiro,
        'password': os.getenv('COPASA_PASSWORD_FINANCEIRO'),
        'webmail_user': os.getenv('WEBMAIL_USER_FINANCEIRO'),
        'webmail_password': os.getenv('WEBMAIL_PASSWORD_FINANCEIRO'),
        'matriculas_key': cpf_financeiro
    },
]

for acess in hits:
    cpf = acess['cpf']
    password = acess['password']
    webmail_user = acess['webmail_user']
    webmail_password = acess['webmail_password']
    matriculas_key = acess['matriculas_key']
    
    identifiers_for_cpf = cpf_per_identifiers.get(matriculas_key, {})
    identifier = identifiers_for_cpf.get(today, None)

    print(f"\n{'='*50}")
    print(f"🚀 Iniciando processamento para CPF {cpf}")
    print(f"{'='*50}")

    try:
        if DOWNLOAD_MODE == "matriculas" and identifier:
            print(f"🔎 Rodando CPF {cpf} para matrículas do dia {today}: {identifier}")
            main(
                cpf=cpf,
                password=password,
                webmail_user=webmail_user,
                webmail_password=webmail_password,
                webmail_host=webmail_host,
                matriculas=identifier
            )
            print(f"✅ Finalizado CPF {cpf} com sucesso.\n")
            
        elif DOWNLOAD_MODE == "matriculas" and not identifier:
            print(f"ℹ️ CPF {cpf} não possui matrículas para o dia {today}. Pulando...")
            
        else:
            print(f"🔥 Rodando CPF {cpf} para baixar todas as faturas...")
            main(
                cpf=cpf,
                password=password,
                webmail_user=webmail_user,
                webmail_password=webmail_password,
                webmail_host=webmail_host,
                matriculas=None
            )
            print(f"✅ Finalizado CPF {cpf} com sucesso.\n")
            
    except Exception as e:
        print(f"💥 CPF {cpf} falhou definitivamente: {str(e)}")
        print(f"🔄 Continuando para o próximo CPF...\n")
        continue

print("🎉 Processamento de todos os CPFs finalizado!")