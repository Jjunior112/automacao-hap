# validador_planilha.py
import pandas as pd
from pathlib import Path
import logging

class ValidadorPlanilha:
    def __init__(self, caminho_planilha: Path, logger: logging.Logger = None):
        self.caminho_planilha = Path(caminho_planilha)
        self.logger = logger or logging.getLogger(__name__)
        self.df = None

    def carregar_e_validar(self) -> pd.DataFrame:
        """
        Carrega a planilha do Excel, padroniza a coluna 'Acao' 
        e executa a validação dinâmica de colunas obrigatórias.
        Retorna o DataFrame limpo ou levanta um ValueError em caso de falha.
        """
        self.logger.info(f"Lendo planilha em: {self.caminho_planilha}")

        if not self.caminho_planilha.exists():
            raise FileNotFoundError(f"O arquivo da planilha não foi encontrado em: {self.caminho_planilha}")

        try:
            self.df = pd.read_excel(self.caminho_planilha)
        except Exception as e:
            raise RuntimeError(f"Erro ao ler o arquivo Excel: {e}")

        # 1. Padroniza a coluna 'Acao'
        if "Acao" in self.df.columns:
            self.df["Acao"] = (
                self.df["Acao"]
                .fillna("")
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
            )
        else:
            raise ValueError("A coluna obrigatória 'Acao' não foi encontrada na planilha.")

        # 2. Identifica quais ações estão presentes para definir as exigências dinâmicas
        colunas_obrigatorias = ["Empresa", "Acao"]
        acoes_presentes = self.df["Acao"].unique()

        # Se houver Ação 2 (Pré-cancelamento), exige Carteirinha e CPF
        if "2" in acoes_presentes:
            colunas_obrigatorias.extend(["Carteirinha", "CPF"])

        # Se houver Ação 1 (Inclusão), exige os campos cadastrais necessários
        if "1" in acoes_presentes:
            colunas_obrigatorias.extend([
                "CPF", "Matricula", "Nome", "DataNasc", "Sexo", "EstadoCivil", 
                "Mae", "DataAdm", "Unidade", "Plano", "CEP", "Endereco", "Numero","Bairro", "Cidade", "Uf"
            ])

        # Remove duplicatas na lista de verificação
        colunas_obrigatorias = list(set(colunas_obrigatorias))

        # 3. Valida a presença física das colunas no DataFrame
        for coluna in colunas_obrigatorias:
            if coluna not in self.df.columns:
                raise ValueError(
                    f"A coluna obrigatória '{coluna}' não foi encontrada na planilha, "
                    f"sendo necessária para as ações presentes."
                )

        self.logger.info(
            f"Planilha carregada e colunas validadas com sucesso. "
            f"Colunas verificadas: {colunas_obrigatorias}"
        )

        return self.df