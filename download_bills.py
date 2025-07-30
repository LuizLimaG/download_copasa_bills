import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from back_to_list import back_to_list
from modal_detector import modal_detector
from change_archive_name import rename_all_pdfs
from analysis_generator import generate_reports_from_folder
from login import login_copasa
from select_all import select_all_option
from logoff import logoff  # seu logout

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

def download_all_bills(driver, wait, download_folder):
    selector = "#tbIdentificador tbody tr"
    i = 0

    start_time = time.time()
    RELAUNCH_TIME = 13 * 60  # 13 minutos

    while True:
        rows = driver.find_elements(By.CSS_SELECTOR, selector)
        if i >= len(rows):
            break

        tempo_decorrido = time.time() - start_time
        if tempo_decorrido >= RELAUNCH_TIME:
            print("⏳ Tempo limite atingido. Reautenticando...")
            logoff(driver, wait)
            login_copasa(driver, wait)
            select_all_option(driver, wait)
            start_time = time.time()
            rows = driver.find_elements(By.CSS_SELECTOR, selector)
            continue

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
            print(f"Baixando fatura {i+1}.")
            wait_for_download(download_folder=download_folder)

        except Exception as e:
            print(f"Fatura {i+1} sem download disponível.")

        try:
            back_to_list(driver=driver, wait=wait)
        except Exception as e:
            print(f"⚠️ Falha ao voltar para lista (fatura {i}): {e}")

        i += 1

    rename_all_pdfs(download_folder)
    txt_folder = os.path.join(download_folder, "contas_txt")
    relatorio_folder = os.path.join(download_folder, "relatorios")
    generate_reports_from_folder(download_folder, txt_folder, relatorio_folder)
