import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def logoff(driver, wait):
    show_logout = wait.until(
        EC.element_to_be_clickable((By.ID, "dropdownMenuLink"))
    )
    show_logout.click()
    show_logout.click()

    time.sleep(1)
    logout_button = driver.find_elements(By.CLASS_NAME, "dropdown-item")
    for btn in logout_button:
        if "Sair" in btn.text:
            btn.click()
            break