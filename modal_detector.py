import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def modal_detector(driver, wait, timeout=5):
    """
    Detecta e trata modais no sistema.
    
    - Fecha modais de erro/alerta automaticamente.
    - Atualiza a página somente quando necessário.
    """

    try:
        include_modal_dialog = wait.until(
            EC.presence_of_element_located((By.ID, "includeModalDialog")),
            message="Nenhum modal detectado."
        )

        modal_title = include_modal_dialog.find_element(By.CLASS_NAME, "modal-title")
        modal_footer = include_modal_dialog.find_element(By.CLASS_NAME, "modal-footer")
        modal_buttons = modal_footer.find_elements(By.CLASS_NAME, "btn")

        title_text = modal_title.text.strip().upper()

        if "ERRO" in title_text or "ALERTA" in title_text:
            print(f"⚠️ Modal detectado: {title_text}")

            for btn in modal_buttons:
                if "OK" in btn.text.upper():
                    print("✅ Fechando modal...")
                    btn.click()
                    time.sleep(1)
                    if "ERRO" in title_text:
                        driver.refresh()
                    break
        else:
            print(f"ℹ️  Modal detectado mas ignorado: {title_text}")

    except TimeoutException:
        return
    except NoSuchElementException:
        return
    except Exception as e:
        print(f"❌ Erro inesperado no modal_detector: {e}")
        return
