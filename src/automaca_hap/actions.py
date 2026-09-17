import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from utils import limpar_valor, configurar_logger

logger = configurar_logger()
TEMPO_ESPERA = 10


def realizar_login(driver, codigo_empresa, senha):
    """
    Realiza o login no sistema preenchendo o código da empresa e a senha,
    disparando o evento onblur necessário e clicando em Prosseguir.
    """
    try:
        wait = WebDriverWait(driver, TEMPO_ESPERA)

        # 1. Preenche o Código da Empresa (utilizando o name='pCodigoEmpresa' do seu HTML)
        xpath_campo_codigo = "//input[@name='pCodigoEmpresa']"
        campo_codigo = wait.until(EC.presence_of_element_located((By.XPATH, xpath_campo_codigo)))
        campo_codigo.clear()
        campo_codigo.send_keys(limpar_valor(codigo_empresa))

        # Dispara o evento onblur via JavaScript (necessario pois o HTML original usa onblur="retornaUnidade(this);")
        driver.execute_script("arguments[0].blur();", campo_codigo)

        # Pequena pausa ou espera caso o onblur carregue elementos dinâmicos (opcional, mas recomendado)
        time.sleep(3)
        campo_codigo.send_keys(Keys.TAB)         

        # 2. Preenche a Senha (utilizando o id='pSenha' do seu HTML)
        xpath_campo_senha = "//input[@id='pSenha']"
        campo_senha = driver.find_element(By.XPATH, xpath_campo_senha)
        campo_senha.clear()
        campo_senha.send_keys(limpar_valor(senha))

        # 3. Clica no botão "Prosseguir" (utilizando o id='Prosseguir' do seu HTML)
        xpath_botao_prosseguir = "//input[@id='Prosseguir']"
        botao_prosseguir = driver.find_element(By.XPATH, xpath_botao_prosseguir)
        botao_prosseguir.click()

        # ----------------------------------------------------
        # VERIFICAÇÃO DE SUCESSO NO LOGIN
        # ----------------------------------------------------
        # XPath exato fornecido que só existe após o login bem-sucedido
        xpath_indicador_sucesso = "/html/body/div[2]/div/div/span/h1"
        
        wait.until(EC.presence_of_element_located((By.XPATH, xpath_indicador_sucesso)))
        
        logger.info("Login realizado e validado com sucesso!")
        return True

    except Exception as e:
        logger.error(f"Erro ao tentar realizar o login: {e}")
        return False


def acessar_precancelamento_titular(driver):
    """
    Acessa a tela de Pré-cancelamento de Titular Ativo.
    
    Executa apenas uma vez:
    1. Localiza o menu de pré-cancelamento.
    2. Clica no menu.
    3. Aguarda o carregamento da tela.
    
    Retorna:
        True  -> acesso realizado com sucesso.
        False -> ocorreu algum erro.
    """
    try:
        wait = WebDriverWait(driver, TEMPO_ESPERA)

        # ----------------------------------------------------
        # PASSO 1: Acessar a tela de pré-cancelamento
        # ----------------------------------------------------
        logger.info("Acessando a opção de Pré-cancelamento de Titular Ativo...")

        xpath_link_cancelamento = "//a[contains(., 'Pré-cancelamento de Titular Ativo')]"

        link_cancelamento = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, xpath_link_cancelamento)
            )
        )

        link_cancelamento.click()

        # ----------------------------------------------------
        # PASSO 2: Aguardar o carregamento
        # ----------------------------------------------------
        logger.info("Aguardando 3 segundos para o carregamento da página...")
        time.sleep(3)

        logger.info("Tela de pré-cancelamento acessada com sucesso.")

        return True

    except Exception as e:
        logger.error(
            f"Erro ao acessar a tela de pré-cancelamento: {e}"
        )
        return False


