import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from login import login_copasa
from select_all import select_all_option

def logoff(driver, wait):
    try:
        show_logout = wait.until(
        EC.element_to_be_clickable((By.ID, "spUserName"))
        )
        time.sleep(1)
        
        show_logout.click()
        show_logout.click()

        time.sleep(2)
        
        logout_button = driver.find_elements(By.CLASS_NAME, "dropdown-item")
        
        for btn in logout_button:
            if "Sair" in btn.text:
                btn.click()
                break

        time.sleep(1)
        login_copasa(driver, wait)
        select_all_option(driver)
    except Exception as e:
        print("Erro ao tentar fazer logoff e relogar:", e) 