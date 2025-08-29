from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from select_all import select_all_option

def back_to_list(driver, wait):
    no_invoice_detected = False
    
    try:
        try:
            fast_wait = WebDriverWait(driver, 3)
            container = fast_wait.until(
                EC.visibility_of_element_located((By.ID, 'OpenInvoices'))
            )
            text = container.text.strip().upper()
            if "NAO EXISTE DEBITOS PARA A MATRICULA INFORMADA" in text:
                no_invoice_detected = True
        except:
            pass
        
        back_button = wait.until(
            EC.element_to_be_clickable((By.ID, 'btnSelect'))
        )
        back_button.click()
    except:
        pass

    select_all_option(driver=driver)
    
    if no_invoice_detected:
        return "no_invoice"
    else:
        return "success"