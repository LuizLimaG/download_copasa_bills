"""
Utilitários para debug, manutenção e análise do sistema COPASA otimizado
"""
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from database_manager import DatabaseManager
from config import SystemConfig, LoggingConfig

class DebugUtils:
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def analyze_download_patterns(self, days: int = 7) -> Dict:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            response = self.db.supabase.table('tentativas_download').select('*').gte('data_tentativa', start_date.date()).execute()
            data = response.data
            
            total_tentativas = len(data)
            sucessos = len([d for d in data if d.get('sucesso')])
            erros = total_tentativas - sucessos
            
            daily_stats = {}
            for record in data:
                day = record.get('data_tentativa', '')
                if day not in daily_stats:
                    daily_stats[day] = {'total': 0, 'sucessos': 0, 'erros': 0}
                daily_stats[day]['total'] += 1
                if record.get('sucesso'):
                    daily_stats[day]['sucessos'] += 1
                else:
                    daily_stats[day]['erros'] += 1
            
            return {
                'periodo': f'{days} dias',
                'total_tentativas': total_tentativas,
                'sucessos': sucessos,
                'erros': erros,
                'taxa_sucesso': (sucessos / total_tentativas * 100) if total_tentativas > 0 else 0,
                'estatisticas_diarias': daily_stats
            }
        except Exception as e:
            return {'erro': f'Erro ao analisar: {str(e)}'}
    
    def check_pending_matriculas(self, cpf: Optional[str] = None) -> Dict:
        try:
            if cpf:
                matriculas = self.db.get_matriculas_para_cpf(cpf, incluir_pendentes=True, verificar_duplicatas=True)
                return {
                    'cpf': cpf,
                    'matriculas_pendentes': len(matriculas),
                    'lista': matriculas
                }
            else:
                credentials = self.db.get_credenciais_ativas()
                resultado = {}
                for cred in credentials:
                    cpf = cred['cpf']
                    matriculas = self.db.get_matriculas_para_cpf(cpf, incluir_pendentes=True, verificar_duplicatas=True)
                    resultado[cpf] = {
                        'matriculas_pendentes': len(matriculas),
                        'lista': matriculas[:5] + ['...'] if len(matriculas) > 5 else matriculas
                    }
                return resultado
        except Exception as e:
            return {'erro': f'Erro ao verificar pendências: {str(e)}'}
    
    def analyze_error_patterns(self, days: int = 3) -> Dict:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            response = self.db.supabase.table('tentativas_download').select('*').eq('sucesso', False).gte('data_tentativa', start_date.date()).execute()
            errors = response.data
            
            if not errors:
                return {'message': 'Nenhum erro encontrado no período'}
            
            error_types = {}
            for error in errors:
                error_msg = error.get('erro', 'Erro desconhecido')
                error_types[error_msg] = error_types.get(error_msg, 0) + 1
            
            sorted_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)
            
            return {
                'periodo': f'{days} dias',
                'total_erros': len(errors),
                'tipos_erro': dict(sorted_errors),
                'erro_mais_comum': sorted_errors[0] if sorted_errors else None
            }
        except Exception as e:
            return {'erro': f'Erro ao analisar padrões: {str(e)}'}

class FileUtils:
    @staticmethod
    def clean_download_folder(days_old: int = 30) -> Dict:
        download_dir = Path(SystemConfig.DOWNLOAD_DIR)
        if not download_dir.exists():
            return {'erro': 'Pasta de download não existe'}
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        removed_files = []
        total_size_freed = 0
        
        for file_path in download_dir.glob('**/*'):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    size = file_path.stat().st_size
                    total_size_freed += size
                    removed_files.append(str(file_path.name))
                    try:
                        file_path.unlink()
                    except Exception as e:
                        print(f"Erro ao remover {file_path}: {e}")
        
        return {
            'arquivos_removidos': len(removed_files),
            'espaco_liberado_mb': round(total_size_freed / 1024 / 1024, 2),
            'arquivos': removed_files[:10] + ['...'] if len(removed_files) > 10 else removed_files
        }
    
    @staticmethod
    def count_files_by_type() -> Dict:
        download_dir = Path(SystemConfig.DOWNLOAD_DIR)
        if not download_dir.exists():
            return {'erro': 'Pasta de download não existe'}
        
        file_counts = {}
        total_size = 0
        
        for file_path in download_dir.glob('**/*'):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                size = file_path.stat().st_size
                
                if ext not in file_counts:
                    file_counts[ext] = {'count': 0, 'size_mb': 0}
                
                file_counts[ext]['count'] += 1
                file_counts[ext]['size_mb'] += size / 1024 / 1024
                total_size += size
        
        for ext in file_counts:
            file_counts[ext]['size_mb'] = round(file_counts[ext]['size_mb'], 2)
        
        return {
            'tipos_arquivo': file_counts,
            'tamanho_total_mb': round(total_size / 1024 / 1024, 2)
        }
    
    @staticmethod
    def find_duplicate_pdfs() -> List[str]:
        download_dir = Path(SystemConfig.DOWNLOAD_DIR)
        if not download_dir.exists():
            return []
        
        pdf_files = list(download_dir.glob('*.pdf'))
        file_sizes = {}
        duplicates = []
        
        for pdf_file in pdf_files:
            size = pdf_file.stat().st_size
            if size in file_sizes:
                duplicates.append(f"{pdf_file.name} (mesmo tamanho que {file_sizes[size]})")
            else:
                file_sizes[size] = pdf_file.name
        
        return duplicates

