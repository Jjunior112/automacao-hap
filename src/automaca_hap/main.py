from pathlib import Path
from datetime import datetime
import os
import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from actions import realizar_login, executar_precancelamento_titular
from utils import configurar_logger

# ============================================================
# CONFIGURAÇÕES E VARIÁVEIS DE AMBIENTE (.env)
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega as variáveis do arquivo .env
load_dotenv(BASE_DIR.parent / ".env")

URL_LOGIN = os.getenv("URL_LOGIN")    
SENHA_LOGIN = os.getenv("SENHA_LOGIN")

# Caminho para o arquivo Excel em src/data/dados.xlsx
CAMINHO_PLANILHA = BASE_DIR / "data" / "dados.xlsx"

logger = configurar_logger()


# ============================================================
# CONFIGURAÇÃO DO NAVEGADOR
# ============================================================

def criar_driver():
    options = Options()
    options.add_argument("--start-maximized")
    
    # Se quiser rodar em segundo plano no futuro, basta descomentar a linha abaixo:
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

    # ----------------------------------------------------
    # 0. Leitura e Validação da Planilha (ANTES DO LOGIN)
    # ----------------------------------------------------
    try:
        logger.info(f"Lendo planilha em: {CAMINHO_PLANILHA}")
        df = pd.read_excel(CAMINHO_PLANILHA)
        
        # Valida se as colunas obrigatórias existem
        colunas_obrigatorias = ["Empresa", "Carteirinha", "CPF"]
        for coluna in colunas_obrigatorias:
            if coluna not in df.columns:
                raise ValueError(f"A coluna obrigatória '{coluna}' não foi encontrada na planilha.")
        
        logger.info("Planilha carregada e colunas ('Empresa', 'Carteirinha', 'CPF') validadas com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao carregar ou validar a planilha: {e}")
        return

    driver = criar_driver()

    try:
        # ----------------------------------------------------
        # 1. Realiza o Login
        # ----------------------------------------------------
        logger.info("Acessando página de login...")
        driver.get(URL_LOGIN)

        resultados_processamento = []
        primeiro_login_feito = False

        # ----------------------------------------------------
        # 2. ITERAÇÃO SOBRE OS DADOS DA PLANILHA
        # ----------------------------------------------------
        for index, row in df.iterrows():
            empresa = str(row.get("Empresa", "")).strip()
            carteirinha = str(row.get("Carteirinha", "")).strip()
            cpf = str(row.get("CPF", "")).strip()
            nome = str(row.get("Nome", "")).strip() if "Nome" in df.columns else ""

            row_dict = row.to_dict()

            # Validação: Empresa, CPF e Carteirinha devem estar preenchidos
            if not empresa or empresa.lower() == "nan" or not carteirinha or carteirinha.lower() == "nan" or not cpf or cpf.lower() == "nan":
                msg_status = "Erro"
                msg_detalhe = "Empresa, Carteirinha ou CPF vazios/inválidos na planilha."
                logger.warning(f"Linha {index + 2}: {msg_detalhe} Pulando registro.")
                
                row_dict["Status"] = msg_status
                row_dict["Mensagem"] = msg_detalhe
                resultados_processamento.append(row_dict)
                continue

            # Realiza o login (caso ainda não tenha feito) utilizando o código da empresa da linha atual
            if not primeiro_login_feito:
                logger.info(f"Realizando login com o código da empresa: {empresa}")
                sucesso_login = realizar_login(
                    driver=driver,
                    codigo_empresa=empresa,
                    senha=SENHA_LOGIN
                )

                if not sucesso_login:
                    logger.error("Falha no login com a empresa informada. Encerrando automação.")
                    break
                
                primeiro_login_feito = True
                logger.info("Login realizado com sucesso!")

            logger.info(f"--- Processando registro {index + 2} | Empresa: {empresa} | Carteirinha: {carteirinha} | CPF: {cpf} ---")

            # Executa o fluxo de pré-cancelamento
            sucesso_precancelamento = executar_precancelamento_titular(
                driver=driver,
                codigo_titular=carteirinha,
                cpf_titular=cpf
            )

            if not sucesso_precancelamento:
                msg_status = "Erro"
                msg_detalhe = "Falha durante a execução do pré-cancelamento ou divergência de validação."
                logger.error(f"Linha {index + 2}: {msg_detalhe}")
            else:
                msg_status = "Sucesso"
                msg_detalhe = "Pré-cancelamento executado e validado com sucesso."
                logger.info(f"Registro da linha {index + 2} concluído com sucesso!")

            row_dict["Status"] = msg_status
            row_dict["Mensagem"] = msg_detalhe
            resultados_processamento.append(row_dict)

# ----------------------------------------------------
        # 3. SALVANDO ARQUIVO DE SAÍDA COM DATA E HORA
        # ----------------------------------------------------
        if resultados_processamento:
            timestamp_str = datetime.now().strftime("%d-%m-%Y_%H-%M")
            
            # Define corretamente a pasta de saída e garante que ela exista
            pasta_dados = BASE_DIR / "data"
            pasta_dados.mkdir(parents=True, exist_ok=True)
            
            caminho_saida = pasta_dados / f"resultado_processamento_{timestamp_str}.xlsx"
            
            df_resultado = pd.DataFrame(resultados_processamento)
            df_resultado.to_excel(caminho_saida, index=False)
            
            logger.info(f"Processamento finalizado. Relatório salvo em: {caminho_saida}")
        else:
            logger.info("Nenhum registro foi processado.")

    except Exception as erro:
        logger.exception(f"Erro fatal na automação: {erro}")

    finally:
        driver.quit()
        logger.info("Navegador encerrado.")
        logger.info("=" * 60)
        logger.info("AUTOMAÇÃO FINALIZADA")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()