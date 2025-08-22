import time

start_time = time.time()

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from login import login_copasa
from select_all import select_all_option
from download_bills import download_all_bills

firefox_prefs = {
    # Configurações básicas de download
    "browser.download.folderList": 2,
    "browser.download.dir": r"C:\Users\luizz\PROJETOS\antisuicidio\contas",
    "browser.download.useDownloadDir": True,
    "browser.download.viewableInternally": False,
    
    # Tipos de arquivo para download automático
    "browser.helperApps.neverAsk.saveToDisk": 
        "application/pdf,application/zip,application/octet-stream,application/x-pdf,application/acrobat,applications/vnd.pdf,text/pdf,text/x-pdf",
    
    # Desabilitar visualizador PDF interno
    "pdfjs.disabled": True,
    "plugin.disable_full_page_plugin_for_types": "application/pdf",
    
    # Configurações adicionais
    "browser.download.manager.showWhenStarting": False,
    "browser.download.manager.focusWhenStarting": False,
    "browser.download.manager.useWindow": False,
    "browser.download.manager.showAlertOnComplete": False,
    "browser.download.manager.closeWhenDone": False,
    
    # Segurança
    "browser.download.manager.alertOnEXEOpen": False,
    "browser.download.manager.scanWhenDone": False,
}

options = webdriver.FirefoxOptions()

for key, value in firefox_prefs.items():
    options.set_preference(key, value)

options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Firefox(options=options)
driver.maximize_window()

def main(cpf, password, webmail_user, webmail_password, webmail_host):
    wait = WebDriverWait(driver, 60)

    login_copasa(driver=driver, wait=wait, cpf=cpf, password=password, webmail_user=webmail_user, webmail_password=webmail_password, webmail_host=webmail_host)
    select_all_option(driver=driver)
    download_all_bills(driver=driver, download_folder=r"C:\Users\luizz\PROJETOS\antisuicidio\contas")

    end_time = time.time()
    total_seconds = end_time - start_time
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    print(f"Tempo total de execução: {minutes}min {seconds}s")