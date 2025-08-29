import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException

from logoff import logoff
from login import login_copasa_simple
from back_to_list import back_to_list
from select_all import select_all_option
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

def download_all_bills(driver, download_folder, cpf, password, webmail_user, webmail_password, webmail_host, timeout=20):
    wait = WebDriverWait(driver, timeout=timeout)
    selector = "#tbIdentificador tbody tr"
    i = 0

    start_time = time.time()
    RELAUNCH_TIME = int(os.getenv("RELAUNCH_TIME"))

    rows = driver.find_elements(By.CSS_SELECTOR, selector)
    total_rows = len(rows)
    
    print(f"Iniciando download de {total_rows} faturas\n")
    
    while i < total_rows:
        rows = driver.find_elements(By.CSS_SELECTOR, selector)

        tempo_decorrido = time.time() - start_time
        if tempo_decorrido >= RELAUNCH_TIME:
            print(f"\nReautenticando...\n")           
            logoff(driver, wait)
            login_copasa_simple(driver, wait, cpf, password, webmail_user, webmail_password, webmail_host)
            select_all_option(driver)
            start_time = time.time()
            rows = driver.find_elements(By.CSS_SELECTOR, selector)

        if i >= len(rows):
            print(f"Índice {i} maior que número de linhas disponíveis ({len(rows)}). Finalizando.")
            break

        download_success = False
        try:
            current_row = rows[i]
            radio_button = current_row.find_element(By.CSS_SELECTOR, "input[type='radio']")
            radio_button.click()
            
            proceed_button = wait.until(
                EC.element_to_be_clickable((By.ID, "btnproceed"))
            )
            proceed_button.click()
            
            download_button = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "fa-download"))
            )
            download_button.click()
            
            download_success = wait_for_download(download_folder=download_folder)
            
        except Exception as e:
            print(f"\nFatura {i+1}/{total_rows} - Erro: fatura não encontrada ou tempo esgotado")

        status = "OK" if download_success else "ERRO"
        print(f"\n[{i+1}/{total_rows}] {status}")
        
        safe_rename_after_download(download_folder)

        try:
            back_to_list(driver=driver, wait=wait)
        except Exception:
            pass
        
        i += 1
    
    print("Downloads concluídos! Gerando relatórios...")
    safe_rename_after_download(download_folder)
    
    try:
        txt_folder = os.path.join(download_folder, "contas_txt")
        relatorio_folder = os.path.join(download_folder, "relatorios")
        generate_reports_from_folder(download_folder, txt_folder, relatorio_folder)
        print("Relatórios gerados com sucesso!")
    except Exception as e:
        print(f"Erro ao gerar relatórios: {e}")


def _normalize_matricula(s: str) -> str:
    return "".join(ch for ch in str(s).strip() if ch.isdigit())

def download_bills_by_matricula(driver, download_folder, matriculas, cpf, password, webmail_user, webmail_password, webmail_host, timeout=20):
    wait = WebDriverWait(driver, timeout=timeout)
    selector = "#tbIdentificador tbody tr"

    pending = {_normalize_matricula(m) for m in (matriculas or []) if str(m).strip()}
    processed = set()
    failed_attempts = {}
    removed_matriculas = set()

    if not pending:
        print("Nenhuma matrícula fornecida.")
        return

    start_time = time.time()
    RELAUNCH_TIME = int(os.getenv("RELAUNCH_TIME"))
    max_passes = 50
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

        for row in rows:
            try:
                linha_raw = row.find_element(By.CSS_SELECTOR, "span.IdentifierNumber").text
                linha = _normalize_matricula(linha_raw)

                if linha not in pending or linha in removed_matriculas:
                    continue

                found_this_pass.add(linha)
                
                failed_attempts[linha] = failed_attempts.get(linha, 0)
                
                if failed_attempts[linha] >= 3:
                    print(f"Matrícula {linha} - REMOVIDA PERMANENTEMENTE\n")
                    pending.discard(linha)
                    removed_matriculas.add(linha)
                    matricula_processada_nesta_iteracao = True
                    break

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
                        pending.discard(linha)
                        removed_matriculas.add(linha)
                        back_to_list(driver=driver, wait=wait)
                        matricula_processada_nesta_iteracao = True
                        break
                except:
                    pass

                download_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "fa-download")))
                download_button.click()
                ok = wait_for_download(download_folder=download_folder)

                if ok:
                    print(f"Matrícula {linha} - BAIXADA\n")
                    processed.add(linha)
                    pending.discard(linha)
                    failed_attempts.pop(linha, None)
                    safe_rename_after_download(download_folder)
                    matricula_processada_nesta_iteracao = True
                else:
                    failed_attempts[linha] += 1
                    print(f"Matrícula {linha} - FALHA ({failed_attempts[linha]}/3)\n")
                    if failed_attempts[linha] >= 3:
                        print(f"Matrícula {linha} - REMOVIDA PERMANENTEMENTE\n")
                        pending.discard(linha)
                        removed_matriculas.add(linha)
                    safe_rename_after_download(download_folder)

                back_status = back_to_list(driver=driver, wait=wait)
                
                if back_status == "no_invoice":
                    print(f"Matrícula {linha} - SEM FATURA - REMOVIDA\n")
                    pending.discard(linha)
                    removed_matriculas.add(linha)
                
                matricula_processada_nesta_iteracao = True
                break

            except (StaleElementReferenceException, NoSuchElementException, TimeoutException) as e:
                if 'linha' in locals():
                    failed_attempts[linha] = failed_attempts.get(linha, 0) + 1
                    print(f"Matrícula {linha} - ERRO ({failed_attempts[linha]}/3): fatura não encontrada ou tempo esgotado")
                    if failed_attempts[linha] >= 3:
                        print(f"Matrícula {linha} - REMOVIDA PERMANENTEMENTE\n")
                        pending.discard(linha)
                        removed_matriculas.add(linha)
                safe_rename_after_download(download_folder)
                try:
                    back_to_list(driver=driver, wait=wait)
                except Exception:
                    pass
                matricula_processada_nesta_iteracao = True
                break
            except Exception as e:
                print(f"Erro inesperado: {str(e)[:50]}...")
                safe_rename_after_download(download_folder)
                matricula_processada_nesta_iteracao = True
                break

        for matricula, attempts in list(failed_attempts.items()):
            if attempts >= 3 and matricula in pending:
                print(f"FORÇAR REMOÇÃO: Matrícula {matricula}")
                pending.discard(matricula)
                removed_matriculas.add(matricula)

        if not found_this_pass and not matricula_processada_nesta_iteracao:
            remaining_pending = pending - removed_matriculas
            if not remaining_pending:
                print("Todas as matrículas foram processadas ou removidas")
                break
            print(f"Nenhuma matrícula pendente encontrada nesta varredura")

        if not pending:
            break

        print(f"DEBUG - Pendentes: {sorted(pending)}, Removidas: {sorted(removed_matriculas)}")

    if pending:
        print(f"Matrículas não processadas após {max_passes} varreduras: {sorted(pending)}")
    else:
        print("Todas as matrículas foram processadas!")

    print("Processamento final...")
    safe_rename_after_download(download_folder)
    
    try:
        txt_folder = os.path.join(download_folder, "contas_txt")
        relatorio_folder = os.path.join(download_folder, "relatorios")
        generate_reports_from_folder(download_folder, txt_folder, relatorio_folder)
        print("Relatórios gerados com sucesso!")
    except Exception as e:
        print(f"Erro ao gerar relatórios: {e}")