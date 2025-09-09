import os
import logging
from main import main
from dotenv import load_dotenv
from database_manager import DatabaseManager

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('runner.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

webmail_host = os.getenv('WEBMAIL_HOST')
db = DatabaseManager()

print(f"CURRENT DIRETORY: {os.getcwd()}")

def main_runner():
    logger.info("🚀 Iniciando sistema de download COPASA otimizado")
    
    try:
        credentials = db.get_credenciais_ativas()
        
        if not credentials:
            logger.warning("⚠️ Nenhuma credencial ativa encontrada no banco de dados")
            return
        
        logger.info(f"📋 Encontradas {len(credentials)} credenciais ativas para processar")
        
        total_processados = 0
        total_erros = 0
        
        for i, cred in enumerate(credentials, 1):
            cpf = cred['cpf']
            password = cred['password']
            webmail_user = cred['webmail_user']
            webmail_password = cred['webmail_password']
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 PROCESSANDO CREDENCIAL {i}/{len(credentials)}")
            logger.info(f"👤 CPF: {cpf}")
            logger.info(f"📧 Email: {webmail_user}")
            logger.info(f"{'='*60}")
            
            try:
                identifiers = db.get_matriculas_para_cpf(
                    cpf, 
                    incluir_pendentes=True, 
                    verificar_duplicatas=True
                )

                if not identifiers:
                    logger.info(f"ℹ️ CPF {cpf}: Nenhuma matrícula pendente para processar")
                    logger.info("   • Todas as matrículas já foram baixadas hoje")
                    logger.info("   • Ou não há matrículas agendadas para hoje")
                    continue
                
                logger.info(f"🎯 Matrículas para processar: {len(identifiers)}")
                logger.info(f"📋 Lista: {identifiers}")
                
                main(
                    cpf=cpf,
                    password=password,
                    webmail_user=webmail_user,
                    webmail_password=webmail_password,
                    webmail_host=webmail_host,
                    matriculas=identifiers
                )
                
                logger.info(f"✅ CPF {cpf} processado com sucesso!")
                total_processados += 1
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar CPF {cpf}: {str(e)}")
                logger.error(f"🔄 Continuando para próxima credencial...")
                total_erros += 1
                continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 RELATÓRIO FINAL")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Credenciais processadas com sucesso: {total_processados}")
        logger.info(f"❌ Credenciais com erro: {total_erros}")
        logger.info(f"📈 Taxa de sucesso: {(total_processados/(total_processados + total_erros)*100) if (total_processados + total_erros) > 0 else 0:.1f}%")
        logger.info(f"🎉 Processamento finalizado!")
        
    except Exception as e:
        logger.error(f"💥 Erro crítico no runner: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        main_runner()
    except KeyboardInterrupt:
        logger.warning("⚠️ Execução interrompida pelo usuário")
    except Exception as e:
        logger.error(f"💥 Erro fatal: {str(e)}")
        exit(1)