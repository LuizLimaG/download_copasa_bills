import os 
from main import main
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
webmail_host = os.environ['webmail_host']
first_cpf = os.getenv('COPASA_USER')
second_cpf = os.getenv('COPASA_USER_DOIS')

matriculas_por_cpf = {
    first_cpf: {
        27: ['34392442', '49863660', '3320768', '235628954'], # alterar para dia 1
        2: ['169966067', '1198606', '23668058', '103267878'],
        3: ['132325195', '128133252'],
        8: ['27040862', '122089910'],
        11: ['6713062'],
        31: ['46784676'],
    },
    second_cpf: {
    }
}

today = datetime.now().day
DOWNLOAD_MODE = os.getenv("DOWNLOAD_MODE", "all")

acessos = [
    {
        'cpf': first_cpf,
        'password': os.getenv('COPASA_PASSWORD'),
        'webmail_user': os.getenv('WEBMAIL_USER'),
        'webmail_password': os.getenv('WEBMAIL_PASSWORD'),
        'matriculas_key': first_cpf
    },
    {
        'cpf': second_cpf,
        'password': os.getenv('COPASA_PASSWORD_DOIS'),
        'webmail_user': os.getenv('WEBMAIL_USER_DOIS'),
        'webmail_password': os.getenv('WEBMAIL_PASSWORD_DOIS'),
        'matriculas_key': second_cpf
    },
]

for acesso in acessos:
    cpf = acesso['cpf']
    password = acesso['password']
    webmail_user = acesso['webmail_user']
    webmail_password = acesso['webmail_password']
    matriculas_key = acesso['matriculas_key']
    
    matriculas_do_cpf = matriculas_por_cpf.get(matriculas_key, {})
    identifier = matriculas_do_cpf.get(today, None)

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