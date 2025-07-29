from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def modal_detector(driver, wait):
    try:
        modal = driver.find_element(By.ID, 'modalDialog')
        modal_body = modal.find_element(By.CLASS_NAME, 'modal-body')
        modal_paragraph = modal_body.find_elements(By.TAG_NAME, 'p')
        modal_footer = modal.find_element(By.CLASS_NAME, 'modal-footer')
        modal_close = modal_footer.find_element(By.TAG_NAME, 'button')
        
        for text in modal_paragraph:
            if 'Favor realizar novo logon' in text.text:
                print("Fechando modal de logon.")
                modal_close.click()
            
            if 'ERRO COPASA: Houve um erro inesperado' in text.text:
                print(f"Algum erro inesperado em {driver.current_url()}")
                modal_close.click()
                driver.navigate().refresh()

    except:
        print('Nenhum modal encontrado?')
        pass
    