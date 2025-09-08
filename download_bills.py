import os
import time
import logging
from enum import Enum
from typing import Set, Optional, Tuple, Dict
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

class SystemState(Enum):
    HEALTHY = "healthy"
    SLOW = "slow" 
    MODAL_ERROR = "modal_error"
    SESSION_EXPIRED = "session_expired"
    NO_RESPONSE = "no_response"
    CRITICAL_ERROR = "critical_error"

class RecoveryAction(Enum):
    WAIT = "wait"
    REFRESH = "refresh"
    CLOSE_MODAL = "close_modal" 
    RELOGIN = "relogin"
    SKIP_MATRICULA = "skip_matricula"
    ABORT = "abort"

class COPASASystemMonitor:
    def __init__(self, max_wait_time: int = 3, max_recovery_attempts: int = 2):
        self.max_wait_time = max_wait_time
        self.max_recovery_attempts = max_recovery_attempts
        self.recovery_stats = {
            RecoveryAction.WAIT: 0,
            RecoveryAction.REFRESH: 0,
            RecoveryAction.CLOSE_MODAL: 0,
            RecoveryAction.RELOGIN: 0,
            RecoveryAction.SKIP_MATRICULA: 0
        }
        self.consecutive_problems = 0
        self.last_problem_time = 0
        
    def detect_system_state(self, driver) -> SystemState:
        try:
            modal_state = self._quick_modal_check(driver)
            if modal_state != SystemState.HEALTHY:
                return modal_state
            
            essential_elements = self._check_essential_elements(driver)
            if not essential_elements:
                return SystemState.NO_RESPONSE
                
            if self._detect_slowness(driver):
                return SystemState.SLOW
                
            self.consecutive_problems = 0
            return SystemState.HEALTHY
            
        except Exception as e:
            logger.error(f"Erro na detecção de estado: {e}")
            return SystemState.CRITICAL_ERROR
    
    def _quick_modal_check(self, driver) -> SystemState:
        try:
            modals = driver.find_elements(By.CSS_SELECTOR, 
                ".modal.show, .modal[style*='display: block'], .alert-danger")
            
            for modal in modals[:3]:
                if not modal.is_displayed():
                    continue
                    
                modal_text = modal.text.upper()
                error_keywords = ["ERRO", "ERROR", "FALHA", "TIMEOUT", "SESSÃO", "SESSION"]
                if any(keyword in modal_text for keyword in error_keywords):
                    if "SESSÃO" in modal_text or "SESSION" in modal_text:
                        return SystemState.SESSION_EXPIRED
                    return SystemState.MODAL_ERROR
                    
        except Exception:
            pass
        
        return SystemState.HEALTHY
    
    def _check_essential_elements(self, driver) -> bool:
        try:
            essential_selectors = [
                "#tbIdentificador",
                "#btnproceed",       
                ".IdentifierNumber" 
            ]
            
            for selector in essential_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        return True
                except:
                    continue
                    
            return False
        except:
            return False
    
    def _detect_slowness(self, driver) -> bool:
        try:
            loading_selectors = [
                ".fa-spinner",
                ".loading:not([style*='display: none'])",
                ".spinner-border",
                "[class*='loading']:not([style*='display: none'])"
            ]
            
            for selector in loading_selectors:
                loadings = driver.find_elements(By.CSS_SELECTOR, selector)
                if any(l.is_displayed() for l in loadings):
                    return True
                    
        except Exception:
            pass
        return False
    
    def get_recovery_action(self, state: SystemState, attempt: int) -> RecoveryAction:
        current_time = time.time()
        
        if self.consecutive_problems > 3:
            if current_time - self.last_problem_time < 30:
                return RecoveryAction.RELOGIN
        
        recovery_map = {
            SystemState.MODAL_ERROR: [RecoveryAction.CLOSE_MODAL, RecoveryAction.REFRESH],
            SystemState.SESSION_EXPIRED: [RecoveryAction.RELOGIN],
            SystemState.SLOW: [RecoveryAction.WAIT, RecoveryAction.REFRESH],
            SystemState.NO_RESPONSE: [RecoveryAction.REFRESH, RecoveryAction.RELOGIN],
            SystemState.CRITICAL_ERROR: [RecoveryAction.REFRESH, RecoveryAction.ABORT]
        }
        
        actions = recovery_map.get(state, [RecoveryAction.REFRESH])
        
        if attempt < len(actions):
            return actions[attempt]
        else:
            return RecoveryAction.SKIP_MATRICULA if attempt < self.max_recovery_attempts else RecoveryAction.ABORT
    
    def execute_recovery(self, driver, wait, action: RecoveryAction) -> bool:
        self.consecutive_problems += 1
        self.last_problem_time = time.time()
        self.recovery_stats[action] += 1
        
        try:
            if action == RecoveryAction.CLOSE_MODAL:
                return self._close_modals_fast(driver)
            
            elif action == RecoveryAction.REFRESH:
                logger.info("🔄 Refresh da página...")
                driver.refresh()
                time.sleep(2)
                return True
            
            elif action == RecoveryAction.WAIT:
                logger.info("⏳ Aguardando sistema estabilizar...")
                time.sleep(3)
                return True
            
            elif action == RecoveryAction.RELOGIN:
                logger.info("🔐 Relogin necessário...")
                return False
            
            elif action == RecoveryAction.SKIP_MATRICULA:
                logger.warning("⏭️ Pulando matrícula atual...")
                return False
            
            elif action == RecoveryAction.ABORT:
                logger.error("🛑 Abortando execução...")
                return False
                
        except Exception as e:
            logger.error(f"Erro na recuperação {action}: {e}")
            return False
            
        return True
    
    def _close_modals_fast(self, driver) -> bool:
        try:
            close_selectors = [
                ".modal.show .close",
                ".modal.show .btn-close", 
                ".modal.show [data-dismiss='modal']",
                ".alert-danger .close"
            ]
            
            closed_any = False
            for selector in close_selectors:
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons[:2]:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            closed_any = True
                            time.sleep(0.5)
                            break
                except:
                    continue
            
            if not closed_any:
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(0.5)
                closed_any = True
            
            logger.info(f"🔐 Modais fechados: {closed_any}")
            return closed_any
            
        except Exception as e:
            logger.debug(f"Erro ao fechar modais: {e}")
            return False
    
    def log_stats(self):
        if sum(self.recovery_stats.values()) > 0:
            logger.info(f"📊 Estatísticas de recuperação: {dict(self.recovery_stats)}")

