import os
import time
from selenium import webdriver
from login import login_copasa
from select_all import select_all_option
from selenium.webdriver.support.ui import WebDriverWait
from download_bills import download_all_bills, download_bills_by_matricula
from selenium.common.exceptions import TimeoutException as SeleniumTimeoutException

MAX_TENTATIVAS = 3
TIMEOUT_SEGUNDOS = 60

class CustomTimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise CustomTimeoutException("Timeout: Operação demorou mais que 60 segundos")

def create_driver():
    donwload_dir = os.getenv("DOWNLOAD_DIR")
    firefox_prefs = {
        "browser.download.folderList": 2,
        "browser.download.dir": donwload_dir,
        "browser.download.useDownloadDir": True,
        "browser.download.viewableInternally": False,
        "browser.helperApps.neverAsk.saveToDisk": 
            "application/pdf,application/zip,application/octet-stream,application/x-pdf,application/acrobat,applications/vnd.pdf,text/pdf,text/x-pdf",
        "pdfjs.disabled": True,
        "plugin.disable_full_page_plugin_for_types": "application/pdf",
        "browser.download.manager.showWhenStarting": False,
        "browser.download.manager.focusWhenStarting": False,
        "browser.download.manager.useWindow": False,
        "browser.download.manager.showAlertOnComplete": False,
        "browser.download.manager.closeWhenDone": False,
        "browser.download.manager.alertOnEXEOpen": False,
        "browser.download.manager.scanWhenDone": False,
    }

    options = webdriver.FirefoxOptions()
    for key, value in firefox_prefs.items():
        options.set_preference(key, value)

    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Firefox(options=options)
    driver.maximize_window()
    return driver

def executar_main_interno(driver, wait, cpf, password, webmail_user, webmail_password, webmail_host, matriculas, donwload_dir, callbacks=None):
    try:
        login_copasa(
            driver=driver,
            wait=wait,
            cpf=cpf,
            password=password,
            webmail_user=webmail_user,
            webmail_password=webmail_password,
            webmail_host=webmail_host
        )

        select_all_option(driver=driver)

        if matriculas:
            download_bills_by_matricula(
                driver=driver,
                download_folder=donwload_dir,
                matriculas=matriculas,
                cpf=cpf,
                password=password,
                webmail_user=webmail_user,
                webmail_password=webmail_password,
                webmail_host=webmail_host
            )
        else:
            download_all_bills(
                driver=driver,
                download_folder=donwload_dir,
                cpf=cpf,
                password=password,
                webmail_user=webmail_user,
                webmail_password=webmail_password,
                webmail_host=webmail_host
            )
        
        return True
        
    except CustomTimeoutException:
        raise
    except Exception as e:
        raise e

def main(cpf, password, webmail_user, webmail_password, webmail_host, matriculas=None, success_callback=None, failure_callback=None, no_invoice_callback=None):
    start_time = time.time()
    donwload_dir = os.getenv("DOWNLOAD_DIR")
    driver = None
    
    callbacks = {
        'success': success_callback,
        'failure': failure_callback,
        'no_invoice': no_invoice_callback
    } if any([success_callback, failure_callback, no_invoice_callback]) else None
    
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            print(f"🔄 Tentativa {tentativa}/{MAX_TENTATIVAS} para CPF {cpf}")
            
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
            driver = create_driver()
            wait = WebDriverWait(driver, 60)
            
            executar_main_interno(
                driver, wait, cpf, password, webmail_user, 
                webmail_password, webmail_host, matriculas, donwload_dir, callbacks
            )
            
            print(f"✅ Sucesso na tentativa {tentativa} para CPF {cpf}")
            break
            
        except CustomTimeoutException as e:
            print(f"⏰ {e} - Tentativa {tentativa} para CPF {cpf}")
            
            if tentativa < MAX_TENTATIVAS:
                print(f"🔄 Tentando novamente em 5 segundos...")
                time.sleep(5)
            else:
                print(f"❌ CPF {cpf} falhou após {MAX_TENTATIVAS} tentativas por timeout")
                raise
                
        except SeleniumTimeoutException as e:
            print(f"⏰ Timeout do Selenium na tentativa {tentativa} para CPF {cpf}: {str(e)}")
            
            if tentativa < MAX_TENTATIVAS:
                print(f"🔄 Tentando novamente em 5 segundos...")
                time.sleep(5)
            else:
                print(f"❌ CPF {cpf} falhou após {MAX_TENTATIVAS} tentativas por timeout do Selenium")
                raise
                
        except Exception as e:
            print(f"❌ Erro na tentativa {tentativa} para CPF {cpf}: {str(e)}")
            
            if tentativa < MAX_TENTATIVAS:
                print(f"🔄 Tentando novamente em 5 segundos...")
                time.sleep(5)
            else:
                print(f"❌ CPF {cpf} falhou após {MAX_TENTATIVAS} tentativas por erro: {str(e)}")
                raise
    
    if driver:
        try:
            driver.quit()
        except:
            pass
    
    end_time = time.time()
    total_seconds = end_time - start_time
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    print(f"⏱️ Tempo total de execução para CPF {cpf}: {minutes}min {seconds}s")
