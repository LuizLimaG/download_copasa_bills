import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webmail import webmail_access
from select_agency import select_agency

def login_copasa(driver, wait, cpf, password, webmail_user, webmail_password, webmail_host, max_retries=3):  
    for attempt in range(1, max_retries + 1):
        print(f"=== TENTATIVA DE LOGIN {attempt}/{max_retries} ===")
        
        try:
            driver.get("https://copasaportalprd.azurewebsites.net/Copasa.Portal/Login/index")
            time.sleep(2)
            
            print("Preenchendo CPF...")
            userInput = wait.until(EC.element_to_be_clickable((By.ID, "cpfInput")))
            userInput.clear()
            userInput.send_keys(cpf)
            
            print("Preenchendo senha...")
            passwordInput = wait.until(EC.element_to_be_clickable((By.ID, "passwordInput")))
            passwordInput.clear()
            passwordInput.send_keys(password)
            
            print("Enviando credenciais...")
            validateLogin = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary")))
            validateLogin.click()
            
            try:
                error_selectors = [
                    ".alert-danger",
                    ".error-message", 
                    ".invalid-feedback",
                    "[class*='error']"
                ]
                
                for selector in error_selectors:
                    error_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if error_elements:
                        error_text = error_elements[0].text.lower()
                        if any(word in error_text for word in ['inválido', 'incorreto', 'erro', 'invalid', 'error']):
                            raise Exception(f"Erro de credenciais detectado: {error_text}")
                            
            except Exception as e:
                if "credenciais" in str(e):
                    print(f"Erro de credenciais na tentativa {attempt}: {e}")
                    if attempt < max_retries:
                        print("Aguardando antes da próxima tentativa...")
                        time.sleep(5)
                        continue
                    else:
                        print("Máximo de tentativas atingido para credenciais.")
                        return False
            
            print("Buscando token no webmail...")
            token = webmail_access(driver, webmail_host, webmail_user, webmail_password)
            
            if not token:
                raise Exception("Não foi possível obter token do webmail")
            driver.get("https://copasaportalprd.azurewebsites.net/Copasa.Portal/Login/token")
            time.sleep(2)
            
            print(f"Preenchendo token: {token}")
            tokenInput = wait.until(EC.element_to_be_clickable((By.ID, "tokenInput")))
            tokenInput.clear()
            time.sleep(0.5)
            tokenInput.send_keys(token)
            
            print("Validando token...")
            tokenValidate = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary")))
            tokenValidate.click()
            time.sleep(3)
            
            try:
                error_elements = driver.find_elements(By.CSS_SELECTOR, ".alert-danger, .error-message")
                if error_elements:
                    error_text = error_elements[0].text.lower()
                    if 'token' in error_text or 'código' in error_text:
                        raise Exception(f"Erro de token detectado: {error_text}")
            except Exception as e:
                if "token" in str(e):
                    print(f"Erro de token na tentativa {attempt}: {e}")
                    if attempt < max_retries:
                        print("Aguardando antes da próxima tentativa...")
                        time.sleep(5)
                        continue
                    else:
                        print("Máximo de tentativas atingido para token.")
                        return False
            
            print("Selecionando agência...")
            select_agency(driver=driver, wait=wait)
            
            print("Procurando serviço 'Segunda via de contas'...")
            services = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "centerElem")))
            service_found = False
            
            for service in services:
                if "Pagamentos e 2ª via de contas" in service.text:
                    service.click()
                    print("Acessou 'Segunda via de contas'")
                    service_found = True
                    break
            
            if not service_found:
                raise Exception("Serviço 'Segunda via de contas' não encontrado")
            
            print(f"=== LOGIN COPASA CONCLUÍDO COM SUCESSO (Tentativa {attempt}) ===\n")
            return True
            
        except TimeoutException as e:
            print(f"Timeout na tentativa {attempt}: {e}")
            if attempt < max_retries:
                print(f"Aguardando {attempt * 5} segundos antes da próxima tentativa...")
                time.sleep(attempt * 5)
            else:
                print("Máximo de tentativas atingido devido a timeout.")
                return False
                
        except WebDriverException as e:
            print(f"Erro do WebDriver na tentativa {attempt}: {e}")
            if attempt < max_retries:
                print("Tentando recarregar a página...")
                try:
                    driver.refresh()
                    time.sleep(3)
                except:
                    pass
                time.sleep(5)
            else:
                print("Máximo de tentativas atingido devido a erro do WebDriver.")
                return False
                
        except Exception as e:
            print(f"Erro inesperado na tentativa {attempt}: {e}")
            if attempt < max_retries:
                print(f"Aguardando {attempt * 3} segundos antes da próxima tentativa...")
                time.sleep(attempt * 3)
            else:
                print("Máximo de tentativas atingido devido a erro inesperado.")
                return False
        
        finally:
            time.sleep(1)
    
    print("=== FALHA NO LOGIN APÓS TODAS AS TENTATIVAS ===")
    return False


def login_copasa_simple(driver, wait, cpf, password, webmail_user, webmail_password, webmail_host):
    return login_copasa(driver, wait, cpf, password, webmail_user, webmail_password, webmail_host, max_retries=3)