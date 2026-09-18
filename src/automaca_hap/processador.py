# processador.py
import time
from datetime import datetime
from pathlib import Path
import logging
import pandas as pd

from actions import (
    acessar_precancelamento_titular,
    executar_precancelamento_titular,
    acessar_inclusao_titular,  
    executar_inclusao_titular
)

class ProcessadorPlanilha:
    def __init__(self, driver, df: pd.DataFrame, base_dir: Path, logger: logging.Logger = None):
        self.driver = driver
        self.df = df
        self.base_dir = base_dir
        self.logger = logger or logging.getLogger(__name__)
        self.resultados = []

    def executar_processamento(self):
        """Itera sobre as linhas do DataFrame, executa as ações e retorna os resultados."""
        self.logger.info("Iniciando processamento dos registros da planilha...")

        for index, row in self.df.iterrows():
            linha_excel = index + 2  # Cabeçalho ocupa a linha 1
            row_dict = row.to_dict()

            empresa = str(row.get("Empresa", "")).strip()
            carteirinha = str(row.get("Carteirinha", "")).strip()
            cpf = str(row.get("CPF", "")).strip()
            matricula = str(row.get("Matricula", "")).strip()
            acao = str(row.get("Acao", "")).strip()

            # Validação básica de linha
            if not self._validar_dados_basicos(empresa, cpf, acao, linha_excel, row_dict):
                continue

            # Validação específica para Inclusão (Ação 1)
            if acao == "1" and (not matricula or matricula.lower() == "nan"):
                msg_detalhe = "Matrícula vazia/inválida para a ação de Inclusão."
                self._registrar_erro(linha_excel, msg_detalhe, row_dict)
                continue

            self.logger.info(
                f"--- Processando registro {linha_excel} | "
                f"Ação: {acao} | Empresa: {empresa} | CPF: {cpf} ---"
            )

            sucesso_operacao = self._despatch_acao(acao, carteirinha, cpf, row, linha_excel)

            # Tratamento do resultado
            if not sucesso_operacao:
                msg_status = "Erro"
                msg_detalhe = f"Falha durante a execução da ação (Código: {acao})."
                self.logger.error(f"Linha {linha_excel}: {msg_detalhe}")
            else:
                msg_status = "Sucesso"
                msg_detalhe = f"Ação (Código: {acao}) executada com sucesso."
                self.logger.info(f"Registro da linha {linha_excel} concluído com sucesso!")

            row_dict["Status"] = msg_status
            row_dict["Mensagem"] = msg_detalhe
            self.resultados.append(row_dict)

            self.logger.info("Aguardando 5 segundos antes do próximo registro...")
            time.sleep(5)

        return self.resultados

    def _validar_dados_basicos(self, empresa, cpf, acao, linha_excel, row_dict) -> bool:
        if not empresa or empresa.lower() == "nan" or not cpf or cpf.lower() == "nan" or not acao or acao.lower() == "nan":
            msg_detalhe = "Empresa, CPF ou Ação vazios/inválidos na planilha."
            self._registrar_erro(linha_excel, msg_detalhe, row_dict)
            return False
        return True

    def _registrar_erro(self, linha_excel, msg_detalhe, row_dict):
        self.logger.warning(f"Linha {linha_excel}: {msg_detalhe} Pulando registro.")
        row_dict["Status"] = "Erro"
        row_dict["Mensagem"] = msg_detalhe
        self.resultados.append(row_dict)

    def _despatch_acao(self, acao, carteirinha, cpf, row, linha_excel) -> bool:
        """Faz o direcionamento (match-case) para a função correta do Selenium."""
        match acao:
            case "2":  # Pré-cancelamento
                if not carteirinha or carteirinha.lower() == "nan":
                    self.logger.error(f"Linha {linha_excel}: Carteirinha é obrigatória para pré-cancelamento.")
                    return False
                if not acessar_precancelamento_titular(self.driver):
                    self.logger.error("Erro ao acessar tela de pré-cancelamento.")
                    return False
                return executar_precancelamento_titular(
                    driver=self.driver,
                    codigo_titular=carteirinha,
                    cpf_titular=cpf
                )

            case "1":  # Inclusão
                if not acessar_inclusao_titular(self.driver):
                    self.logger.error("Erro ao acessar tela de inclusão de titular.")
                    return False
                return executar_inclusao_titular(
                    driver=self.driver,
                    dados_linha=row
                )

            case _:
                self.logger.warning(f"Linha {linha_excel}: Ação desconhecida '{acao}'.")
                return False

    def salvar_relatorio(self) -> str | None:
        """Salva o DataFrame de resultados em um arquivo Excel com timestamp."""
        if not self.resultados:
            self.logger.info("Nenhum registro foi processado para gerar relatório.")
            return None

        timestamp_str = datetime.now().strftime("%d-%m-%Y_%H-%M")
        pasta_dados = self.base_dir / "data" / "processamentos"
        pasta_dados.mkdir(parents=True, exist_ok=True)
        
        caminho_saida = pasta_dados / f"resultado_processamento_{timestamp_str}.xlsx"
        
        df_resultado = pd.DataFrame(self.resultados)
        df_resultado.to_excel(caminho_saida, index=False)
        
        self.logger.info(f"Relatório de processamento salvo em: {caminho_saida}")
        return str(caminho_saida)