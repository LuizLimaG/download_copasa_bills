import os
import time
from selenium.webdriver.common.by import By
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

def wait_for_download(download_folder, timeout=30):
    initial_files = set(os.listdir(download_folder))
    start_time = time.time()

    while time.time() - start_time < timeout:
        current_files = set(os.listdir(download_folder))
        new_files = current_files - initial_files

        if new_files:
            temp_files = [f for f in new_files if f.endswith(('.crdownload', '.part'))]
            if not temp_files:
                return True
        time.sleep(0.5)
    return False

def safe_rename_after_download(download_folder):
    try:
        rename_all_pdfs_safe_mode(download_folder)
    except Exception as e:
        print(f"Erro ao processar arquivos: {e}")

def _normalize_matricula(s: str) -> str:
    return "".join(ch for ch in str(s).strip() if ch.isdigit())

def download_bills_by_matricula(driver, download_folder, matriculas, cpf, password, webmail_user, webmail_password, webmail_host, timeout=20):
    wait = WebDriverWait(driver, timeout=timeout)
    selector = "#tbIdentificador tbody tr"
    db = DatabaseManager()

    matriculas_filtradas = db.filtrar_matriculas_nao_baixadas(matriculas, verificar_hoje_apenas=True)
    
    pending = {_normalize_matricula(m) for m in (matriculas_filtradas or []) if str(m).strip()}
    processed = set()

    if not pending:
        print("Nenhuma matrícula pendente para processar (todas já foram baixadas ou lista vazia).")
        return

    start_time = time.time()
    RELAUNCH_TIME = int(os.getenv("RELAUNCH_TIME"))
    max_passes = 300
    passes = 0
    
    print(f"Buscando {len(pending)} matrículas: {pending}\n")

    while pending and passes < max_passes:
        passes += 1
        
        print(f"Varredura {passes}/{max_passes} - Pendentes: {len(pending)}\n")

        if time.time() - start_time >= RELAUNCH_TIME:
            print("Reautenticando...")            
            logoff(driver, wait)
            login_copasa_simple(driver, wait, cpf, password, webmail_user, webmail_password, webmail_host)
            select_all_option(driver)
            start_time = time.time()

        rows = driver.find_elements(By.CSS_SELECTOR, selector)
        found_this_pass = set()
        matricula_processada_nesta_iteracao = False

        if len(rows) <= 0:
            driver.refresh()
            continue
        
        for row in rows:    
            try:
                linha_raw = row.find_element(By.CSS_SELECTOR, "span.IdentifierNumber").text
                linha = _normalize_matricula(linha_raw)

                if linha not in pending:
                    continue

                if db.matricula_ja_baixada_hoje(linha):
                    print(f"Matrícula {linha} - JÁ BAIXADA HOJE - REMOVENDO DA LISTA")
                    pending.discard(linha)
                    matricula_processada_nesta_iteracao = True
                    continue

                found_this_pass.add(linha)

                radio_button = row.find_element(By.CSS_SELECTOR, "input[type='radio']")
                radio_button.click()

                proceed_button = wait.until(EC.element_to_be_clickable((By.ID, "btnproceed")))
                proceed_button.click()

                try:
                    no_debt_element = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.ID, 'OpenInvoices'))
                    )
                    if "NAO EXISTE DEBITOS PARA A MATRICULA INFORMADA" in no_debt_element.text.upper():
                        print(f"Matrícula {linha} - SEM DÉBITOS - REMOVIDA")
                        db.registrar_tentativa(linha, False, "Sem débitos")
                        pending.discard(linha)
                        back_to_list(driver=driver, wait=wait)
                        matricula_processada_nesta_iteracao = True
                        break
                except:
                    pass

                download_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "fa-download")))
                download_button.click()
                download_success = wait_for_download(download_folder=download_folder)

                if download_success:
                    print(f"Matrícula {linha} - BAIXADA\n")
                    db.registrar_tentativa(linha, True)
                    processed.add(linha)
                    pending.discard(linha)
                    safe_rename_after_download(download_folder)
                else:
                    print(f"Matrícula {linha} - ERRO NO DOWNLOAD\n")
                    db.registrar_tentativa(linha, False, "Falha no download")
                    pending.discard(linha)
                    safe_rename_after_download(download_folder)

                back_status = back_to_list(driver=driver, wait=wait)
                
                if back_status == "no_invoice":
                    print(f"Matrícula {linha} - SEM FATURA - REMOVIDA\n")
                    db.registrar_tentativa(linha, False, "Sem fatura disponível")
                    pending.discard(linha)
                
                matricula_processada_nesta_iteracao = True
                break

            except (StaleElementReferenceException, NoSuchElementException, TimeoutException) as e:
                if 'linha' in locals():
                    print(f"Matrícula {linha} - ERRO: fatura não encontrada ou tempo esgotado\n")
                    db.registrar_tentativa(linha, False, str(e))
                    pending.discard(linha)
                try:
                    back_to_list(driver=driver, wait=wait)
                except Exception:
                    pass
                matricula_processada_nesta_iteracao = True
                break
            except Exception as e:
                print(f"Erro inesperado: {str(e)[:50]}...")
                matricula_processada_nesta_iteracao = True
                break

        if not found_this_pass and not matricula_processada_nesta_iteracao:
            remaining_pending = pending.copy()
            if not remaining_pending:
                print("Todas as matrículas foram processadas")
                break
            print(f"Nenhuma matrícula pendente encontrada nesta varredura")

        if not pending:
            break

        print(f"{"="*30}\n")

    if pending:
        print(f"Matrículas não processadas após {max_passes} varreduras: {sorted(pending)}")
    else:
        print("Todas as matrículas foram processadas!")

    print("Processamento final...")
    rename_all_pdfs_safe_mode(download_folder)
    
    try:
        txt_folder = os.path.join(download_folder, "contas_txt")
        relatorio_folder = os.path.join(download_folder, "relatorios")
        generate_reports_from_folder(download_folder, txt_folder, relatorio_folder)
        print("Relatórios gerados com sucesso!")
    except Exception as e:
        print(f"Erro ao gerar relatórios: {e}")