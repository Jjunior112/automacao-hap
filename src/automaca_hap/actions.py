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


def executar_precancelamento_titular(driver, codigo_titular, cpf_titular):
    """
    Executa o fluxo completo de pré-cancelamento:
    1. Clica no menu de pré-cancelamento.
    2. Aguarda 3 segundos.
    3. Preenche o input pCodigoTitular com os primeiros 11 caracteres.
    4. Clica no primeiro botão de submit 'Prosseguir'.
    5. Verifica se ocorreu erro de código inválido na tela.
    6. Seleciona a opção 'DEMISSAO ROTATIVA' no select de motivos.
    7. Valida se o CPF exibido na tela após 'CPF USUÁRIO TITULAR:' bate com o parâmetro 'cpf_titular'.
    8. Clica no botão final de submit 'Prosseguir'.
    """
    try:
        wait = WebDriverWait(driver, TEMPO_ESPERA)

        # ----------------------------------------------------
        # PASSO 1: Acessar a tela de pré-cancelamento
        # ----------------------------------------------------
        logger.info("Acessando a opção de Pré-cancelamento de Titular Ativo...")
        xpath_link_cancelamento = "//a[contains(., 'Pré-cancelamento de Titular Ativo')]"
        link_cancelamento = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_link_cancelamento)))
        link_cancelamento.click()

        # ----------------------------------------------------
        # PASSO 2: Aguardar o carregamento
        # ----------------------------------------------------
        logger.info("Aguardando 3 segundos para o carregamento da página...")
        time.sleep(3)

        # ----------------------------------------------------
        # PASSO 3: Tratar o código e preencher o input
        # ----------------------------------------------------
        codigo_tratado = str(codigo_titular)[:11]
        logger.info(f"Código tratado (primeiros 11 caracteres): {codigo_tratado}")

        xpath_input_titular = "//input[@name='pCodigoTitular']"
        campo_titular = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_input_titular)))
        
        campo_titular.click()
        campo_titular.clear()
        
        driver.execute_script("""
            var el = arguments[0];
            var valor = arguments[1];
            el.value = valor;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.dispatchEvent(new Event('blur', { bubbles: true }));
        """, campo_titular, codigo_tratado)

        # ----------------------------------------------------
        # PASSO 4: Clicar no botão Prosseguir (Primeiro Submit)
        # ----------------------------------------------------
        logger.info("Clicando no botão de Prosseguir do titular...")
        xpath_botao_prosseguir_1 = "//input[@type='submit' and @value='Prosseguir' and contains(@class, 'botao')]"
        botao_prosseguir_1 = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_botao_prosseguir_1)))
        
        try:
            botao_prosseguir_1.click()
        except Exception:
            driver.execute_script("arguments[0].click();", botao_prosseguir_1)

        # Pequena pausa para garantir o carregamento do retorno da página após o submit
        time.sleep(2)

        # ----------------------------------------------------
        # PASSO 5: Verificar se apareceu a mensagem de Erro de Código Inválido
        # ----------------------------------------------------
        xpath_erro_invalido = "//*[contains(text(), 'ERRO: CÓDIGO TITULAR INVÁLIDO')]"
        elementos_erro = driver.find_elements(By.XPATH, xpath_erro_invalido)
        
        if elementos_erro:
            logger.error("ERRO DETECTADO NA TELA: CÓDIGO TITULAR INVÁLIDO (INEXISTENTE, NÃO ATIVO OU SEM DEPENDENTES).")
            return False

        # ----------------------------------------------------
        # PASSO 6: Selecionar o motivo 'DEMISSAO ROTATIVA' (value="50")
        # ----------------------------------------------------
        logger.info("Selecionando o motivo 'Demissão Rotativa'...")
        xpath_select = "//select[@name='pmotivocancelamento']"
        elemento_select = wait.until(EC.presence_of_element_located((By.XPATH, xpath_select)))

        select_obj = Select(elemento_select)
        select_obj.select_by_value("50")

        driver.execute_script("""
            var el = arguments[0];
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.dispatchEvent(new Event('click', { bubbles: true }));
        """, elemento_select)

        # ----------------------------------------------------
        # PASSO 7: Validação do CPF do Titular antes do Submit Final
        # ----------------------------------------------------
        logger.info("Realizando a validação do CPF do titular na tela...")
        
        # Localiza o texto estruturado que contém 'CPF USUÁRIO TITULAR:' no HTML
        xpath_bloco_info = "//*[contains(text(), 'CPF USUÁRIO TITULAR:')]"
        elemento_info = wait.until(EC.presence_of_element_located((By.XPATH, xpath_bloco_info)))
        
        texto_tela = elemento_info.text.strip()
        
        # Extrai dinamicamente o trecho que vem após 'CPF USUÁRIO TITULAR:'
        if "CPF USUÁRIO TITULAR:" in texto_tela:
            cpf_encontrado = texto_tela.split("CPF USUÁRIO TITULAR:")[1].split("\n")[0].strip()
        else:
            cpf_encontrado = texto_tela.strip()

        # Limpa eventuais caracteres não numéricos para comparar apenas os dígitos do CPF
        cpf_encontrado_limpo = "".join(filter(str.isdigit, cpf_encontrado))
        cpf_planilha_limpo = "".join(filter(str.isdigit, str(cpf_titular)))

        logger.info(f"CPF esperado (Planilha): {cpf_planilha_limpo}")
        logger.info(f"CPF encontrado na tela: {cpf_encontrado_limpo}")

        if cpf_encontrado_limpo != cpf_planilha_limpo:
            logger.error(f"ERRO DE VALIDAÇÃO: O CPF na tela ('{cpf_encontrado_limpo}') diverge do CPF fornecido ('{cpf_planilha_limpo}').")
            return False

        logger.info("Validação do CPF realizada com sucesso! Os CPFs coincidem.")

        # ----------------------------------------------------
        # PASSO 8: Clicar no botão Prosseguir final (Segundo Submit)
        # ----------------------------------------------------
        logger.info("Clicando no botão de Prosseguir final após a validação...")
        
        xpath_botao_prosseguir_final = "//input[@type='submit' and @value='Prosseguir' and contains(@class, 'botao')]"
        botao_prosseguir_final = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_botao_prosseguir_final)))
        
        try:
            botao_prosseguir_final.click()
        except Exception:
            driver.execute_script("arguments[0].click();", botao_prosseguir_final)

        logger.info("Fluxo completo de pré-cancelamento validado por CPF e submetido com sucesso.")
        return True

    except Exception as e:
        logger.error(f"Erro durante a execução do fluxo de pré-cancelamento: {e}")
        return False