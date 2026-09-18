# main.py
from pathlib import Path
import os

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from actions import realizar_login
from utils import configurar_logger
from validador_planilha import ValidadorPlanilha
from processador import ProcessadorPlanilha

# ============================================================
# CONFIGURAÇÕES E VARIÁVEIS DE AMBIENTE (.env)
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")

URL_LOGIN = os.getenv("URL_LOGIN")
SENHA_LOGIN = os.getenv("SENHA_LOGIN")
CAMINHO_PLANILHA = BASE_DIR / "data" / "dados.xlsx"

logger = configurar_logger()

def criar_driver():
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless=new")
    return webdriver.Chrome(options=options)

def main():
    logger.info("=" * 60)
    logger.info("INICIANDO AUTOMAÇÃO - HAPVIDA PORTAL")
    logger.info("=" * 60)

    # 1. Validação e Carga da Planilha
    try:
        validador = ValidadorPlanilha(CAMINHO_PLANILHA, logger)
        df = validador.carregar_e_validar()
    except Exception as e:
        logger.error(f"Erro na validação da planilha: {e}")
        return

    # 2. Inicialização do Driver
    driver = criar_driver()

    try:
        # 3. Acesso à página e Login Global
        logger.info("Acessando página de login...")
        driver.get(URL_LOGIN)

        # Localiza a primeira empresa válida para o login único
        primeira_empresa = None
        for _, row in df.iterrows():
            empresa = str(row.get("Empresa", "")).strip()
            cpf = str(row.get("CPF", "")).strip()
            if empresa and empresa.lower() != "nan" and cpf and cpf.lower() != "nan":
                primeira_empresa = empresa
                break

        if not primeira_empresa:
            logger.error("Nenhum registro válido encontrado para login.")
            return

        logger.info(f"Realizando login com a empresa: {primeira_empresa}")
        if not realizar_login(driver=driver, codigo_empresa=primeira_empresa, senha=SENHA_LOGIN):
            logger.error("Falha no login. Encerrando automação.")
            return

        logger.info("Login realizado com sucesso!")

        # 4. Delegação do Processamento das Linhas para o Processador
        processador = ProcessadorPlanilha(driver=driver, df=df, base_dir=BASE_DIR, logger=logger)
        processador.executar_processamento()

        # 5. Salvamento do Relatório Final
        processador.salvar_relatorio()

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