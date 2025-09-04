import os
import time
import logging
from typing import Set, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException

from logoff import logoff
from back_to_list import back_to_list
from login import login_copasa_simple
from select_all import select_all_option
from database_manager import DatabaseManager
from change_archive_name import rename_all_pdfs_safe_mode
from analysis_generator import generate_reports_from_folder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_bills.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class COPASASystemChecker:
    """Classe para verificar saúde do sistema COPASA"""
    
    @staticmethod
    def verificar_estado_sistema(driver, wait, max_tentativas: int = 3) -> bool:
        """
        Verifica se o sistema COPASA está funcionando corretamente
        Returns: True se sistema OK, False se instável
        """
        for tentativa in range(max_tentativas):
            try:
                modais_erro_reais = COPASASystemChecker._detectar_modais_erro_reais(driver)
                
                if modais_erro_reais:
                    logger.warning(f"Modal de erro REAL detectado - Tentativa {tentativa + 1}")
                    COPASASystemChecker._fechar_modais(modais_erro_reais)
                    time.sleep(3)
                    continue
                
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tbIdentificador")), 10)
                except TimeoutException:
                    logger.warning("Tabela principal não encontrada")
                    if tentativa < max_tentativas - 1:
                        driver.refresh()
                        time.sleep(5)
                        continue
                    else:
                        return False
                
                loadings_ativos = driver.find_elements(By.CSS_SELECTOR, 
                    ".loading:not([style*='display: none']), .spinner:not([style*='display: none']), .fa-spinner")
                
                loadings_visiveis = [l for l in loadings_ativos if l.is_displayed()]
                
                if loadings_visiveis:
                    logger.warning("Sistema em carregamento - aguardando...")
                    time.sleep(5)
                    continue
                
                elementos_interface = driver.find_elements(By.CSS_SELECTOR, 
                    "#btnproceed, .IdentifierNumber")
                
                if len(elementos_interface) == 0:
                    logger.warning("Interface não carregada completamente")
                    driver.refresh()
                    time.sleep(5)
                    continue
                
                mensagens_erro = driver.find_elements(By.CSS_SELECTOR, 
                    ".alert-danger, .error-message, .validation-summary-errors")
                
                erros_visiveis = [erro for erro in mensagens_erro if erro.is_displayed() and erro.text.strip()]
                
                if erros_visiveis:
                    logger.warning(f"Mensagens de erro do sistema detectadas: {[e.text for e in erros_visiveis]}")
                    if tentativa < max_tentativas - 1:
                        driver.refresh()
                        time.sleep(5)
                        continue
                
                logger.info("✅ Sistema COPASA funcionando normalmente")
                return True
                
            except TimeoutException:
                logger.warning(f"Timeout ao verificar sistema - Tentativa {tentativa + 1}")
                if tentativa < max_tentativas - 1:
                    driver.refresh()
                    time.sleep(5)
                continue
                    
            except Exception as e:
                logger.error(f"Erro ao verificar estado do sistema: {str(e)}")
                if tentativa < max_tentativas - 1:
                    driver.refresh()
                    time.sleep(5)
                continue
        
        logger.error("🚫 Sistema COPASA instável após múltiplas tentativas")
        return False
    
    @staticmethod
    def _detectar_modais_erro_reais(driver) -> list:
        """
        ✅ NOVA FUNÇÃO: Detecta apenas modais de erro REAIS
        """
        modais_erro = []
        
        try:
            possíveis_modais = driver.find_elements(By.CSS_SELECTOR, 
                ".modal.show, .modal[style*='display: block'], .modal.in")
            
            for modal in possíveis_modais:
                if not modal.is_displayed():
                    continue
                
                indicadores_erro = modal.find_elements(By.CSS_SELECTOR,
                    ".alert-danger, .error, .modal-header .text-danger, .btn-danger")
                
                texto_modal = modal.text.upper() if modal.text else ""
                palavras_erro = ["ERRO", "ERROR", "FALHA", "PROBLEMA", "INVALID", "TIMEOUT", "EXCEPTION"]
                
                if indicadores_erro or any(palavra in texto_modal for palavra in palavras_erro):
                    modais_erro.append(modal)
                    logger.debug(f"Modal de erro detectado: {texto_modal[:100]}...")
            
            modais_estruturais = driver.find_elements(By.CSS_SELECTOR, 
                "#includeModalDialog, #includeModalDialogWaitWindow, div[id*='include']")
            
            modais_erro = [m for m in modais_erro if m not in modais_estruturais]
            
        except Exception as e:
            logger.debug(f"Erro ao detectar modais: {e}")
        
        return modais_erro
    
    @staticmethod
    def _fechar_modais(modais_erro):
        """Tenta fechar modais de erro"""
        for modal in modais_erro:
            try:
                botoes_fechar = modal.find_elements(By.CSS_SELECTOR, 
                    ".close, .btn-close, [data-dismiss='modal'], .fa-times, .btn-default")
                
                for botao in botoes_fechar:
                    if botao.is_displayed() and botao.is_enabled():
                        botao.click()
                        time.sleep(1)
                        logger.info("Modal de erro fechado")
                        break
                        
                else:
                    modal.send_keys(Keys.ESCAPE)
                    time.sleep(1)
                    
            except Exception as e:
                logger.debug(f"Não foi possível fechar modal: {e}")