class DownloadMonitor:
    def __init__(self):
        self.passes_sem_resultado = 0
        self.total_processadas = 0
        self.inicio_execucao = time.time()
        
    def registrar_pass_vazio(self):
        self.passes_sem_resultado += 1
        
    def registrar_processamento(self):
        self.passes_sem_resultado = 0
        self.total_processadas += 1
        
    def deve_pausar(self, limite_passes_vazios: int = 3) -> bool:
        return self.passes_sem_resultado >= limite_passes_vazios
        
    def log_estatisticas(self, passes_atual: int, pendentes: int):
        if passes_atual % 5 == 0 and passes_atual > 0:
            tempo_execucao = time.time() - self.inicio_execucao
            eficiencia = (self.total_processadas / passes_atual) * 100 if passes_atual > 0 else 0
            
            logger.info(f"📊 Pass: {passes_atual} | Pendentes: {pendentes} | "
                       f"Processadas: {self.total_processadas} | Eficiência: {eficiencia:.1f}%")

class OptimizedDownloadManager:
    def __init__(self, download_folder: str):
        self.download_folder = download_folder
        self.monitor = COPASASystemMonitor()
        self.processed_count = 0
        self.error_count = 0
        self.start_time = time.time()
        
    def process_matricula_with_recovery(self, driver, wait, row, db, matricula: str) -> Tuple[str, str]:
        max_attempts = 2
        
        for attempt in range(max_attempts):
            system_state = self.monitor.detect_system_state(driver)
            
            if system_state != SystemState.HEALTHY:
                logger.warning(f"Sistema não saudável: {system_state.value}")
                
                recovery_action = self.monitor.get_recovery_action(system_state, attempt)
                
                if recovery_action == RecoveryAction.RELOGIN:
                    return "relogin_needed", "Sistema necessita relogin"
                
                elif recovery_action == RecoveryAction.SKIP_MATRICULA:
                    return "skipped", "Matrícula pulada por instabilidade"
                
                elif recovery_action == RecoveryAction.ABORT:
                    return "abort", "Execução abortada"
                
                recovery_success = self.monitor.execute_recovery(driver, wait, recovery_action)
                
                if not recovery_success and recovery_action not in [RecoveryAction.WAIT]:
                    continue
                
                time.sleep(1)
                system_state = self.monitor.detect_system_state(driver)
                if system_state != SystemState.HEALTHY:
                    continue
            
            try:
                return self._process_single_matricula(driver, wait, row, db, matricula)
            
            except Exception as e:
                logger.warning(f"Erro no processamento (tentativa {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(1)
                    continue
                else:
                    return "error", f"Erro após {max_attempts} tentativas: {str(e)}"
        
        return "failed", "Falha após todas as tentativas de recuperação"
    
    def _process_single_matricula(self, driver, wait, row, db, matricula: str) -> Tuple[str, str]:
        try:
            radio_button = WebDriverWait(driver, 3).until(
                lambda d: row.find_element(By.CSS_SELECTOR, "input[type='radio']")
            )
            radio_button.click()
            
            proceed_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "btnproceed"))
            )
            proceed_button.click()
            
            try:
                no_debt_element = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.ID, 'OpenInvoices'))
                )
                if "NAO EXISTE DEBITOS" in no_debt_element.text.upper():
                    db.registrar_tentativa(matricula, False, "Sem débitos")
                    return "no_debt", "Sem débitos"
            except TimeoutException:
                pass
            
            try:
                download_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "fa-download"))
                )
                download_button.click()
                
                if self._wait_download_optimized():
                    db.registrar_tentativa(matricula, True)
                    self.processed_count += 1
                    return "success", "Download realizado"
                else:
                    db.registrar_tentativa(matricula, False, "Falha no download")
                    return "download_failed", "Falha no download"
                    
            except TimeoutException:
                db.registrar_tentativa(matricula, False, "Sem fatura disponível")
                return "no_invoice", "Sem fatura disponível"
            
        except Exception as e:
            self.error_count += 1
            return "error", f"Erro no processamento: {str(e)}"
    
    def _wait_download_optimized(self, timeout: int = 10) -> bool:
        initial_files = set(os.listdir(self.download_folder))
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                current_files = set(os.listdir(self.download_folder))
                new_files = current_files - initial_files
                
                if new_files:
                    temp_files = [f for f in new_files if f.endswith(('.crdownload', '.part', '.tmp'))]
                    if not temp_files:
                        return True
                        
            except OSError:
                pass
            time.sleep(0.3)
        
        return False
    
    def should_continue(self) -> bool:
        runtime = time.time() - self.start_time
        
        if self.error_count > 8 and runtime < 180:
            logger.error("🛑 Muitos erros em pouco tempo - parando execução")
            return False
        
        if self.monitor.consecutive_problems > 4:
            logger.error("🛑 Sistema muito instável - parando execução")
            return False
            
        return True
    
    def log_final_stats(self):
        runtime = time.time() - self.start_time
        logger.info(f"📈 Estatísticas finais:")
        logger.info(f"   Processadas: {self.processed_count}")
        logger.info(f"   Erros: {self.error_count}")
        logger.info(f"   Tempo: {runtime:.1f}s")
        self.monitor.log_stats()

