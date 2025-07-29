from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from webmail import webmail_access
from select_agency import select_agency

def login_copasa(driver, wait):
    driver.get("https://copasaportalprd.azurewebsites.net/Copasa.Portal/Login/index")
    
    userInput = wait.until(
        EC.element_to_be_clickable((By.ID, "cpfInput"))
    )
    userInput.send_keys("90268660620")

    passwordInput = wait.until(
        EC.element_to_be_clickable((By.ID, "passwordInput"))
    )
    passwordInput.send_keys("@#Rintec2025")

    validateLogin = wait.until(
        EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
    )
    validateLogin.click()
        
    token = webmail_access(driver, "https://rintec.com.br:2096/", "contato@rintec.com.br", "@#Rintec161212")

    driver.get("https://copasaportalprd.azurewebsites.net/Copasa.Portal/Login/token")

    tokenInput = wait.until(
        EC.element_to_be_clickable((By.ID, "tokenInput"))
    )
    tokenInput.send_keys(token)

    tokenValidate = wait.until(
        EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
    )
    tokenValidate.click()
    
    select_agency(driver=driver, wait=wait)

    