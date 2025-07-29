from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from select_all import select_all_option

def back_to_list(driver, wait):
    back_button = wait.until(
        EC.element_to_be_clickable((By.ID, 'btnSelect'))
    )
    back_button.click()
    
    select_all_option(driver=driver)