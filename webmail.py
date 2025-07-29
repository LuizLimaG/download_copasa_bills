import time
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException, WebDriverException


class WebmailTokenExtractor:
    """Classe especializada para extração de tokens de autenticação via webmail"""
    
    DEFAULT_TIMEOUT = 20
    SEARCH_TIMEOUT = 15
    EMAIL_LOAD_TIMEOUT = 10
    
    SELECTORS = {
        'login': {
            'username': (By.ID, "user"),
            'password': (By.ID, "pass"),
            'submit': (By.ID, "login_submit")
        },
        'search': {
            'form': (By.ID, "mailsearchform")
        },
        'email': {
            'message_row': "//tr[contains(@class, 'unread')]//span[contains(text(), 'Código') and contains(text(), 'COPASA')]/..",
            'iframe': (By.ID, "messagecontframe"),
            'token': (By.CLASS_NAME, "v1code")
        }
    }
    
    def __init__(self, host: str, username: str, password: str):
        """
        Inicializa o extrator de tokens
        Args:
            host: URL do webmail
            username: Email do usuário
            password: Senha do email
        """
        self.host = host
        self.username = username
        self.password = password
        
        if not all([self.host, self.username, self.password]):
            raise ValueError("Parâmetros obrigatórios: host, username e password")
        
        self.driver = None
        self.wait = None
    
    def _setup_wait(self, driver: WebDriver) -> None:
        self.driver = driver
        self.wait = WebDriverWait(driver, self.DEFAULT_TIMEOUT)
    
    def _safe_click(self, locator: tuple, timeout: int = None) -> bool:
        try:
            timeout = timeout or self.DEFAULT_TIMEOUT
            element = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(locator))
            element.click()
            return True
        except TimeoutException:
            print(f"⏰ Timeout ao tentar clicar em {locator}")
            return False
    
    def _safe_send_keys(self, locator: tuple, text: str, timeout: int = None) -> bool:
        try:
            timeout = timeout or self.DEFAULT_TIMEOUT
            element = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))
            element.clear()
            element.send_keys(text)
            return True
        except TimeoutException:
            print(f"⏰ Timeout ao enviar texto para {locator}")
            return False
    
    def _wait_for_page_load(self, expected_element: tuple = None) -> bool:
        try:
            if expected_element:
                self.wait.until(EC.presence_of_element_located(expected_element))
            else:
                self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            return True
        except TimeoutException:
            print("⏰ Timeout no carregamento da página")
            return False
    
    def login_to_webmail(self) -> bool:
        try:
            print(f"🌐 Acessando webmail: {self.host}")
            self.driver.get(self.host)
            self.driver.maximize_window()
            
            if not self._wait_for_page_load(self.SELECTORS['login']['username']):
                return False
            
            print("👤 Inserindo credenciais...")
            if not self._safe_send_keys(self.SELECTORS['login']['username'], self.username):
                return False
            if not self._safe_send_keys(self.SELECTORS['login']['password'], self.password):
                return False
            return self._safe_click(self.SELECTORS['login']['submit']) and \
                   self._wait_for_page_load(self.SELECTORS['search']['form'])
        except WebDriverException as e:
            print(f"❌ Erro do WebDriver durante login: {e}")
            return False
    
    def search_copasa_email(self) -> bool:
        try:
            print("🔍 Buscando email da COPASA...")
            search_input = WebDriverWait(self.driver, self.SEARCH_TIMEOUT).until(
                EC.element_to_be_clickable(self.SELECTORS['search']['form'])
            )
            time.sleep(2)
            search_input.clear()
            search_input.send_keys("crm.acesso@copasa.com.br")
            search_input.send_keys(Keys.ENTER)
            
            found_email = WebDriverWait(self.driver, self.SEARCH_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, self.SELECTORS['email']['message_row']))
            )
            found_email.click()
            return True
        except TimeoutException:
            print("⏰ Timeout - email não encontrado")
            return False
    
    def extract_token_from_email(self) -> Optional[str]:
        try:
            iframe = WebDriverWait(self.driver, self.EMAIL_LOAD_TIMEOUT).until(
                EC.presence_of_element_located(self.SELECTORS['email']['iframe'])
            )
            self.driver.switch_to.frame(iframe)
            
            token_element = WebDriverWait(self.driver, self.EMAIL_LOAD_TIMEOUT).until(
                EC.presence_of_element_located(self.SELECTORS['email']['token'])
            )
            token = token_element.text.strip()
            self.driver.switch_to.default_content()
            return token
        except TimeoutException:
            self.driver.switch_to.default_content()
            return None
    
    def get_authentication_token(self, driver: WebDriver) -> Optional[str]:
        print("🚀 Iniciando extração de token COPASA...")
        self._setup_wait(driver)
        if not self.login_to_webmail():
            return None
        if not self.search_copasa_email():
            return None
        return self.extract_token_from_email()


def webmail_access(driver: WebDriver, host: str, email_user: str, email_password: str) -> Optional[str]:
    """
    Função de acesso rápido ao webmail.
    """
    try:
        extractor = WebmailTokenExtractor(host, email_user, email_password)
        return extractor.get_authentication_token(driver)
    except Exception as e:
        print(f"❌ Erro na função webmail_access: {e}")
        return None