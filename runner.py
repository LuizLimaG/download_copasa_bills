import os
from main import main
from dotenv import load_dotenv
from database_manager import DatabaseManager

load_dotenv()

webmail_host = os.getenv('WEBMAIL_HOST')
db = DatabaseManager()

credentials = db.get_credenciais_ativas()

for cred in credentials:
    cpf = cred['cpf']
    password = cred['password']
    webmail_user = cred['webmail_user']
    webmail_password = cred['webmail_password']
    
    identifiers = db.get_matriculas_para_cpf(cpf, incluir_pendentes=True, verificar_duplicatas=True)

    print(f"\n{'='*50}")
    print(f"🚀 Iniciando processamento para CPF {cpf}")
    print(f"🔍 Matrículas para processar: {len(identifiers)}")
    if identifiers:
        print(f"📋 Lista de matrículas: {identifiers}")
    print(f"{'='*50}")

    try:
        if identifiers:
            main(
                cpf=cpf,
                password=password,
                webmail_user=webmail_user,
                webmail_password=webmail_password,
                webmail_host=webmail_host,
                matriculas=identifiers
            )
            print(f"✅ Finalizado CPF {cpf} com sucesso.\n")
        else:
            print(f"ℹ️ CPF {cpf} não possui matrículas para processar (todas já foram baixadas ou não há matrículas agendadas para hoje).")
            
    except Exception as e:
        print(f"💥 CPF {cpf} falhou definitivamente: {str(e)}")
        print(f"🔄 Continuando para o próximo CPF...\n")
        continue

print("🎉 Processamento de todos os CPFs finalizado!")