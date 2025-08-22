import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webmail import webmail_access
from select_agency import select_agency
from modal_detector import modal_detector

def login_copasa(driver, wait, cpf, password, webmail_user, webmail_password, webmail_host):
    print("=== INICIANDO LOGIN COPASA ===")
    
    print("Acessando página de login...")
    driver.get("https://copasaportalprd.azurewebsites.net/Copasa.Portal/Login/index")
    
    print("Preenchendo CPF...")
    userInput = wait.until(
        EC.element_to_be_clickable((By.ID, "cpfInput"))
    )
    userInput.send_keys(cpf)

    print("Preenchendo senha...")
    passwordInput = wait.until(
        EC.element_to_be_clickable((By.ID, "passwordInput"))
    )
    passwordInput.send_keys(password)

    print("Clicando em login...")
    validateLogin = wait.until(
        EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
    )
    validateLogin.click()
    
    print("Verificando modais após login...")
    modal_detector(driver=driver, wait=wait)
    
    print("Acessando webmail para buscar token...")
    token = webmail_access(driver, webmail_host, webmail_user, webmail_password)
    print(f"Token obtido: {token}")

    print("Acessando página de token...")
    driver.get("https://copasaportalprd.azurewebsites.net/Copasa.Portal/Login/token")

    print("Preenchendo token...")
    tokenInput = wait.until(
        EC.element_to_be_clickable((By.ID, "tokenInput"))
    )
    tokenInput.send_keys(token)

    print("Validando token...")
    tokenValidate = wait.until(
        EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
    )
    tokenValidate.click()
    
    print("Verificando modais após token...")
    modal_detector(driver=driver, wait=wait)
    
    print("Selecionando agência...")
    select_agency(driver=driver, wait=wait)
    
    print("=== LOGIN COPASA CONCLUÍDO ===")
    time.sleep(1)
    listServices = driver.find_elements(By.CLASS_NAME, "centerElem")

    for service in listServices:
        if "Segunda via de contas" in service.text:
            service.click()
            break