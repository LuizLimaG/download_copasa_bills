import shutil
import os
from pathlib import Path
from datetime import datetime

def mover_arquivos_e_relatorios():
    """Script simples para mover arquivos baixados e relatórios"""
    
    # SEUS CAMINHOS (ajuste conforme necessário)
    pasta_downloads = r"C:\Users\User\Documents\Automacao\download_copasa_bills\Faturas"
    pasta_relatorios = r"C:\Users\User\Documents\Automacao\download_copasa_bills\Faturas\Relatorios - FATURAS"
    
    # DESTINOS (crie essas pastas ou ajuste os caminhos)
    pasta_destino_arquivos = r"z:\RINTEC - 01 - GERAL\RINTEC - COPASA TESTE\Faturas"
    pasta_destino_relatorios = r"z:\RINTEC - 01 - GERAL\RINTEC - COPASA TESTE\Relatorios"
    
    print("🚀 INICIANDO MOVIMENTAÇÃO DE ARQUIVOS")
    print("=" * 50)
    
    # Criar pastas de destino
    try:
        Path(pasta_destino_arquivos).mkdir(parents=True, exist_ok=True)
        Path(pasta_destino_relatorios).mkdir(parents=True, exist_ok=True)
        print("✅ Pastas de destino criadas/verificadas")
    except Exception as e:
        print(f"❌ Erro ao criar pastas: {e}")
        return
    
    total_movidos = 0
    
    # MOVER ARQUIVOS DA PASTA DOWNLOADS
    print(f"\n📁 Movendo arquivos de: {pasta_downloads}")
    print(f"📁 Para: {pasta_destino_arquivos}")
    print("-" * 40)
    
    try:
        for arquivo in Path(pasta_downloads).iterdir():
            # Só pegar arquivos (não pastas)
            if arquivo.is_file():
                destino = Path(pasta_destino_arquivos) / arquivo.name
                
                # Se arquivo já existe, adicionar timestamp
                if destino.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nome_base = arquivo.stem
                    extensao = arquivo.suffix
                    novo_nome = f"{nome_base}_{timestamp}{extensao}"
                    destino = Path(pasta_destino_arquivos) / novo_nome
                
                try:
                    shutil.move(str(arquivo), str(destino))
                    print(f"✅ Movido: {arquivo.name} → {destino.name}")
                    total_movidos += 1
                except Exception as e:
                    print(f"❌ Erro ao mover {arquivo.name}: {e}")
                    
    except Exception as e:
        print(f"❌ Erro ao processar pasta downloads: {e}")
    
    # MOVER RELATÓRIOS
    print(f"\n📋 Movendo relatórios de: {pasta_relatorios}")
    print(f"📋 Para: {pasta_destino_relatorios}")
    print("-" * 40)
    
    try:
        if Path(pasta_relatorios).exists():
            for relatorio in Path(pasta_relatorios).iterdir():
                # Só pegar arquivos
                if relatorio.is_file():
                    destino = Path(pasta_destino_relatorios) / relatorio.name
                    
                    # Se arquivo já existe, adicionar timestamp
                    if destino.exists():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        nome_base = relatorio.stem
                        extensao = relatorio.suffix
                        novo_nome = f"{nome_base}_{timestamp}{extensao}"
                        destino = Path(pasta_destino_relatorios) / novo_nome
                    
                    try:
                        shutil.move(str(relatorio), str(destino))
                        print(f"✅ Movido: {relatorio.name} → {destino.name}")
                        total_movidos += 1
                    except Exception as e:
                        print(f"❌ Erro ao mover {relatorio.name}: {e}")
        else:
            print("⚠️ Pasta de relatórios não encontrada")
            
    except Exception as e:
        print(f"❌ Erro ao processar relatórios: {e}")
    
    # RESULTADO FINAL
    print("\n" + "=" * 50)
    print("📊 RESULTADO FINAL")
    print("=" * 50)
    print(f"📁 Total de arquivos movidos: {total_movidos}")
    if total_movidos > 0:
        print("✅ Movimentação concluída com sucesso!")
        print(f"\n📂 Arquivos movidos para: {pasta_destino_arquivos}")
        print(f"📂 Relatórios movidos para: {pasta_destino_relatorios}")
    else:
        print("⚠️ Nenhum arquivo foi movido")
        print("   - Verifique se há arquivos nas pastas de origem")
        print("   - Verifique as permissões")
        print("=" * 50)