class DownloadMonitor:
    """Monitor inteligente para downloads e loops vazios"""
    
    def __init__(self):
        self.passes_sem_resultado = 0
        self.total_processadas = 0
        self.inicio_execucao = time.time()
        
    def registrar_pass_vazio(self):
        """Registra uma passagem sem resultados"""
        self.passes_sem_resultado += 1
        
    def registrar_processamento(self):
        """Registra que uma matrícula foi processada"""
        self.passes_sem_resultado = 0
        self.total_processadas += 1
        
    def deve_pausar(self, limite_passes_vazios: int = 5) -> bool:
        """Verifica se deve pausar por muitos passes vazios"""
        return self.passes_sem_resultado >= limite_passes_vazios
        
    def log_estatisticas(self, passes_atual: int, pendentes: int):
        """Loga estatísticas de progresso"""
        if passes_atual % 10 == 0 and passes_atual > 0:
            tempo_execucao = time.time() - self.inicio_execucao
            eficiencia = (self.total_processadas / passes_atual) * 100
            
            logger.info(f"📊 Estatísticas - Pass: {passes_atual} | "
                       f"Pendentes: {pendentes} | Processadas: {self.total_processadas} | "
                       f"Eficiência: {eficiencia:.1f}% | Tempo: {tempo_execucao:.1f}s")
            
            if eficiencia < 10 and passes_atual > 20:
                logger.warning("⚠️ ALERTA: Baixa eficiência - possível problema sistêmico")

def wait_for_download(download_folder: str, timeout: int = 30) -> bool:
    """
    Aguarda conclusão de download de forma mais robusta
    """
    initial_files = set(os.listdir(download_folder))
    start_time = time.time()
    
    logger.debug(f"Aguardando download na pasta: {download_folder}")

    while time.time() - start_time < timeout:
        try:
            current_files = set(os.listdir(download_folder))
            new_files = current_files - initial_files

            if new_files:
                temp_files = [f for f in new_files if f.endswith(('.crdownload', '.part', '.tmp'))]
                
                if not temp_files:
                    logger.info(f"Download concluído: {list(new_files)}")
                    return True
                else:
                    logger.debug(f"Download em andamento: {temp_files}")
                    
        except OSError as e:
            logger.warning(f"Erro ao verificar pasta de download: {e}")
            
        time.sleep(0.5)
    
    logger.error(f"Timeout no download após {timeout}s")
    return False

def safe_rename_after_download(download_folder: str):
    """
    Renomeia arquivos com tratamento de erro mais robusto
    """
    try:
        rename_all_pdfs_safe_mode(download_folder)
        logger.debug("Arquivos renomeados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao renomear arquivos: {e}")

