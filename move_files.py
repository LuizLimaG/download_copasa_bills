import os
import glob
import shutil
from pathlib import Path
from datetime import datetime

class GerenciadorArquivos:
    def __init__(self):
        self.pasta_downloads = "downloads"
        self.pasta_relatorios = "relatorios"
        self.pasta_destino_arquivos = "arquivos_processados"
        self.pasta_destino_relatorios = "relatorios_finalizados"
        
    def criar_pastas_destino(self):
        try:
            Path(self.pasta_destino_arquivos).mkdir(parents=True, exist_ok=True)
            Path(self.pasta_destino_relatorios).mkdir(parents=True, exist_ok=True)
            print("✓ Pastas de destino criadas/verificadas")
        except Exception as e:
            print(f"✗ Erro ao criar pastas: {e}")
    
    def mover_arquivos_baixados(self, extensoes_permitidas=None):
        contador = 0
        erros = []
        
        print(f"\n📁 Movendo arquivos de: {self.pasta_downloads}")
        print(f"📁 Para: {self.pasta_destino_arquivos}")
        print("-" * 50)
        
        try:
            pasta_origem = Path(self.pasta_downloads)
            
            if not pasta_origem.exists():
                print(f"⚠️  Pasta {self.pasta_downloads} não encontrada!")
                return contador
            
            for arquivo in pasta_origem.iterdir():
                if arquivo.is_file():
                    if extensoes_permitidas and arquivo.suffix.lower() not in extensoes_permitidas:
                        continue
                    
                    destino = Path(self.pasta_destino_arquivos) / arquivo.name
                    
                    if destino.exists():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        nome_sem_ext = arquivo.stem
                        extensao = arquivo.suffix
                        novo_nome = f"{nome_sem_ext}_{timestamp}{extensao}"
                        destino = Path(self.pasta_destino_arquivos) / novo_nome
                    
                    try:
                        shutil.move(str(arquivo), str(destino))
                        print(f"✓ {arquivo.name} → {destino.name}")
                        contador += 1
                    except Exception as e:
                        erro_msg = f"Erro ao mover {arquivo.name}: {e}"
                        erros.append(erro_msg)
                        print(f"✗ {erro_msg}")
        
        except Exception as e:
            print(f"✗ Erro geral ao processar downloads: {e}")
        
        print(f"\n📊 Arquivos movidos: {contador}")
        if erros:
            print(f"⚠️  Erros encontrados: {len(erros)}")
        
        return contador
    
    def mover_relatorios(self, extensoes_relatorio=['.txt', '.csv', '.json', '.xml', '.log']):
        contador = 0
        erros = []
        
        print(f"\n📋 Movendo relatórios de: {self.pasta_relatorios}")
        print(f"📋 Para: {self.pasta_destino_relatorios}")
        print("-" * 50)
        
        try:
            pasta_origem = Path(self.pasta_relatorios)
            
            if not pasta_origem.exists():
                print(f"⚠️  Pasta {self.pasta_relatorios} não encontrada!")
                return contador
            
            for arquivo in pasta_origem.iterdir():
                if arquivo.is_file() and arquivo.suffix.lower() in extensoes_relatorio:
                    destino = Path(self.pasta_destino_relatorios) / arquivo.name
                    
                    if destino.exists():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        nome_sem_ext = arquivo.stem
                        extensao = arquivo.suffix
                        novo_nome = f"{nome_sem_ext}_{timestamp}{extensao}"
                        destino = Path(self.pasta_destino_relatorios) / novo_nome
                    
                    try:
                        shutil.move(str(arquivo), str(destino))
                        print(f"✓ {arquivo.name} → {destino.name}")
                        contador += 1
                    except Exception as e:
                        erro_msg = f"Erro ao mover {arquivo.name}: {e}"
                        erros.append(erro_msg)
                        print(f"✗ {erro_msg}")
        
        except Exception as e:
            print(f"✗ Erro geral ao processar relatórios: {e}")
        
        print(f"\n📊 Relatórios movidos: {contador}")
        if erros:
            print(f"⚠️  Erros encontrados: {len(erros)}")
        
        return contador
    
    def configurar_caminhos(self, pasta_downloads=None, pasta_relatorios=None, 
                          pasta_destino_arquivos=None, pasta_destino_relatorios=None):
        if pasta_downloads:
            self.pasta_downloads = pasta_downloads
        if pasta_relatorios:
            self.pasta_relatorios = pasta_relatorios
        if pasta_destino_arquivos:
            self.pasta_destino_arquivos = pasta_destino_arquivos
        if pasta_destino_relatorios:
            self.pasta_destino_relatorios = pasta_destino_relatorios
    
    def processar_tudo(self, extensoes_arquivos=None):
        print("🚀 Iniciando processo de organização de arquivos...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.criar_pastas_destino()
        
        total_arquivos = self.mover_arquivos_baixados(extensoes_arquivos)
        
        total_relatorios = self.mover_relatorios()
        
        print("\n" + "="*60)
        print("📈 RESUMO FINAL")
        print("="*60)
        print(f"📁 Arquivos movidos: {total_arquivos}")
        print(f"📋 Relatórios movidos: {total_relatorios}")
        print(f"📊 Total geral: {total_arquivos + total_relatorios}")
        print("="*60)
        print("✅ Processo concluído!")