import os
from dotenv import load_dotenv

load_dotenv()

class SystemConfig:
    SYSTEM_CHECK_TIMEOUT = 3          
    ELEMENT_WAIT_TIMEOUT = 3          
    DOWNLOAD_TIMEOUT = 10             
    MODAL_CHECK_TIMEOUT = 1           
    
    MAX_RECOVERY_ATTEMPTS = 2        
    MAX_CONSECUTIVE_PROBLEMS = 4     
    EMPTY_PASSES_LIMIT = 3            
    
    RELAUNCH_TIME = int(os.getenv("RELAUNCH_TIME", "720"))  
    MAX_PASSES = int(os.getenv("MAX_PASSES", "80"))         
    
    MAX_ERRORS_PER_SESSION = 8        
    ERROR_WINDOW_TIME = 180           
    
    PASS_INTERVAL = 0.5               
    RECOVERY_INTERVAL = 1             
    STABILIZATION_WAIT = 30           
    DOWNLOAD_CHECK_INTERVAL = 0.3     
    
    STATS_LOG_INTERVAL = 5            
    
    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")
    DUPLICATES_FOLDER = "Duplicatas"
    TXT_FOLDER = "contas_txt"
    REPORTS_FOLDER = "relatorios"

class DatabaseConfig:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    RECENT_DOWNLOAD_DAYS = 5          
    CHECK_TODAY_ONLY = True           

class WebmailConfig:
    WEBMAIL_HOST = os.getenv("WEBMAIL_HOST")
    
    DEFAULT_TIMEOUT = 20
    SEARCH_TIMEOUT = 15
    EMAIL_LOAD_TIMEOUT = 10

class DriverConfig:
    @staticmethod
    def get_firefox_preferences():
        return {
            "browser.download.folderList": 2,
            "browser.download.dir": SystemConfig.DOWNLOAD_DIR,
            "browser.download.useDownloadDir": True,
            "browser.download.viewableInternally": False,
            "browser.helperApps.neverAsk.saveToDisk": 
                "application/pdf,application/zip,application/octet-stream,application/x-pdf,application/acrobat,applications/vnd.pdf,text/pdf,text/x-pdf",
            "pdfjs.disabled": True,
            "plugin.disable_full_page_plugin_for_types": "application/pdf",
            "browser.download.manager.showWhenStarting": False,
            "browser.download.manager.focusWhenStarting": False,
            "browser.download.manager.useWindow": False,
            "browser.download.manager.showAlertOnComplete": False,
            "browser.download.manager.closeWhenDone": False,
            "browser.download.manager.alertOnEXEOpen": False,
            "browser.download.manager.scanWhenDone": False,
        }
    
    @staticmethod
    def get_firefox_options():
        return [
            "--disable-blink-features=AutomationControlled",
            # "--headless"  # Descomente para modo headless
        ]

class LoggingConfig:
    LEVEL = "INFO"
    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    
    LOG_FILES = {
        'main': 'download_bills.log',
        'runner': 'runner.log',
        'system_monitor': 'system_monitor.log'
    }
    
    ENCODING = 'utf-8'

class PerformanceConfig:
    MAX_MODALS_TO_CHECK = 3           
    MAX_CLOSE_BUTTONS_PER_SELECTOR = 2  
    
    CLEAR_CACHE_INTERVAL = 50         
    
    PROCESS_PRIORITY = "normal"       

class Selectors:
    TABLE_ROWS = "#tbIdentificador tbody tr"
    RADIO_BUTTON = "input[type='radio']"
    PROCEED_BUTTON = "#btnproceed"
    DOWNLOAD_BUTTON = ".fa-download"
    BACK_BUTTON = "#btnSelect"
    
    ESSENTIAL_ELEMENTS = [
        "#tbIdentificador",
        "#btnproceed",
        ".IdentifierNumber"
    ]

    MODALS = ".modal.show, .modal[style*='display: block'], .alert-danger"
    CLOSE_BUTTONS = [
        ".modal.show .close",
        ".modal.show .btn-close", 
        ".modal.show [data-dismiss='modal']",
        ".alert-danger .close"
    ]
    
    LOADING_INDICATORS = [
        ".fa-spinner",
        ".loading:not([style*='display: none'])",
        ".spinner-border",
        "[class*='loading']:not([style*='display: none'])"
    ]
    
    NO_DEBT_ELEMENT = "#OpenInvoices"
    IDENTIFIER_NUMBER = "span.IdentifierNumber"

def validate_config():
    required_configs = [
        SystemConfig.DOWNLOAD_DIR,
        DatabaseConfig.SUPABASE_URL,
        DatabaseConfig.SUPABASE_KEY,
        WebmailConfig.WEBMAIL_HOST
    ]
    
    missing_configs = [config for config in required_configs if not config]
    
    if missing_configs:
        raise ValueError(f"Configurações obrigatórias não encontradas: {missing_configs}")
    
    return True

try:
    validate_config()
except ValueError as e:
    print(f"⚠️ Erro de configuração: {e}")
    print("📝 Verifique se o arquivo .env está configurado corretamente")