def _normalize_matricula(s: str) -> str:
    """Normaliza matrícula removendo caracteres não numéricos"""
    return "".join(ch for ch in str(s).strip() if ch.isdigit())

def safe_element_interaction(driver, wait, locator: Tuple, action: str = "click", 
                           max_tentativas: int = 1, timeout: int = 10):
    """
    Interação segura com elementos, com retry automático
    """
    for tentativa in range(max_tentativas):
        try:
            if action == "click":
                element = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable(locator)
                )
                element.click()
                return element
            elif action == "find":
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located(locator)
                )
                return element
                
        except (TimeoutException, StaleElementReferenceException) as e:
            if tentativa < max_tentativas - 1:
                logger.warning(f"Tentativa {tentativa + 1} falhou para {locator}: {e}")
                time.sleep(2)
                continue
            else:
                logger.error(f"Falha definitiva ao interagir com {locator}")
                raise
    
    return None

def processar_matricula_individual(driver, wait, row, db: DatabaseManager, 
                                 download_folder: str) -> Tuple[str, str, str]:
    """
    Processa uma matrícula individual
    Returns: (status, matricula, motivo)
    """
    try:
        linha_raw = row.find_element(By.CSS_SELECTOR, "span.IdentifierNumber").text
        linha = _normalize_matricula(linha_raw)
        
        logger.info(f"Processando matrícula: {linha}")
        
        if db.matricula_ja_baixada_hoje(linha):
            logger.info(f"Matrícula {linha} - JÁ BAIXADA HOJE")
            return "ja_baixada", linha, "Já baixada hoje"
        
        radio_button = row.find_element(By.CSS_SELECTOR, "input[type='radio']")
        radio_button.click()
        
        proceed_button = safe_element_interaction(driver, wait, (By.ID, "btnproceed"))
        if not proceed_button:
            return "erro", linha, "Falha ao clicar em proceed"
        
        try:
            no_debt_element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, 'OpenInvoices'))
            )
            if "NAO EXISTE DEBITOS PARA A MATRICULA INFORMADA" in no_debt_element.text.upper():
                logger.info(f"Matrícula {linha} - SEM DÉBITOS")
                db.registrar_tentativa(linha, False, "Sem débitos")
                return "sem_debitos", linha, "Sem débitos"
        except TimeoutException:
            pass
        
        download_button = safe_element_interaction(driver, wait, (By.CLASS_NAME, "fa-download"))
        if not download_button:
            return "erro", linha, "Botão de download não encontrado"
        
        download_success = wait_for_download(download_folder)
        
        if download_success:
            logger.info(f"✅ Matrícula {linha} - BAIXADA COM SUCESSO")
            db.registrar_tentativa(linha, True)
            safe_rename_after_download(download_folder)
            return "sucesso", linha, "Download realizado"
        else:
            logger.error(f"❌ Matrícula {linha} - FALHA NO DOWNLOAD")
            db.registrar_tentativa(linha, False, "Falha no download")
            return "erro_download", linha, "Falha no download"
            
    except Exception as e:
        linha_safe = linha if 'linha' in locals() else "desconhecida"
        logger.error(f"Erro ao processar matrícula {linha_safe}: {str(e)}")
        return "erro", linha_safe, f"Erro: {str(e)}"

