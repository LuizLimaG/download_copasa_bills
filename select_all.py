from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def select_all_option(driver, timeout=60):
    wait = WebDriverWait(driver=driver, timeout=timeout)
    select = wait.until(
        EC.element_to_be_clickable((By.CLASS_NAME, "custom-select"))
    )
    select.click()

    options = driver.find_elements(By.TAG_NAME, 'option')

    for option in options:
        if "Todos" in option.text:
            option.click()
            break