def _normalize_matricula(s: str) -> str:
    return "".join(ch for ch in str(s).strip() if ch.isdigit())

def download_bills_by_matricula(driver, download_folder: str, matriculas, cpf: str, 
                              password: str, webmail_user: str, webmail_password: str, 
                              webmail_host: str, timeout: int = 10):
    
    RELAUNCH_TIME = int(os.getenv("RELAUNCH_TIME", "720")) 
    max_passes = int(os.getenv("MAX_PASSES", "80"))
    
    wait = WebDriverWait(driver, timeout)
    selector = "#tbIdentificador tbody tr"
    db = DatabaseManager()
    download_manager = OptimizedDownloadManager(download_folder)
    download_monitor = DownloadMonitor()
    
    matriculas_filtradas = db.filtrar_matriculas_nao_baixadas(matriculas, verificar_hoje_apenas=True)
    pending = {_normalize_matricula(m) for m in (matriculas_filtradas or []) if str(m).strip()}

    if not pending:
        logger.info("Nenhuma matrícula pendente para processar")
        return

    logger.info(f"🚀 SISTEMA OTIMIZADO - Processando {len(pending)} matrículas")
    logger.debug(f"Matrículas pendentes: {sorted(pending)}")

    start_time = time.time()
    session_start = time.time()
    passes = 0

    while pending and passes < max_passes and download_manager.should_continue():
        passes += 1
        logger.debug(f"🔄 Pass {passes}/{max_passes} - Pendentes: {len(pending)}")

        if time.time() - session_start >= RELAUNCH_TIME:
            logger.info("🔄 Relogin preventivo (12 min)...")
            try:
                logoff(driver, wait)
                login_copasa_simple(driver, wait, cpf, password, webmail_user, webmail_password, webmail_host)
                select_all_option(driver)
                session_start = time.time()
                logger.info("✅ Relogin preventivo concluído")
            except Exception as e:
                logger.error(f"Erro no relogin preventivo: {e}")
                break

        system_state = download_manager.monitor.detect_system_state(driver)
        if system_state not in [SystemState.HEALTHY, SystemState.SLOW]:
            recovery_action = download_manager.monitor.get_recovery_action(system_state, 0)
            
            if recovery_action == RecoveryAction.RELOGIN:
                logger.info("🔐 Sistema requer relogin...")
                try:
                    logoff(driver, wait)
                    login_copasa_simple(driver, wait, cpf, password, webmail_user, webmail_password, webmail_host)
                    select_all_option(driver)
                    session_start = time.time()
                    continue
                except Exception as e:
                    logger.error(f"Erro no relogin requerido: {e}")
                    break
            
            elif recovery_action == RecoveryAction.ABORT:
                logger.error("🛑 Sistema em estado crítico - abortando")
                break
            
            else:
                download_manager.monitor.execute_recovery(driver, wait, recovery_action)
                continue

        if download_monitor.deve_pausar():
            logger.warning("🔄 Muitas passagens vazias - aguardando estabilização...")
            time.sleep(30)
            download_monitor.passes_sem_resultado = 0
            continue

        try:
            rows = driver.find_elements(By.CSS_SELECTOR, selector)
        except Exception as e:
            logger.error(f"Erro ao buscar elementos: {e}")
            driver.refresh()
            time.sleep(2)
            continue

        if len(rows) <= 0:
            logger.warning("Lista vazia - possível problema no carregamento")
            download_monitor.registrar_pass_vazio()
            driver.refresh()
            time.sleep(2)
            continue

        matricula_processada_nesta_pass = False
        
        for row in rows:
            try:
                linha_raw = row.find_element(By.CSS_SELECTOR, "span.IdentifierNumber").text
                linha = _normalize_matricula(linha_raw)

                if linha not in pending:
                    continue

                status, message = download_manager.process_matricula_with_recovery(
                    driver, wait, row, db, linha
                )
                
                if status == "relogin_needed":
                    logger.info("🔐 Relogin solicitado pelo monitor...")
                    try:
                        logoff(driver, wait)
                        login_copasa_simple(driver, wait, cpf, password, webmail_user, webmail_password, webmail_host)
                        select_all_option(driver)
                        session_start = time.time()
                        break
                    except Exception as e:
                        logger.error(f"Erro no relogin solicitado: {e}")
                        pending.discard(linha)
                        break

                elif status == "abort":
                    logger.error("🛑 Abortando por solicitação do monitor")
                    pending.clear()
                    break

                elif status in ["success", "no_debt", "no_invoice", "skipped"]:
                    pending.discard(linha)
                    download_monitor.registrar_processamento()
                    matricula_processada_nesta_pass = True
                    logger.info(f"✅ {linha}: {message}")

                elif status in ["download_failed", "error", "failed"]:
                    pending.discard(linha)
                    logger.error(f"❌ {linha}: {message}")
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
            download_monitor.registrar_pass_vazio()
        
        download_monitor.log_estatisticas(passes, len(pending))

        time.sleep(0.5)

    if pending:
        logger.warning(f"⚠️ Matrículas não processadas após {passes} passes: {sorted(pending)}")
    else:
        logger.info("🎉 Todas as matrículas foram processadas com sucesso!")

    logger.info("🔧 Executando processamento final...")
    
    try:
        rename_all_pdfs_safe_mode(download_folder)
        logger.info("✅ Arquivos renomeados")
        
        txt_folder = os.path.join(download_folder, "contas_txt")
        relatorio_folder = os.path.join(download_folder, "relatorios")
        generate_reports_from_folder(download_folder, txt_folder, relatorio_folder)
        logger.info("✅ Relatórios gerados com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento final: {e}")

    download_manager.log_final_stats()
    logger.info(f"🏁 Execução finalizada - Total: {download_monitor.total_processadas} processadas")