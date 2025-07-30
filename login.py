from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from webmail import webmail_access
from select_agency import select_agency
from modal_detector import modal_detector

def login_copasa(driver, wait):
    print("=== INICIANDO LOGIN COPASA ===")
    
    print("Acessando página de login...")
    driver.get("https://copasaportalprd.azurewebsites.net/Copasa.Portal/Login/index")
    
    print("Preenchendo CPF...")
    userInput = wait.until(
        EC.element_to_be_clickable((By.ID, "cpfInput"))
    )
    userInput.send_keys("90268660620")

    print("Preenchendo senha...")
    passwordInput = wait.until(
        EC.element_to_be_clickable((By.ID, "passwordInput"))
    )
    passwordInput.send_keys("@#Rintec2025")

    print("Clicando em login...")
    validateLogin = wait.until(
        EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
    )
    validateLogin.click()
    
    print("Verificando modais após login...")
    modal_detector(driver=driver, wait=wait)
    
    print("Acessando webmail para buscar token...")
    token = webmail_access(driver, "https://rintec.com.br:2096/", "contato@rintec.com.br", "@#Rintec161212")
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
    
    listServices = driver.find_elements(By.CLASS_NAME, "centerElem")

    for service in listServices:
        if "Segunda via de contas" in service.text:
            service.click()
            break