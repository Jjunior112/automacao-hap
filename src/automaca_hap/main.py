from pathlib import Path
from datetime import datetime
import os

import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from actions import (
    realizar_login,
    acessar_precancelamento_titular,
    executar_precancelamento_titular,
    acessar_inclusao_titular,  
    executar_inclusao_titular
)
from utils import configurar_logger


# ============================================================
# CONFIGURAÇÕES E VARIÁVEIS DE AMBIENTE (.env)
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega as variáveis do arquivo .env
load_dotenv(BASE_DIR.parent / ".env")

URL_LOGIN = os.getenv("URL_LOGIN")
SENHA_LOGIN = os.getenv("SENHA_LOGIN")

# Caminho para o arquivo Excel
CAMINHO_PLANILHA = BASE_DIR / "data" / "dados.xlsx"

logger = configurar_logger()


# ============================================================
# CONFIGURAÇÃO DO NAVEGADOR
# ============================================================

def criar_driver():
    options = Options()
    options.add_argument("--start-maximized")

    # Se quiser rodar em segundo plano no futuro:
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    return driver


# ============================================================
# MAIN
# ============================================================

def main():

    logger.info("=" * 60)
    logger.info("INICIANDO AUTOMAÇÃO - HAPVIDA PORTAL")
    logger.info("=" * 60)

    # ========================================================
    # 0. LEITURA E VALIDAÇÃO DINÂMICA DA PLANILHA
    # ========================================================

    try:
        logger.info(f"Lendo planilha em: {CAMINHO_PLANILHA}")

        df = pd.read_excel(CAMINHO_PLANILHA)

        # Padroniza a coluna 'Acao' se existir
        if "Acao" in df.columns:
            df["Acao"] = df["Acao"].fillna("").astype(str).str.replace(".0", "", regex=False).str.strip()
        else:
            raise ValueError("A coluna obrigatória 'Acao' não foi encontrada na planilha.")

        # Validações de colunas obrigatórias baseadas no tipo de ação
        colunas_obrigatorias = ["Empresa", "Acao"]
        acoes_presentes = df["Acao"].unique()

        # Se houver Ação 2 (Pré-cancelamento), exige Carteirinha e CPF
        if "2" in acoes_presentes:
            colunas_obrigatorias.extend(["Carteirinha", "CPF"])

        # Se houver Ação 1 (Inclusão), exige os campos cadastrais necessários incluindo Matricula
        if "1" in acoes_presentes:
            colunas_obrigatorias.extend([
                "CPF", "Matricula", "Nome", "DataNasc", "Sexo", "EstadoCivil", 
                "Mae", "DataAdm", "Unidade", "Plano", "CEP", "Endereco", "Bairro", "Cidade", "Uf"
            ])

        # Remove duplicadas na lista de verificação
        colunas_obrigatorias = list(set(colunas_obrigatorias))

        for coluna in colunas_obrigatorias:
            if coluna not in df.columns:
                raise ValueError(
                    f"A coluna obrigatória '{coluna}' não foi encontrada na planilha, "
                    f"sendo necessária para as ações presentes."
                )

        logger.info(
            f"Planilha carregada e colunas validadas com sucesso. "
            f"Colunas verificadas: {colunas_obrigatorias}"
        )

    except Exception as e:
        logger.error(
            f"Erro ao carregar ou validar a planilha: {e}"
        )
        return

    # ========================================================
    # CRIAÇÃO DO DRIVER
    # ========================================================

    driver = criar_driver()

    resultados_processamento = []

    try:

        # ====================================================
        # 1. ACESSAR PÁGINA DE LOGIN
        # ====================================================

        logger.info("Acessando página de login...")

        driver.get(URL_LOGIN)

        # ====================================================
        # 2. LOCALIZAR A PRIMEIRA EMPRESA VÁLIDA
        # ====================================================

        primeira_empresa = None

        for _, row in df.iterrows():

            empresa = str(
                row.get("Empresa", "")
            ).strip()

            cpf = str(
                row.get("CPF", "")
            ).strip()

            # Procura uma linha que tenha os dados necessários para realizar o primeiro login.
            if (
                empresa
                and empresa.lower() != "nan"
                and cpf
                and cpf.lower() != "nan"
            ):
                primeira_empresa = empresa
                break

        # ====================================================
        # 3. VALIDA SE EXISTE REGISTRO VÁLIDO PARA LOGIN
        # ====================================================

        if not primeira_empresa:

            logger.error(
                "Nenhum registro válido foi encontrado "
                "na planilha para realizar o login."
            )

            return

        # ====================================================
        # 4. REALIZA O LOGIN UMA ÚNICA VEZ
        # ====================================================

        logger.info(
            f"Realizando login com o código da empresa: "
            f"{primeira_empresa}"
        )

        sucesso_login = realizar_login(
            driver=driver,
            codigo_empresa=primeira_empresa,
            senha=SENHA_LOGIN
        )

        if not sucesso_login:

            logger.error(
                "Falha no login com a empresa informada. "
                "Encerrando automação."
            )

            return

        logger.info("Login realizado com sucesso!")

        # ====================================================
        # 5. LOOP SOBRE OS REGISTROS DA PLANILHA (SWITCH-CASE)
        # ====================================================

        for index, row in df.iterrows():

            empresa = str(
                row.get("Empresa", "")
            ).strip()

            carteirinha = str(
                row.get("Carteirinha", "")
            ).strip()

            cpf = str(
                row.get("CPF", "")
            ).strip()

            matricula = str(
                row.get("Matricula", "")
            ).strip()

            acao = str(
                row.get("Acao", "")
            ).strip()

            row_dict = row.to_dict()

            # ------------------------------------------------
            # VALIDAÇÃO DOS DADOS BÁSICOS DA LINHA
            # ------------------------------------------------

            if (
                not empresa
                or empresa.lower() == "nan"
                or not cpf
                or cpf.lower() == "nan"
                or not acao
                or acao.lower() == "nan"
            ):

                msg_status = "Erro"

                msg_detalhe = (
                    "Empresa, CPF ou Ação "
                    "vazios/inválidos na planilha."
                )

                logger.warning(
                    f"Linha {index + 2}: "
                    f"{msg_detalhe} Pulando registro."
                )

                row_dict["Status"] = msg_status
                row_dict["Mensagem"] = msg_detalhe

                resultados_processamento.append(
                    row_dict
                )

                continue

            # Validação específica da Matrícula caso a ação seja Inclusão (1)
            if acao == "1" and (not matricula or matricula.lower() == "nan"):
                msg_status = "Erro"
                msg_detalhe = "Matrícula vazia/inválida para a ação de Inclusão."
                logger.warning(f"Linha {index + 2}: {msg_detalhe} Pulando registro.")
                row_dict["Status"] = msg_status
                row_dict["Mensagem"] = msg_detalhe
                resultados_processamento.append(row_dict)
                continue

            # ------------------------------------------------
            # LOG DO REGISTRO ATUAL
            # ------------------------------------------------

            logger.info(
                f"--- Processando registro {index + 2} | "
                f"Ação: {acao} | Empresa: {empresa} | CPF: {cpf} ---"
            )

            sucesso_operacao = False

            # ========================================================
            # FLUXO SWITCH-CASE (MATCH-CASE):
            # 1 = Inclusão de Titular
            # 2 = Pré-cancelamento de Titular Ativo
            # ========================================================

            match acao:
                case "2":  # Pré-cancelamento
                    if not carteirinha or carteirinha.lower() == "nan":
                        logger.error(f"Linha {index + 2}: Carteirinha é obrigatória para pré-cancelamento.")
                        sucesso_operacao = False
                    else:
                        if not acessar_precancelamento_titular(driver):
                            logger.error("Erro ao acessar tela de pré-cancelamento.")
                            sucesso_operacao = False
                        else:
                            sucesso_operacao = executar_precancelamento_titular(
                                driver=driver,
                                codigo_titular=carteirinha,
                                cpf_titular=cpf
                            )

                case "1":  # Inclusão
                    if not acessar_inclusao_titular(driver):
                        logger.error("Erro ao acessar tela de inclusão de titular.")
                        sucesso_operacao = False
                    else:
                        sucesso_operacao = executar_inclusao_titular(
                            driver=driver,
                            dados_linha=row
                        )

                case _:
                    logger.warning(
                        f"Linha {index + 2}: Ação desconhecida '{acao}'. "
                        "Use '1' para Inclusão ou '2' para Pré-cancelamento."
                    )
                    sucesso_operacao = False

            # ------------------------------------------------
            # TRATAMENTO DO RESULTADO DA AÇÃO
            # ------------------------------------------------

            if not sucesso_operacao:

                msg_status = "Erro"

                msg_detalhe = (
                    f"Falha durante a execução da ação (Código: {acao}) "
                    "ou divergência de validação."
                )

                logger.error(
                    f"Linha {index + 2}: "
                    f"{msg_detalhe}"
                )

            else:

                msg_status = "Sucesso"

                msg_detalhe = (
                    f"Ação (Código: {acao}) executada e "
                    "validada com sucesso."
                )

                logger.info(
                    f"Registro da linha {index + 2} "
                    "concluído com sucesso!"
                )

            row_dict["Status"] = msg_status
            row_dict["Mensagem"] = msg_detalhe

            resultados_processamento.append(
                row_dict
            )

            # ------------------------------------------------
            # AGUARDA 5 SEGUNDOS ANTES DA PRÓXIMA ITERAÇÃO
            # ------------------------------------------------

            logger.info(
                "Aguardando 5 segundos antes do próximo registro..."
            )

            time.sleep(5)

        # ====================================================
        # 6. SALVAR ARQUIVO DE SAÍDA
        # ====================================================

        if resultados_processamento:

            timestamp_str = datetime.now().strftime(
                "%d-%m-%Y_%H-%M"
            )

            pasta_dados = BASE_DIR / "data" / "processamentos"

            pasta_dados.mkdir(
                parents=True,
                exist_ok=True
            )

            caminho_saida = (
                pasta_dados
                / f"resultado_processamento_{timestamp_str}.xlsx"
            )

            df_resultado = pd.DataFrame(
                resultados_processamento
            )

            df_resultado.to_excel(
                caminho_saida,
                index=False
            )

            logger.info(
                f"Processamento finalizado. "
                f"Relatório salvo em: {caminho_saida}"
            )

        else:

            logger.info(
                "Nenhum registro foi processado."
            )

    except Exception as erro:

        logger.exception(
            f"Erro fatal na automação: {erro}"
        )

    finally:

        driver.quit()

        logger.info(
            "Navegador encerrado."
        )

        logger.info("=" * 60)
        logger.info("AUTOMAÇÃO FINALIZADA")
        logger.info("=" * 60)


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()
