import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webmail import webmail_access
from select_agency import select_agency
from modal_detector import modal_detector

def login_copasa(driver, wait, cpf, password, webmail_user, webmail_password, webmail_host):
    print("=== INICIANDO LOGIN COPASA ===")
    
    driver.get(f"https://copasaportalprd.azurewebsites.net/Copasa.Portal/Login/index")
    
    userInput = wait.until(
        EC.element_to_be_clickable((By.ID, "cpfInput"))
    )
    userInput.send_keys(cpf)

    passwordInput = wait.until(
        EC.element_to_be_clickable((By.ID, "passwordInput"))
    )
    passwordInput.send_keys(password)

    validateLogin = wait.until(
        EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
    )
    validateLogin.click()
    
    modal_detector(driver=driver, wait=wait)
    
    token = webmail_access(driver, webmail_host, webmail_user, webmail_password)

    driver.get("https://copasaportalprd.azurewebsites.net/Copasa.Portal/Login/token")

    tokenInput = wait.until(
        EC.element_to_be_clickable((By.ID, "tokenInput"))
    )
    tokenInput.send_keys(token)

    tokenValidate = wait.until(
        EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
    )
    tokenValidate.click()
    
    modal_detector(driver=driver, wait=wait)
    
    select_agency(driver=driver, wait=wait)
    
    print(f"=== LOGIN COPASA CONCLUÍDO ===\n")
    time.sleep(1)
    listServices = driver.find_elements(By.CLASS_NAME, "centerElem")

    for service in listServices:
        if "Segunda via de contas" in service.text:
            service.click()
            break