def download_bills_by_matricula(driver, download_folder: str, matriculas, cpf: str, 
                              password: str, webmail_user: str, webmail_password: str, 
                              webmail_host: str, timeout: int = 10):
    """
    Função principal refatorada para download de faturas
    """
    RELAUNCH_TIME = int(os.getenv("RELAUNCH_TIME", "780"))
    max_passes = int(os.getenv("MAX_PASSES", "300"))
    
    wait = WebDriverWait(driver, timeout)
    selector = "#tbIdentificador tbody tr"
    db = DatabaseManager()
    monitor = DownloadMonitor()
    system_checker = COPASASystemChecker()

    matriculas_filtradas = db.filtrar_matriculas_nao_baixadas(matriculas, verificar_hoje_apenas=True)
    pending = {_normalize_matricula(m) for m in (matriculas_filtradas or []) if str(m).strip()}

    if not pending:
        logger.info("Nenhuma matrícula pendente para processar")
        return

    logger.info(f"🚀 Iniciando processamento de {len(pending)} matrículas")
    logger.debug(f"Matrículas pendentes: {sorted(pending)}")

    start_time = time.time()
    passes = 0

    while pending and passes < max_passes:
        passes += 1
        logger.debug(f"Varredura {passes}/{max_passes} - Pendentes: {len(pending)}")

        if not system_checker.verificar_estado_sistema(driver, wait):
            logger.warning("Sistema COPASA instável - aguardando recuperação...")
            time.sleep(30)
            continue

        if time.time() - start_time >= RELAUNCH_TIME:
            logger.info("🔄 Reautenticando preventivamente...")
            try:
                logoff(driver, wait)
                login_copasa_simple(driver, wait, cpf, password, webmail_user, webmail_password, webmail_host)
                select_all_option(driver)
                start_time = time.time()
                logger.info("✅ Reautenticação concluída")
            except Exception as e:
                logger.error(f"Erro na reautenticação: {e}")
                break

        if monitor.deve_pausar():
            logger.warning("🔄 Muitas passagens vazias - pausando para estabilização...")
            time.sleep(60)
            monitor.passes_sem_resultado = 0
            continue

        try:
            rows = driver.find_elements(By.CSS_SELECTOR, selector)
        except Exception as e:
            logger.error(f"Erro ao buscar elementos: {e}")
            driver.refresh()
            continue

        if len(rows) <= 0:
            logger.warning("Lista vazia - possível problema no carregamento")
            monitor.registrar_pass_vazio()
            driver.refresh()
            time.sleep(3)
            continue

        matricula_processada_nesta_pass = False
        
        for row in rows:
            try:
                linha_raw = row.find_element(By.CSS_SELECTOR, "span.IdentifierNumber").text
                linha = _normalize_matricula(linha_raw)

                if linha not in pending:
                    continue

                status, matricula_processada, motivo = processar_matricula_individual(
                    driver, wait, row, db, download_folder
                )
                
                if status in ["ja_baixada", "sem_debitos", "sucesso", "erro_download"]:
                    pending.discard(linha)
                    monitor.registrar_processamento()
                    matricula_processada_nesta_pass = True
                
                back_status = back_to_list(driver, wait)
                
                if back_status == "no_invoice":
                    logger.info(f"Matrícula {linha} - SEM FATURA DISPONÍVEL")
                    db.registrar_tentativa(linha, False, "Sem fatura disponível")
                    pending.discard(linha)
                
                break

            except (StaleElementReferenceException, NoSuchElementException) as e:
                logger.warning(f"Elemento perdido durante processamento: {e}")
                try:
                    back_to_list(driver, wait)
                except Exception:
                    pass
                matricula_processada_nesta_pass = True
                break
                
            except Exception as e:
                logger.error(f"Erro inesperado no processamento: {str(e)}")
                driver.refresh()
                matricula_processada_nesta_pass = True
                break

        if not matricula_processada_nesta_pass:
            monitor.registrar_pass_vazio()
        
        monitor.log_estatisticas(passes, len(pending))

        time.sleep(1)

    if pending:
        logger.warning(f"⚠️ Matrículas não processadas após {passes} varreduras: {sorted(pending)}")
    else:
        logger.info("🎉 Todas as matrículas foram processadas com sucesso!")

    logger.info("🔧 Executando processamento final...")
    
    try:
        rename_all_pdfs_safe_mode(download_folder)
        logger.info("✅ Arquivos renomeados")
        
        txt_folder = os.path.join(download_folder, "IGNORAR")
        relatorio_folder = os.path.join(download_folder, "Relatorios")
        generate_reports_from_folder(download_folder, txt_folder, relatorio_folder)
        logger.info("✅ Relatórios gerados com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento final: {e}")

    logger.info(f"🏁 Execução finalizada - Total processadas: {monitor.total_processadas}")