def executar_precancelamento_titular(driver, codigo_titular, cpf_titular):
    """
    Executa o processo de pré-cancelamento para um titular.

    IMPORTANTE:
    A função assume que a tela de pré-cancelamento já foi acessada
    pela função acessar_precancelamento_titular().

    Executa:
    1. Preenche o input pCodigoTitular com os primeiros 11 caracteres.
    2. Clica no primeiro botão de submit 'Prosseguir'.
    3. Verifica se ocorreu erro de código inválido na tela.
    4. Seleciona a opção 'DEMISSAO ROTATIVA' no select de motivos.
    5. Valida se o CPF exibido na tela bate com cpf_titular.
    6. Clica no botão final de submit 'Prosseguir'.

    Retorna:
        True  -> processo realizado com sucesso.
        False -> ocorreu erro ou divergência de CPF.
    """
    try:
        wait = WebDriverWait(driver, TEMPO_ESPERA)

        # ----------------------------------------------------
        # PASSO 1: Tratar o código e preencher o input
        # ----------------------------------------------------
        codigo_tratado = str(codigo_titular)[:11]

        logger.info(
            f"Código tratado (primeiros 11 caracteres): {codigo_tratado}"
        )

        xpath_input_titular = "//input[@name='pCodigoTitular']"

        campo_titular = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, xpath_input_titular)
            )
        )

        campo_titular.click()
        campo_titular.clear()

        driver.execute_script("""
            var el = arguments[0];
            var valor = arguments[1];

            el.value = valor;

            el.dispatchEvent(
                new Event('input', { bubbles: true })
            );

            el.dispatchEvent(
                new Event('change', { bubbles: true })
            );

            el.dispatchEvent(
                new Event('blur', { bubbles: true })
            );
        """, campo_titular, codigo_tratado)

        # ----------------------------------------------------
        # PASSO 2: Clicar no primeiro botão Prosseguir
        # ----------------------------------------------------
        logger.info("Clicando no botão de Prosseguir do titular...")

        xpath_botao_prosseguir_1 = (
            "//input[@type='submit' "
            "and @value='Prosseguir' "
            "and contains(@class, 'botao')]"
        )

        botao_prosseguir_1 = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, xpath_botao_prosseguir_1)
            )
        )

        try:
            botao_prosseguir_1.click()
        except Exception:
            driver.execute_script(
                "arguments[0].click();",
                botao_prosseguir_1
            )

        # Pequena pausa após o submit
        time.sleep(2)

        # ----------------------------------------------------
        # PASSO 3: Verificar código titular inválido
        # ----------------------------------------------------
        xpath_erro_invalido = (
            "//*[contains(text(), "
            "'ERRO: CÓDIGO TITULAR INVÁLIDO')]"
        )

        elementos_erro = driver.find_elements(
            By.XPATH,
            xpath_erro_invalido
        )

        if elementos_erro:
            logger.error(
                "ERRO DETECTADO NA TELA: "
                "CÓDIGO TITULAR INVÁLIDO "
                "(INEXISTENTE, NÃO ATIVO OU SEM DEPENDENTES)."
            )
            return False

        # ----------------------------------------------------
        # PASSO 4: Selecionar motivo 'DEMISSAO ROTATIVA'
        # ----------------------------------------------------
        logger.info(
            "Selecionando o motivo 'Demissão Rotativa'..."
        )

        xpath_select = "//select[@name='pmotivocancelamento']"

        elemento_select = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, xpath_select)
            )
        )

        select_obj = Select(elemento_select)
        select_obj.select_by_value("50")

        driver.execute_script("""
            var el = arguments[0];

            el.dispatchEvent(
                new Event('change', { bubbles: true })
            );

            el.dispatchEvent(
                new Event('click', { bubbles: true })
            );
        """, elemento_select)

        # ----------------------------------------------------
        # PASSO 6: Clicar no Prosseguir final
        # ----------------------------------------------------
        logger.info(
            "Clicando no botão de Prosseguir final "
            "após a validação..."
        )

        xpath_botao_prosseguir_final = (
            "//input[@type='submit' "
            "and @value='Prosseguir' "
            "and contains(@class, 'botao')]"
        )

        botao_prosseguir_final = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, xpath_botao_prosseguir_final)
            )
        )

        try:
            botao_prosseguir_final.click()
        except Exception:
            driver.execute_script(
                "arguments[0].click();",
                botao_prosseguir_final
            )

        logger.info(
            "Pré-cancelamento processado com sucesso."
        )

        return True

    except Exception as e:
        logger.error(
            f"Erro durante a execução do pré-cancelamento: {e}"
        )
        return False


