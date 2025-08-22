from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time

def modal_detector(driver, wait):
    try:
        include_modal_dialog = driver.find_element(By.ID, 'includeModalDialog')
        modal_title = include_modal_dialog.find_element(By.CLASS_NAME, 'modal-title')
        modal_footer = include_modal_dialog.find_element(By.CLASS_NAME, 'modal-footer')
        modal_close = modal_footer.find_elements(By.CLASS_NAME, 'btn')

        if 'ERRO' in modal_title.text.upper():
            print("Modal de erro detectado.")
            for btn in modal_close:
                if 'OK' in btn.text.upper():
                    print("✅ Fechando modal...")
                    btn.click()
                    time.sleep(1)
                    driver.refresh()
                    break
        if 'Alerta' in modal_title.text:
            print("Modal de erro detectado.")
            for btn in modal_close:
                if 'Ok' in btn.text:
                    print("✅ Fechando modal...")
                    btn.click()
                    time.sleep(1)
                    driver.refresh()
                    break
        else:
            print('Nenhum modal nocivo foi encontrado.')

    except NoSuchElementException:
        print('Nenhum modal encontrado')
    except:
        print('Erro ao encontrar o modal')