class LogAnalyzer:
    @staticmethod
    def analyze_recent_logs(hours: int = 24) -> Dict:
        log_file = Path(LoggingConfig.LOG_FILES['main'])
        if not log_file.exists():
            return {'erro': 'Arquivo de log não encontrado'}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            recent_lines = []
            error_count = 0
            warning_count = 0
            info_count = 0
            
            for line in lines:
                try:
                    timestamp_str = line.split(' - ')[0]
                    log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                    
                    if log_time >= cutoff_time:
                        recent_lines.append(line.strip())
                        
                        if 'ERROR' in line:
                            error_count += 1
                        elif 'WARNING' in line:
                            warning_count += 1
                        elif 'INFO' in line:
                            info_count += 1
                            
                except (ValueError, IndexError):
                    continue
            
            return {
                'periodo': f'{hours} horas',
                'total_logs': len(recent_lines),
                'erros': error_count,
                'avisos': warning_count,
                'infos': info_count,
                'ultimas_linhas': recent_lines[-10:] if recent_lines else []
            }
            
        except Exception as e:
            return {'erro': f'Erro ao analisar logs: {str(e)}'}
    
    @staticmethod
    def find_error_patterns() -> Dict:
        log_file = Path(LoggingConfig.LOG_FILES['main'])
        if not log_file.exists():
            return {'erro': 'Arquivo de log não encontrado'}
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            error_patterns = {}
            
            for line in lines:
                if 'ERROR' in line:
                    parts = line.split(' - ')
                    if len(parts) >= 3:
                        error_msg = parts[2].strip()
                        import re
                        generalized = re.sub(r'\d+', 'X', error_msg)
                        error_patterns[generalized] = error_patterns.get(generalized, 0) + 1
            
            sorted_patterns = sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)
            
            return {
                'padroes_erro': dict(sorted_patterns),
                'erro_mais_comum': sorted_patterns[0] if sorted_patterns else None
            }
            
        except Exception as e:
            return {'erro': f'Erro ao analisar padrões: {str(e)}'}

class SystemHealthChecker:
    def __init__(self):
        self.debug = DebugUtils()
    
    def full_health_check(self) -> Dict:
        results = {}
        
        results['config'] = self._check_config()
        
        results['files'] = self._check_files()
        
        results['database'] = self._check_database()
        
        results['logs'] = self._check_logs()
        
        issues = []
        for category, data in results.items():
            if isinstance(data, dict) and data.get('status') == 'error':
                issues.append(f"{category}: {data.get('message', 'Erro desconhecido')}")
        
        results['overall'] = {
            'status': 'healthy' if not issues else 'warning' if len(issues) < 3 else 'critical',
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }
        
        return results
    
    def _check_config(self) -> Dict:
        try:
            from config import validate_config
            validate_config()
            return {'status': 'ok', 'message': 'Configuração válida'}
        except Exception as e:
            return {'status': 'error', 'message': f'Erro de configuração: {str(e)}'}
    
    def _check_files(self) -> Dict:
        download_dir = Path(SystemConfig.DOWNLOAD_DIR)
        
        if not download_dir.exists():
            return {'status': 'error', 'message': 'Pasta de download não existe'}
        
        required_folders = [
            SystemConfig.TXT_FOLDER,
            SystemConfig.REPORTS_FOLDER,
            SystemConfig.DUPLICATES_FOLDER
        ]
        
        missing_folders = []
        for folder in required_folders:
            folder_path = download_dir / folder
            if not folder_path.exists():
                missing_folders.append(folder)
        
        if missing_folders:
            return {'status': 'warning', 'message': f'Pastas ausentes: {missing_folders}'}
        else:
            return {'status': 'ok', 'message': 'Estrutura de pastas OK'}
    
    def _check_database(self) -> Dict:
        try:
            credentials = self.debug.db.get_credenciais_ativas()
            return {'status': 'ok', 'message': f'{len(credentials)} credenciais ativas'}
        except Exception as e:
            return {'status': 'error', 'message': f'Erro de banco: {str(e)}'}
    
    def _check_logs(self) -> Dict:
        log_analysis = LogAnalyzer.analyze_recent_logs(1)
        
        if 'erro' in log_analysis:
            return {'status': 'warning', 'message': 'Logs não disponíveis'}
        
        error_count = log_analysis.get('erros', 0)
        if error_count > 10:
            return {'status': 'warning', 'message': f'{error_count} erros na última hora'}
        else:
            return {'status': 'ok', 'message': f'{error_count} erros na última hora'}

