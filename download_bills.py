import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from back_to_list import back_to_list
from modal_detector import modal_detector
from change_archive_name import rename_all_pdfs
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

def download_all_bills(driver, wait, download_folder):
    selector = "#tbIdentificador tbody tr"
    
    i = 0

    while i < len(driver.find_elements(By.CSS_SELECTOR, selector)):
        
        modal_detector(driver=driver, wait=wait)
        rows = driver.find_elements(By.CSS_SELECTOR, selector)
        current_row = rows[i]
        
        time.sleep(1)
        radio_button = current_row.find_element(By.CSS_SELECTOR, "input[type='radio']")
        radio_button.click()
        
        proceed_button = wait.until(
            EC.element_to_be_clickable((By.ID, "btnproceed"))
        )
        proceed_button.click()
                
        try: 
            modal_detector(driver=driver, wait=wait)
            download_button = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "fa-download"))
            )
            download_button.click()
            wait_for_download(download_folder=download_folder)
        except:
            pass
        
        modal_detector(driver=driver, wait=wait)
        back_to_list(driver=driver, wait=wait)
        i += 1
        
    rename_all_pdfs(download_folder)    
    txt_folder = os.path.join(download_folder, "contas_txt")
    relatorio_folder = os.path.join(download_folder, "relatorios")
    generate_reports_from_folder(download_folder, txt_folder, relatorio_folder)