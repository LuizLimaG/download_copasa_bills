import os 
from dotenv import load_dotenv
from main import main

load_dotenv()
webmail_host = os.environ['webmail_host']

acessos = [
    {
        'cpf': os.getenv('COPASA_USER'),
        'password': os.getenv('COPASA_PASSWORD'),
        'webmail_user': os.getenv('WEBMAIL_USER'),
        'webmail_password': os.getenv('WEBMAIL_PASSWORD')
    },
    {
        'cpf': os.getenv('COPASA_USER_DOIS'),
        'password': os.getenv('COPASA_PASSWORD_DOIS'),
        'webmail_user': os.getenv('WEBMAIL_USER_DOIS'),
        'webmail_password': os.getenv('WEBMAIL_PASSWORD_DOIS')
    },
]

for acesso in acessos:
    cpf = acesso['cpf']
    password = acesso['password']
    webmail_user = acesso['webmail_user']
    webmail_password = acesso['webmail_password']
    main(
        cpf=cpf,
        password=password,
        webmail_user=webmail_user,
        webmail_password=webmail_password,
        webmail_host=webmail_host
    )