def main_debug():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python utils.py <comando>")
        print("Comandos disponíveis:")
        print("  health - Verificação de saúde completa")
        print("  pending - Lista matrículas pendentes")
        print("  errors - Análise de erros")
        print("  files - Análise de arquivos")
        print("  logs - Análise de logs")
        print("  clean - Limpa arquivos antigos")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'health':
        checker = SystemHealthChecker()
        result = checker.full_health_check()
        print(f"\n🏥 VERIFICAÇÃO DE SAÚDE DO SISTEMA")
        print(f"={'=' * 50}")
        for category, data in result.items():
            if category != 'overall':
                status_emoji = '✅' if data.get('status') == 'ok' else '⚠️' if data.get('status') == 'warning' else '❌'
                print(f"{status_emoji} {category.upper()}: {data.get('message', 'N/A')}")
        
        overall = result.get('overall', {})
        status_emoji = '🟢' if overall.get('status') == 'healthy' else '🟡' if overall.get('status') == 'warning' else '🔴'
        print(f"\n{status_emoji} STATUS GERAL: {overall.get('status', 'unknown').upper()}")
        if overall.get('issues'):
            print("Problemas encontrados:")
            for issue in overall['issues']:
                print(f"  • {issue}")
    
    elif command == 'pending':
        debug = DebugUtils()
        result = debug.check_pending_matriculas()
        print(f"\n📋 MATRÍCULAS PENDENTES")
        print(f"={'=' * 50}")
        for cpf, data in result.items():
            if cpf != 'erro':
                print(f"CPF {cpf}: {data['matriculas_pendentes']} pendentes")
                if data['lista']:
                    print(f"  Exemplos: {', '.join(map(str, data['lista'][:3]))}")
    
    elif command == 'errors':
        debug = DebugUtils()
        result = debug.analyze_error_patterns()
        print(f"\n❌ ANÁLISE DE ERROS")
        print(f"={'=' * 50}")
        if 'erro' in result:
            print(f"Erro: {result['erro']}")
        else:
            print(f"Período: {result.get('periodo', 'N/A')}")
            print(f"Total de erros: {result.get('total_erros', 0)}")
            tipos = result.get('tipos_erro', {})
            for erro, count in list(tipos.items())[:5]:
                print(f"  • {erro}: {count}x")
    
    elif command == 'files':
        result = FileUtils.count_files_by_type()
        print(f"\n📁 ANÁLISE DE ARQUIVOS")
        print(f"={'=' * 50}")
        if 'erro' in result:
            print(f"Erro: {result['erro']}")
        else:
            print(f"Tamanho total: {result['tamanho_total_mb']} MB")
            for ext, data in result['tipos_arquivo'].items():
                ext_name = ext if ext else 'sem extensão'
                print(f"  {ext_name}: {data['count']} arquivos ({data['size_mb']} MB)")
    
    elif command == 'logs':
        result = LogAnalyzer.analyze_recent_logs()
        print(f"\n📝 ANÁLISE DE LOGS")
        print(f"={'=' * 50}")
        if 'erro' in result:
            print(f"Erro: {result['erro']}")
        else:
            print(f"Período: {result['periodo']}")
            print(f"Total: {result['total_logs']} logs")
            print(f"Erros: {result['erros']}, Avisos: {result['avisos']}, Infos: {result['infos']}")
            if result['ultimas_linhas']:
                print("\nÚltimas linhas:")
                for line in result['ultimas_linhas'][-3:]:
                    print(f"  {line}")
    
    elif command == 'clean':
        result = FileUtils.clean_download_folder()
        print(f"\n🧹 LIMPEZA DE ARQUIVOS")
        print(f"={'=' * 50}")
        if 'erro' in result:
            print(f"Erro: {result['erro']}")
        else:
            print(f"Arquivos removidos: {result['arquivos_removidos']}")
            print(f"Espaço liberado: {result['espaco_liberado_mb']} MB")
    
    else:
        print(f"Comando '{command}' não reconhecido")

if __name__ == "__main__":
    main_debug()