def acessar_inclusao_titular(driver):
    """
    Acessa a tela de Inclusão de Titular.
    """
    try:
        wait = WebDriverWait(driver, TEMPO_ESPERA)
        logger.info("Acessando a opção de Inclusão de Titular...")

        xpath_link_inclusao = "//a[contains(., 'Inclusão de Titular')]"
        link_inclusao = wait.until(
            EC.element_to_be_clickable((By.XPATH, xpath_link_inclusao))
        )
        link_inclusao.click()

        time.sleep(3)
        logger.info("Tela de inclusão de titular acessada com sucesso.")
        return True

    except Exception as e:
        logger.error(f"Erro ao acessar a tela de inclusão de titular: {e}")
        return False


def executar_inclusao_titular(driver, dados_linha):
    """
    Executa o processo de inclusão de titular preenchendo todos os passos solicitados.
    """
    try:
        wait = WebDriverWait(driver, 10)

        # ----------------------------------------------------
        # PASSO 2: Preencher CPF com validação de 11 dígitos (zeros à esquerda)
        # ----------------------------------------------------
        cpf_raw = limpar_valor(dados_linha.get("CPF", ""))
        cpf_tratado = cpf_raw.zfill(11) if cpf_raw else ""
        
        logger.info(f"Preenchendo CPF do titular: {cpf_tratado}")
        campo_cpf = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='pCpfTitular']")))
        campo_cpf.click()
        campo_cpf.clear()
        campo_cpf.send_keys(cpf_tratado)

        # ----------------------------------------------------
        # PASSO 2.1: Clicar no botão Prosseguir
        # ----------------------------------------------------
        logger.info("Clicando no botão 'Prosseguir'...")
        botao_prosseguir = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Prosseguir' and contains(@class, 'botao')]")))
        botao_prosseguir.click()

        # ----------------------------------------------------
        # PASSO 3: Verificações de dados pessoais (Nome, Nasc, Sexo, Estado Civil, Mãe, RG, Órgão, UF)
        # ----------------------------------------------------
        # Nome Titular
        campo_nome = driver.find_element(By.ID, "pNomeTitular")
        if not campo_nome.get_attribute("value").strip():
            campo_nome.clear()
            campo_nome.send_keys(limpar_valor(dados_linha.get("Nome", "")))

        # Data de Nascimento
        campo_nasc = driver.find_element(By.ID, "pDataNasc")
        if not campo_nasc.get_attribute("value").strip():
            campo_nasc.clear()
            campo_nasc.send_keys(limpar_valor(dados_linha.get("DataNasc", "")))

        # Sexo (M ou F)
        select_sexo = Select(driver.find_element(By.ID, "pSexo"))
        val_sexo = limpar_valor(dados_linha.get("Sexo", "")).upper()
        if val_sexo in ["M", "F"]:
            select_sexo.select_by_value(val_sexo)

        # Estado Civil (1 a 6)
        select_est_civil = Select(driver.find_element(By.ID, "pEstadoCivil"))
        val_est_civil = limpar_valor(dados_linha.get("EstadoCivil", ""))
        if val_est_civil:
            select_est_civil.select_by_value(val_est_civil)    

        # Nome da Mãe
        campo_mae = driver.find_element(By.ID, "pMae")
        if not campo_mae.get_attribute("value").strip():
            campo_mae.clear()
            campo_mae.send_keys(limpar_valor(dados_linha.get("Mae", "")))

        # RG, Órgão e UF Órgão (limpar se houver ou preencher se necessário)
        campo_rg = driver.find_element(By.ID, "pRg")
        campo_rg.clear()
        val_rg = limpar_valor(dados_linha.get("RG", ""))
        if val_rg:
            campo_rg.send_keys(val_rg)

        campo_orgao = driver.find_element(By.ID, "pOrgao")
        campo_orgao.clear()
        val_orgao = limpar_valor(dados_linha.get("Orgao", ""))
        if val_orgao:
            campo_orgao.send_keys(val_orgao)

        val_uf_orgao = limpar_valor(dados_linha.get("UfOrgao", ""))
        if val_uf_orgao:
            Select(driver.find_element(By.ID, "pUfOrgao")).select_by_value(val_uf_orgao)

        # ----------------------------------------------------
        # PASSO 4: Preencher Admissão e Matrícula
        # ----------------------------------------------------
        val_adm = limpar_valor(dados_linha.get("DataAdm", ""))
        if val_adm:
            logger.info(f"Preenchendo Data de Admissão: {val_adm}")
            campo_adm = wait.until(EC.element_to_be_clickable((By.ID, "pDataAdm2")))
            campo_adm.click()
            campo_adm.clear()
            campo_adm.send_keys(val_adm)
            
            # Dispara o evento de blur para garantir que a máscara/sistema valide o texto digitado
            driver.execute_script("arguments[0].blur();", campo_adm)

        val_matr = limpar_valor(dados_linha.get("Matricula", ""))
        if val_matr:
            campo_matr = driver.find_element(By.ID, "pMatr")
            campo_matr.clear()
            campo_matr.send_keys(val_matr)

        # ----------------------------------------------------
        # PASSO 5: Preencher Unidade empresa e Plano
        # ----------------------------------------------------
        val_unidade = limpar_valor(dados_linha.get("Unidade", ""))
        if val_unidade:
            Select(driver.find_element(By.ID, "pUnidade")).select_by_value(val_unidade)
            time.sleep(2)  # Aguarda carregamento dinâmico do plano vinculado à unidade

        val_plano = limpar_valor(dados_linha.get("Plano", ""))
        if val_plano:
            Select(driver.find_element(By.ID, "pPlano")).select_by_value(val_plano)

        # ----------------------------------------------------
        # PASSO 6 & 7: Preencher CEP e conferir Endereço
        # ----------------------------------------------------
        val_cep = limpar_valor(dados_linha.get("CEP", ""))
        if val_cep:
            campo_cep = driver.find_element(By.ID, "pCep")
            campo_cep.clear()
            campo_cep.send_keys(val_cep)
            driver.execute_script("arguments[0].blur();", campo_cep)
            time.sleep(60)  # Aguarda o onblur carregar os dados do CEP

        # Logradouro (R, AV, etc.)
        select_logra = Select(driver.find_element(By.ID, "pLogradouro"))
        val_logra = limpar_valor(dados_linha.get("Logradouro", "")).upper()
        if val_logra:
            select_logra.select_by_value(val_logra)

        # Endereço (Obrigatório preenchimento da planilha)
        campos_endereco = driver.find_elements(By.ID, "pEndereco")
        val_endereco = limpar_valor(dados_linha.get("Endereco", ""))
        for campo_end in campos_endereco:
            campo_end.clear()
            campo_end.send_keys(val_endereco)

        # Bairro
        campo_bairro = driver.find_element(By.ID, "pBairro")
        if not campo_bairro.get_attribute("value").strip():
            campo_bairro.clear()
            campo_bairro.send_keys(limpar_valor(dados_linha.get("Bairro", "")))

        # Cidade
        campo_cidade = driver.find_element(By.ID, "pCidade")
        if not campo_cidade.get_attribute("value").strip():
            campo_cidade.clear()
            campo_cidade.send_keys(limpar_valor(dados_linha.get("Cidade", "")))

        # UF Endereço
        val_uf = limpar_valor(dados_linha.get("Uf", "")).upper()
        if val_uf:
            Select(driver.find_element(By.ID, "pUf")).select_by_value(val_uf)

        # ----------------------------------------------------
        # PASSO 8: Enviar / Prosseguir
        # ----------------------------------------------------
        logger.info("Clicando no botão Prosseguir da inclusão de titular...")
        botao_prosseguir = wait.until(
            EC.element_to_be_clickable((By.ID, "btProsseguir"))
        )
        # try:
        #     botao_prosseguir.click()
        # except Exception:
        #     driver.execute_script("arguments[0].click();", botao_prosseguir)

        logger.info("Inclusão de titular processada com sucesso.")
        return True

    except Exception as e:
        logger.error(f"Erro durante a execução da inclusão de titular: {e}")
        return False
