from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

def select_agency(driver, wait):
    agency = wait.until(
        EC.element_to_be_clickable((By.CLASS_NAME, "centerElem"))
    )
    agency.click()