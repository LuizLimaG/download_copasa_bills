import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import List, Dict, Optional, Tuple

load_dotenv()

class DatabaseManager:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)
        
    def _extract_matriculas(self, response):
        return [
            item['matriculas']['numero']
            for item in response.data
            if item.get('matriculas') and item['matriculas'].get('numero')
        ]

    def get_credenciais_ativas(self) -> List[Dict]:
        response = self.supabase.table('credenciais').select('*').eq('ativo', True).execute()
        return response.data

    def get_matriculas_por_dia(self, dia: int, cpf: str = None) -> List[str]:
        if cpf:
            cred_response = self.supabase.table('credenciais').select('id').eq('cpf', cpf).single().execute()
            credencial_id = cred_response.data['id']

            response = (
                self.supabase.table('cronograma_matriculas')
                .select('matriculas(numero)')
                .eq('dia_mes', dia)
                .eq('matriculas.ativo', True)
                .eq('matriculas.credencial_id', credencial_id)
                .execute()
            )
        else:
            response = (
                self.supabase.table('cronograma_matriculas')
                .select('matriculas(numero)')
                .eq('dia_mes', dia)
                .eq('matriculas.ativo', True)
                .execute()
        )
            
        return self._extract_matriculas(response)

    def matricula_ja_baixada_hoje(self, matricula: str) -> bool:
        """Verifica se uma matrícula já foi baixada com sucesso hoje"""
        hoje = datetime.now().date()
        
        response = (
            self.supabase.table('tentativas_download')
            .select('*')
            .eq('matricula_numero', matricula)
            .eq('sucesso', True)
            .eq('data_tentativa', hoje)
            .execute()
        )
        
        return len(response.data) > 0

    def matricula_ja_baixada_recentemente(self, matricula: str, dias: int = 1) -> bool:
        """Verifica se uma matrícula já foi baixada com sucesso nos últimos X dias"""
        data_limite = datetime.now() - timedelta(days=dias)
        
        response = (
            self.supabase.table('tentativas_download')
            .select('*')
            .eq('matricula_numero', matricula)
            .eq('sucesso', True)
            .gte('data_tentativa', data_limite.date())
            .execute()
        )
        
        return len(response.data) > 0

    def get_matriculas_pendentes(self, dias_atras: int = 5, cpf: str = None) -> List[str]:
        data_limite = datetime.now() - timedelta(days=dias_atras)

        subquery = self.supabase.table('tentativas_download').select('matricula_numero')
        subquery = subquery.eq('sucesso', True).gte('data_tentativa', data_limite.date())
        response_sucesso = subquery.execute()
        matriculas_com_sucesso = {item['matricula_numero'] for item in response_sucesso.data}

        if cpf:
            cred_response = self.supabase.table('credenciais').select('id').eq('cpf', cpf).single().execute()
            credencial_id = cred_response.data['id']

            response = (
                self.supabase.table('cronograma_matriculas')
                .select('matriculas(numero)')
                .lte('dia_mes', datetime.now().day)
                .eq('matriculas.ativo', True)
                .eq('matriculas.credencial_id', credencial_id)
                .execute()
            )
        else:
            response = (
                self.supabase.table('cronograma_matriculas')
                .select('matriculas(numero)')
                .lte('dia_mes', datetime.now().day)
                .eq('matriculas.ativo', True)
                .execute()
            )

        todas_matriculas = {
            item['matriculas']['numero']
            for item in response.data
            if item.get('matriculas') and item['matriculas'].get('numero')
        }
        matriculas_pendentes = list(todas_matriculas - matriculas_com_sucesso)

        return matriculas_pendentes

    def filtrar_matriculas_nao_baixadas(self, matriculas: List[str], verificar_hoje_apenas: bool = True) -> List[str]:
        """
        Filtra uma lista de matrículas removendo aquelas que já foram baixadas com sucesso
        
        Args:
            matriculas: Lista de matrículas para verificar
            verificar_hoje_apenas: Se True, verifica apenas downloads de hoje. Se False, verifica dos últimos 5 dias
        
        Returns:
            Lista de matrículas que ainda não foram baixadas
        """
        if not matriculas:
            return []
        
        matriculas_nao_baixadas = []
        
        for matricula in matriculas:
            if verificar_hoje_apenas:
                ja_baixada = self.matricula_ja_baixada_hoje(matricula)
            else:
                ja_baixada = self.matricula_ja_baixada_recentemente(matricula, dias=5)
            
            if not ja_baixada:
                matriculas_nao_baixadas.append(matricula)
            else:
                print(f"📋 Matrícula {matricula} já foi baixada com sucesso - PULANDO")
        
        return matriculas_nao_baixadas

    def registrar_tentativa(self, matricula: str, sucesso: bool, erro: str = None):
        data = {
            'matricula_numero': matricula,
            'sucesso': sucesso,
            'erro': erro
        }
        self.supabase.table('tentativas_download').insert(data).execute()

    def get_matriculas_para_cpf(self, cpf: str, incluir_pendentes: bool = True, verificar_duplicatas: bool = True) -> List[str]:
        """
        Obtém matrículas para processar para um CPF específico
        
        Args:
            cpf: CPF para buscar matrículas
            incluir_pendentes: Se deve incluir matrículas pendentes de dias anteriores
            verificar_duplicatas: Se deve filtrar matrículas já baixadas
        """
        hoje = datetime.now().day
        matriculas_hoje = self.get_matriculas_por_dia(hoje, cpf)
        
        if incluir_pendentes:
            matriculas_pendentes = self.get_matriculas_pendentes(cpf=cpf)
            matriculas_hoje.extend(matriculas_pendentes)
            matriculas_hoje = list(set(matriculas_hoje))
        
        if verificar_duplicatas:
            matriculas_hoje = self.filtrar_matriculas_nao_baixadas(
                matriculas_hoje, 
                verificar_hoje_apenas=True
            )
        
        return matriculas_hoje