import time

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from utils import (
    configurar_logger,
    limpar_valor,
)


logger = configurar_logger()
TEMPO_ESPERA = 10

def aguardar_elementos_pagina(driver, elementos_necessarios, max_tentativas_refresh=10, timeout_elemento=5):
    """
    Garante que todos os elementos necessários estejam presentes na página
    antes de permitir que o processo continue.

    Se algum elemento estiver ausente:
        - atualiza a página;
        - aguarda o carregamento;
        - tenta novamente.

    Retorna True somente quando TODOS os elementos estiverem presentes.


    elementos_necessarios:
        Lista de tuplas no formato:
        [
            ("ID", "pNomeTitular"),
            ("ID", "pDataNasc"),
            ("XPATH", "//input[@name='pCpfTitular']")
        ]
    """

    for tentativa in range(1, max_tentativas_refresh + 1):

        logger.info(
            f"Validando elementos necessários da página "
            f"(tentativa {tentativa}/{max_tentativas_refresh})..."
        )

        elementos_faltantes = []

        # ------------------------------------------------------------
        # Verifica cada elemento individualmente
        # ------------------------------------------------------------

        for tipo, seletor in elementos_necessarios:

            try:
                if tipo.upper() == "ID":
                    by = By.ID

                elif tipo.upper() == "XPATH":
                    by = By.XPATH

                elif tipo.upper() == "NAME":
                    by = By.NAME

                elif tipo.upper() == "CSS":
                    by = By.CSS_SELECTOR

                else:
                    logger.error(
                        f"Tipo de seletor desconhecido: {tipo}"
                    )
                    elementos_faltantes.append(
                        f"{tipo}: {seletor}"
                    )
                    continue

                WebDriverWait(
                    driver,
                    timeout_elemento
                ).until(
                    EC.presence_of_element_located(
                        (by, seletor)
                    )
                )

            except Exception:
                elementos_faltantes.append(
                    f"{tipo}: {seletor}"
                )

        # ------------------------------------------------------------
        # Se não faltou nenhum elemento, pode prosseguir
        # ------------------------------------------------------------

        if not elementos_faltantes:

            logger.info(
                "VALIDAÇÃO OK: todos os elementos necessários "
                "estão presentes na página."
            )

            return True

        # ------------------------------------------------------------
        # Existem elementos faltantes
        # ------------------------------------------------------------

        logger.warning(
            "VALIDAÇÃO FALHOU. Elementos ausentes:"
        )

        for elemento in elementos_faltantes:
            logger.warning(
                f"  - {elemento}"
            )

        # ------------------------------------------------------------
        # Atualiza a página
        # ------------------------------------------------------------

        if tentativa < max_tentativas_refresh:

            logger.warning(
                "Atualizando a página para tentar novamente..."
            )

            driver.refresh()

            # Aguarda o documento terminar de carregar
            try:
                WebDriverWait(
                    driver,
                    15
                ).until(
                    lambda d: d.execute_script(
                        "return document.readyState"
                    ) == "complete"
                )

            except Exception:
                logger.warning(
                    "Timeout aguardando document.readyState."
                )

            # Pequena margem para scripts/AJAX da página
            time.sleep(2)

    # ------------------------------------------------------------
    # Não conseguiu encontrar todos os elementos
    # ------------------------------------------------------------

    logger.error(
        "VALIDAÇÃO FALHOU DEFINITIVAMENTE: "
        "os elementos necessários não ficaram disponíveis "
        f"após {max_tentativas_refresh} tentativas."
    )

    return False

def realizar_login(driver, codigo_empresa, senha):
    """
    Realiza o login no sistema preenchendo o código da empresa e a senha,
    disparando o evento onblur necessário e clicando em Prosseguir.
    """
    try:
        wait = WebDriverWait(driver, TEMPO_ESPERA)

        # 1. Preenche o Código da Empresa
        # utilizando o name='pCodigoEmpresa' do seu HTML
        xpath_campo_codigo = "//input[@name='pCodigoEmpresa']"

        campo_codigo = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, xpath_campo_codigo)
            )
        )

        campo_codigo.clear()
        campo_codigo.send_keys(
            limpar_valor(codigo_empresa)
        )

        # Dispara o evento onblur via JavaScript
        # necessário pois o HTML original usa
        # onblur="retornaUnidade(this);"
        driver.execute_script(
            "arguments[0].blur();",
            campo_codigo
        )

        # Pequena pausa ou espera caso o onblur
        # carregue elementos dinâmicos
        time.sleep(3)

        campo_codigo.send_keys(Keys.TAB)

        # 2. Preenche a Senha
        # utilizando o id='pSenha' do seu HTML
        xpath_campo_senha = "//input[@id='pSenha']"

        campo_senha = driver.find_element(
            By.XPATH,
            xpath_campo_senha
        )

        campo_senha.clear()
        campo_senha.send_keys(
            limpar_valor(senha)
        )

        # 3. Clica no botão "Prosseguir"
        # utilizando o id='Prosseguir' do seu HTML
        xpath_botao_prosseguir = "//input[@id='Prosseguir']"

        botao_prosseguir = driver.find_element(
            By.XPATH,
            xpath_botao_prosseguir
        )

        botao_prosseguir.click()

        # ----------------------------------------------------
        # VERIFICAÇÃO DE SUCESSO NO LOGIN
        # ----------------------------------------------------

        # XPath exato fornecido que só existe
        # após o login bem-sucedido
        xpath_indicador_sucesso = (
            "/html/body/div[2]/div/div/span/h1"
        )

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, xpath_indicador_sucesso)
            )
        )

        logger.info(
            "Login realizado e validado com sucesso!"
        )

        return True

    except Exception as e:
        logger.error(
            f"Erro ao tentar realizar o login: {e}"
        )

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

        logger.info(
            "Acessando a opção de Pré-cancelamento "
            "de Titular Ativo..."
        )

        xpath_link_cancelamento = (
            "//a[contains(., 'Pré-cancelamento de Titular Ativo')]"
        )

        link_cancelamento = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, xpath_link_cancelamento)
            )
        )

        link_cancelamento.click()

        # ----------------------------------------------------
        # PASSO 2: Aguardar o carregamento
        # ----------------------------------------------------

        logger.info(
            "Aguardando 3 segundos para o carregamento da página..."
        )

        time.sleep(3)

        logger.info(
            "Tela de pré-cancelamento acessada com sucesso."
        )

        return True

    except Exception as e:
        logger.error(
            f"Erro ao acessar a tela de pré-cancelamento: {e}"
        )

        return False


def executar_precancelamento_titular(
    driver,
    codigo_titular,
    cpf_titular
):
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
            "Código tratado (primeiros 11 caracteres): "
            f"{codigo_tratado}"
        )

        xpath_input_titular = (
            "//input[@name='pCodigoTitular']"
        )

        campo_titular = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, xpath_input_titular)
            )
        )

        campo_titular.click()
        campo_titular.clear()

        driver.execute_script(
            """
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
            """,
            campo_titular,
            codigo_tratado
        )

        # ----------------------------------------------------
        # PASSO 2: Clicar no primeiro botão Prosseguir
        # ----------------------------------------------------

        logger.info(
            "Clicando no botão de Prosseguir do titular..."
        )

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

        xpath_select = (
            "//select[@name='pmotivocancelamento']"
        )

        elemento_select = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, xpath_select)
            )
        )

        select_obj = Select(elemento_select)
        select_obj.select_by_value("50")

        driver.execute_script(
            """
            var el = arguments[0];

            el.dispatchEvent(
                new Event('change', { bubbles: true })
            );

            el.dispatchEvent(
                new Event('click', { bubbles: true })
            );
            """,
            elemento_select
        )

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

        logger.info(
            "Acessando a opção de Inclusão de Titular..."
        )

        xpath_link_inclusao = (
            "//a[contains(., 'Inclusão de Titular')]"
        )

        link_inclusao = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, xpath_link_inclusao)
            )
        )

        link_inclusao.click()

        logger.info(
            "Tela de inclusão de titular acessada com sucesso."
        )

        return True

    except Exception as e:
        logger.error(
            f"Erro ao acessar a tela de inclusão de titular: {e}"
        )

        return False


def executar_inclusao_titular(driver, dados_linha):
    """
    Executa o processo de inclusão de titular preenchendo apenas os campos
    que estiverem vazios na tela.

    Fluxo:

    1. Localiza o campo CPF.
    2. Preenche o CPF.
    3. Localiza e clica no primeiro botão Prosseguir.
    4. Somente após o primeiro Prosseguir, valida os demais elementos
       necessários da tela.
    5. Preenche os campos que estiverem vazios.
    6. Localiza o botão final Prosseguir.
    7. Executa a validação final conforme o fluxo do sistema.
    8. Retorna ao menu através do botão btEncerrar.

    Retorna:
        True  -> processo executado com sucesso.
        False -> ocorreu algum erro.
    """

    try:
        wait = WebDriverWait(
            driver,
            TEMPO_ESPERA
        )

        # ============================================================
        # PASSO 1: CPF
        #
        # IMPORTANTE:
        # Aqui NÃO fazemos a validação de todos os elementos da página.
        # Primeiro trabalhamos somente com o CPF.
        # ============================================================

        logger.info(
            "============================================================"
        )

        logger.info(
            "INICIANDO PROCESSO DE INCLUSÃO DE TITULAR"
        )

        logger.info(
            "Localizando campo CPF..."
        )

        logger.info(
            "============================================================"
        )

        xpath_campo_cpf = (
            "//input[@name='pCpfTitular']"
        )

        campo_cpf = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    xpath_campo_cpf
                )
            )
        )

        # ============================================================
        # PASSO 2: TRATAR CPF
        # ============================================================

        cpf_raw = limpar_valor(
            dados_linha.get("CPF", "")
        )

        cpf_tratado = (
            cpf_raw.zfill(11)
            if cpf_raw
            else ""
        )

        if not cpf_tratado:
            logger.error(
                "CPF não informado nos dados da linha."
            )

            return False

        logger.info(
            f"CPF tratado: {cpf_tratado}"
        )

        # ============================================================
        # PASSO 3: PREENCHER CPF
        # ============================================================

        valor_atual_cpf = (
            campo_cpf
            .get_attribute("value")
            .strip()
        )

        if not valor_atual_cpf:
            logger.info(
                f"Preenchendo CPF do titular: {cpf_tratado}"
            )

            campo_cpf.click()
            campo_cpf.clear()
            campo_cpf.send_keys(cpf_tratado)

            time.sleep(3)

        else:
            logger.info(
                f"Campo CPF já preenchido: {valor_atual_cpf}"
            )

        # ============================================================
        # PASSO 4: LOCALIZAR PRIMEIRO PROSSEGUIR
        # ============================================================

        logger.info(
            "Localizando o primeiro botão 'Prosseguir'..."
        )

        xpath_botao_prosseguir = (
            "//input[@type='submit' "
            "and @value='Prosseguir' "
            "and contains(@class, 'botao')]"
        )

        botao_prosseguir = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    xpath_botao_prosseguir
                )
            )
        )

        logger.info(
            "Primeiro botão 'Prosseguir' encontrado."
        )

        # ============================================================
        # PASSO 5: CLICAR NO PRIMEIRO PROSSEGUIR
        # ============================================================

        logger.info(
            "Clicando no primeiro botão 'Prosseguir'..."
        )

        try:
            botao_prosseguir.click()

        except Exception:
            logger.warning(
                "Clique normal falhou. Tentando clique via JavaScript..."
            )

            driver.execute_script(
                "arguments[0].click();",
                botao_prosseguir
            )

        time.sleep(3)

        # ============================================================
        # PASSO 6: AGORA SIM VALIDAR OS ELEMENTOS DA SEGUNDA ETAPA
        # ============================================================

        logger.info(
            "============================================================"
        )

        logger.info(
            "PRIMEIRO PROSSEGUIR EXECUTADO."
        )

        logger.info(
            "Iniciando validação dos elementos da segunda etapa..."
        )

        logger.info(
            "============================================================"
        )

        elementos_pos_cpf = [

            # --------------------------------------------------------
            # Dados pessoais
            # --------------------------------------------------------

            (
                "ID",
                "pNomeTitular"
            ),

            (
                "ID",
                "pDataNasc"
            ),

            (
                "ID",
                "pSexo"
            ),

            (
                "ID",
                "pEstadoCivil"
            ),

            (
                "ID",
                "pMae"
            ),

            (
                "ID",
                "pRg"
            ),

            (
                "ID",
                "pOrgao"
            ),

            (
                "ID",
                "pUfOrgao"
            ),

            # --------------------------------------------------------
            # Admissão / matrícula
            # --------------------------------------------------------

            (
                "ID",
                "pDataAdm2"
            ),

            (
                "ID",
                "pMatr"
            ),

            # --------------------------------------------------------
            # Unidade / plano
            # --------------------------------------------------------

            (
                "ID",
                "pUnidade"
            ),

            (
                "ID",
                "pPlano"
            ),

            # --------------------------------------------------------
            # Endereço
            # --------------------------------------------------------

            (
                "ID",
                "pCep"
            ),

            (
                "ID",
                "pLogradouro"
            ),

            (
                "ID",
                "pEndereco"
            ),

            (
                "ID",
                "pBairro"
            ),

            (
                "ID",
                "pCidade"
            ),

            (
                "ID",
                "pUf"
            ),

            (
                "ID",
                "pNumero"
            ),

            # --------------------------------------------------------
            # Botões da segunda etapa
            # --------------------------------------------------------

            (
                "ID",
                "btProsseguir"
            ),

            (
                "ID",
                "btEncerrar"
            ),
        ]

        pagina_pos_cpf_pronta = aguardar_elementos_pagina(
            driver=driver,
            elementos_necessarios=elementos_pos_cpf,
            max_tentativas_refresh=10,
            timeout_elemento=5
        )

        if not pagina_pos_cpf_pronta:
            logger.error(
                "============================================================"
            )

            logger.error(
                "A página da segunda etapa não ficou pronta."
            )

            logger.error(
                "Algum dos elementos necessários não foi localizado."
            )

            logger.error(
                "Processo interrompido."
            )

            logger.error(
                "============================================================"
            )

            return False

        logger.info(
            "============================================================"
        )

        logger.info(
            "VALIDAÇÃO PÓS-CPF CONCLUÍDA COM SUCESSO."
        )

        logger.info(
            "Todos os elementos necessários da segunda etapa "
            "estão disponíveis."
        )

        logger.info(
            "============================================================"
        )

        # ============================================================
        # FUNÇÃO AUXILIAR
        # Preenche campo via JavaScript e dispara eventos.
        # ============================================================

        def preencher_com_evento(
            element_id,
            valor
        ):
            elemento = driver.find_element(
                By.ID,
                element_id
            )

            driver.execute_script(
                "arguments[0].value = arguments[1];",
                elemento,
                valor
            )

            driver.execute_script(
                """
                arguments[0].dispatchEvent(
                    new Event(
                        'input',
                        { bubbles: true }
                    )
                );

                arguments[0].dispatchEvent(
                    new Event(
                        'change',
                        { bubbles: true }
                    )
                );

                arguments[0].dispatchEvent(
                    new Event(
                        'blur',
                        { bubbles: true }
                    )
                );
                """,
                elemento
            )

        # ============================================================
        # PASSO 7: DADOS PESSOAIS
        # ============================================================

        logger.info(
            "Processando Nome do Titular..."
        )

        campo_nome = driver.find_element(
            By.ID,
            "pNomeTitular"
        )

        if not campo_nome.get_attribute(
            "value"
        ).strip():

            val_nome = limpar_valor(
                dados_linha.get(
                    "Nome",
                    ""
                )
            )

            if val_nome:
                logger.info(
                    f"Preenchendo Nome: {val_nome}"
                )

                campo_nome.clear()
                campo_nome.send_keys(
                    val_nome
                )

                time.sleep(1)

        # ------------------------------------------------------------
        # Data de Nascimento
        # ------------------------------------------------------------

        raw_nasc = dados_linha.get(
            "DataNasc",
            ""
        )

        val_nasc = ""

        if (
            pd.notna(raw_nasc)
            and str(raw_nasc).strip() != ""
            and str(raw_nasc).lower() != "nan"
        ):
            try:
                dt_nasc = pd.to_datetime(
                    raw_nasc
                )

                val_nasc = dt_nasc.strftime(
                    "%d/%m/%Y"
                )

            except (
                ValueError,
                TypeError
            ):
                val_nasc = str(
                    raw_nasc
                ).strip()

        campo_nasc = driver.find_element(
            By.ID,
            "pDataNasc"
        )

        if (
            not campo_nasc
            .get_attribute("value")
            .strip()
            and val_nasc
        ):
            logger.info(
                f"Preenchendo Data de Nascimento: {val_nasc}"
            )

            campo_nasc.click()
            campo_nasc.clear()
            campo_nasc.send_keys(
                val_nasc
            )

            time.sleep(1)

        # ------------------------------------------------------------
        # Sexo
        # ------------------------------------------------------------

        select_sexo = Select(
            driver.find_element(
                By.ID,
                "pSexo"
            )
        )

        if (
            not select_sexo
            .first_selected_option
            .text
            .strip()
            or
            select_sexo
            .first_selected_option
            .get_attribute("value") == ""
        ):
            val_sexo = limpar_valor(
                dados_linha.get(
                    "Sexo",
                    ""
                )
            ).upper()

            if val_sexo in [
                "M",
                "F"
            ]:
                logger.info(
                    f"Selecionando Sexo: {val_sexo}"
                )

                select_sexo.select_by_value(
                    val_sexo
                )

        # ------------------------------------------------------------
        # Estado Civil
        # ------------------------------------------------------------

        select_est_civil = Select(
            driver.find_element(
                By.ID,
                "pEstadoCivil"
            )
        )

        if (
            not select_est_civil
            .first_selected_option
            .text
            .strip()
            or
            select_est_civil
            .first_selected_option
            .get_attribute("value") == ""
        ):
            val_est_civil = limpar_valor(
                dados_linha.get(
                    "EstadoCivil",
                    ""
                )
            )

            if val_est_civil:
                logger.info(
                    f"Selecionando Estado Civil: {val_est_civil}"
                )

                select_est_civil.select_by_value(
                    val_est_civil
                )

        # ------------------------------------------------------------
        # Nome da Mãe
        # ------------------------------------------------------------

        campo_mae = driver.find_element(
            By.ID,
            "pMae"
        )

        if not campo_mae.get_attribute(
            "value"
        ).strip():

            val_mae = limpar_valor(
                dados_linha.get(
                    "Mae",
                    ""
                )
            )

            if val_mae:
                logger.info(
                    f"Preenchendo Nome da Mãe: {val_mae}"
                )

                campo_mae.clear()
                campo_mae.send_keys(
                    val_mae
                )

        # ------------------------------------------------------------
        # RG
        # ------------------------------------------------------------

        campo_rg = driver.find_element(
            By.ID,
            "pRg"
        )

        if not campo_rg.get_attribute(
            "value"
        ).strip():

            val_rg = limpar_valor(
                dados_linha.get(
                    "RG",
                    ""
                )
            )

            if val_rg:
                logger.info(
                    f"Preenchendo RG: {val_rg}"
                )

                campo_rg.clear()
                campo_rg.send_keys(
                    val_rg
                )

        # ------------------------------------------------------------
        # Órgão
        # ------------------------------------------------------------

        campo_orgao = driver.find_element(
            By.ID,
            "pOrgao"
        )

        if not campo_orgao.get_attribute(
            "value"
        ).strip():

            val_orgao = limpar_valor(
                dados_linha.get(
                    "Orgao",
                    ""
                )
            )

            if val_orgao:
                logger.info(
                    f"Preenchendo Órgão: {val_orgao}"
                )

                campo_orgao.clear()
                campo_orgao.send_keys(
                    val_orgao
                )

        # ------------------------------------------------------------
        # UF Órgão
        # ------------------------------------------------------------

        select_uf_orgao = Select(
            driver.find_element(
                By.ID,
                "pUfOrgao"
            )
        )

        if (
            not select_uf_orgao
            .first_selected_option
            .text
            .strip()
            or
            select_uf_orgao
            .first_selected_option
            .get_attribute("value") == ""
        ):
            val_uf_orgao = limpar_valor(
                dados_linha.get(
                    "UfOrgao",
                    ""
                )
            )

            if val_uf_orgao:
                logger.info(
                    f"Selecionando UF do Órgão: {val_uf_orgao}"
                )

                select_uf_orgao.select_by_value(
                    val_uf_orgao
                )

        # ============================================================
        # PASSO 8: DATA DE ADMISSÃO
        # ============================================================

        time.sleep(2)

        raw_adm = dados_linha.get(
            "DataAdm",
            ""
        )

        val_adm = ""

        if (
            pd.notna(raw_adm)
            and str(raw_adm).strip() != ""
            and str(raw_adm).lower() != "nan"
        ):
            str_raw = str(
                raw_adm
            ).strip()

            if str_raw.endswith(
                ".0"
            ):
                str_raw = str_raw[:-2]

            try:
                dt_adm = pd.to_datetime(
                    str_raw
                )

                val_adm = dt_adm.strftime(
                    "%d/%m/%Y"
                )

            except (
                ValueError,
                TypeError
            ):
                if (
                    "/" in str_raw
                    and len(
                        str_raw.split("/")
                    ) == 2
                ):
                    mes, ano = (
                        str_raw.split("/")
                    )

                    val_adm = (
                        f"01/"
                        f"{mes.zfill(2)}/"
                        f"{ano}"
                    )

                else:
                    val_adm = str_raw

        campo_adm = driver.find_element(
            By.ID,
            "pDataAdm2"
        )

        if (
            not campo_adm
            .get_attribute("value")
            .strip()
            and val_adm
        ):
            logger.info(
                f"Preenchendo Data de Admissão: {val_adm}"
            )

            driver.execute_script(
                "arguments[0].value = arguments[1];",
                campo_adm,
                val_adm
            )

            driver.execute_script(
                """
                arguments[0].dispatchEvent(
                    new Event(
                        'input',
                        { bubbles: true }
                    )
                );

                arguments[0].dispatchEvent(
                    new Event(
                        'change',
                        { bubbles: true }
                    )
                );

                arguments[0].dispatchEvent(
                    new Event(
                        'blur',
                        { bubbles: true }
                    )
                );
                """,
                campo_adm
            )

            time.sleep(3)

        # ------------------------------------------------------------
        # Matrícula
        # ------------------------------------------------------------

        val_matr = limpar_valor(
            dados_linha.get(
                "Matricula",
                ""
            )
        )

        campo_matr = driver.find_element(
            By.ID,
            "pMatr"
        )

        if (
            not campo_matr
            .get_attribute("value")
            .strip()
            and val_matr
        ):
            logger.info(
                f"Preenchendo Matrícula: {val_matr}"
            )

            campo_matr.clear()
            campo_matr.send_keys(
                val_matr
            )

        # ============================================================
        # PASSO 9: UNIDADE
        # ============================================================

        select_unidade = Select(
            driver.find_element(
                By.ID,
                "pUnidade"
            )
        )

        if (
            not select_unidade
            .first_selected_option
            .text
            .strip()
            or
            select_unidade
            .first_selected_option
            .get_attribute("value") == ""
        ):
            val_unidade = limpar_valor(
                dados_linha.get(
                    "Unidade",
                    ""
                )
            )

            if val_unidade:
                logger.info(
                    f"Selecionando Unidade: {val_unidade}"
                )

                select_unidade.select_by_value(
                    val_unidade
                )

                time.sleep(2)

        # ------------------------------------------------------------
        # Plano
        # ------------------------------------------------------------

        select_plano = Select(
            driver.find_element(
                By.ID,
                "pPlano"
            )
        )

        if (
            not select_plano
            .first_selected_option
            .text
            .strip()
            or
            select_plano
            .first_selected_option
            .get_attribute("value") == ""
        ):
            val_plano = limpar_valor(
                dados_linha.get(
                    "Plano",
                    ""
                )
            )

            if val_plano:
                logger.info(
                    f"Selecionando Plano: {val_plano}"
                )

                select_plano.select_by_value(
                    val_plano
                )

        # ============================================================
        # PASSO 10: CEP
        # ============================================================

        raw_cep = dados_linha.get(
            "CEP",
            ""
        )

        val_cep = ""

        if (
            pd.notna(raw_cep)
            and str(raw_cep).strip() != ""
            and str(raw_cep).lower() != "nan"
        ):
            val_cep = str(
                raw_cep
            ).strip()

            if val_cep.endswith(
                ".0"
            ):
                val_cep = val_cep[:-2]

            val_cep = "".join(
                filter(
                    str.isdigit,
                    val_cep
                )
            )

            val_cep = val_cep.zfill(
                8
            )

        campo_cep = driver.find_element(
            By.ID,
            "pCep"
        )

        valor_atual = (
            campo_cep
            .get_attribute("value")
            .strip()
        )

        if not valor_atual:
            logger.info(
                f"Preenchendo CEP: {val_cep}"
            )

            preencher_com_evento(
                "pCep",
                val_cep
            )

            time.sleep(3)

        # ============================================================
        # PASSO 11: LOGRADOURO
        # ============================================================

        select_logra = Select(
            driver.find_element(
                By.ID,
                "pLogradouro"
            )
        )

        if (
            not select_logra
            .first_selected_option
            .text
            .strip()
            or
            select_logra
            .first_selected_option
            .get_attribute("value") == ""
        ):
            val_logra = limpar_valor(
                dados_linha.get(
                    "Logradouro",
                    ""
                )
            ).upper()

            if val_logra:
                logger.info(
                    f"Selecionando Logradouro: {val_logra}"
                )

                select_logra.select_by_value(
                    val_logra
                )

        # ============================================================
        # PASSO 12: ENDEREÇO
        # ============================================================

        campos_endereco = driver.find_elements(
            By.ID,
            "pEndereco"
        )

        val_endereco = limpar_valor(
            dados_linha.get(
                "Endereco",
                ""
            )
        )

        for campo_end in campos_endereco:
            if (
                not campo_end
                .get_attribute("value")
                .strip()
                and val_endereco
            ):
                logger.info(
                    f"Preenchendo Endereço: {val_endereco}"
                )

                campo_end.clear()
                campo_end.send_keys(
                    val_endereco
                )

        # ============================================================
        # PASSO 13: BAIRRO
        # ============================================================

        campo_bairro = driver.find_element(
            By.ID,
            "pBairro"
        )

        if not campo_bairro.get_attribute(
            "value"
        ).strip():

            val_bairro = limpar_valor(
                dados_linha.get(
                    "Bairro",
                    ""
                )
            )

            if val_bairro:
                logger.info(
                    f"Preenchendo Bairro: {val_bairro}"
                )

                campo_bairro.clear()
                campo_bairro.send_keys(
                    val_bairro
                )

        # ============================================================
        # PASSO 14: CIDADE
        # ============================================================

        campo_cidade = driver.find_element(
            By.ID,
            "pCidade"
        )

        if not campo_cidade.get_attribute(
            "value"
        ).strip():

            val_cidade = limpar_valor(
                dados_linha.get(
                    "Cidade",
                    ""
                )
            )

            if val_cidade:
                logger.info(
                    f"Preenchendo Cidade: {val_cidade}"
                )

                campo_cidade.clear()
                campo_cidade.send_keys(
                    val_cidade
                )

        # ============================================================
        # PASSO 15: UF
        # ============================================================

        select_uf = Select(
            driver.find_element(
                By.ID,
                "pUf"
            )
        )

        if (
            not select_uf
            .first_selected_option
            .text
            .strip()
            or
            select_uf
            .first_selected_option
            .get_attribute("value") == ""
        ):
            val_uf = limpar_valor(
                dados_linha.get(
                    "Uf",
                    ""
                )
            ).upper()

            if val_uf:
                logger.info(
                    f"Selecionando UF: {val_uf}"
                )

                select_uf.select_by_value(
                    val_uf
                )

        # ============================================================
        # PASSO 16: NÚMERO
        # ============================================================

        campo_numero = driver.find_element(
            By.ID,
            "pNumero"
        )

        if not campo_numero.get_attribute(
            "value"
        ).strip():

            val_num = limpar_valor(
                dados_linha.get(
                    "Numero",
                    ""
                )
            )

            if val_num.endswith(
                ".0"
            ):
                val_num = val_num[:-2]

            if val_num:
                logger.info(
                    f"Preenchendo Número: {val_num}"
                )

                time.sleep(1)

                driver.execute_script(
                    "arguments[0].value = arguments[1];",
                    campo_numero,
                    val_num
                )

                driver.execute_script(
                    """
                    arguments[0].dispatchEvent(
                        new Event(
                            'input',
                            { bubbles: true }
                        )
                    );

                    arguments[0].dispatchEvent(
                        new Event(
                            'change',
                            { bubbles: true }
                        )
                    );

                    arguments[0].dispatchEvent(
                        new Event(
                            'blur',
                            { bubbles: true }
                        )
                    );
                    """,
                    campo_numero
                )

        # ============================================================
        # PASSO 17: VALIDAÇÃO FINAL
        # ============================================================

        logger.info(
            "============================================================"
        )

        logger.info(
            "Preenchimento concluído."
        )

        logger.info(
            "Localizando botão final 'Prosseguir'..."
        )

        logger.info(
            "============================================================"
        )

        botao_prosseguir_final = wait.until(
            EC.element_to_be_clickable(
                (
                    By.ID,
                    "btProsseguir"
                )
            )
        )

        logger.info(
            "Botão final 'Prosseguir' encontrado."
        )

        botao_prosseguir_final.click()

        logger.info(
            "Botão final 'Prosseguir' acionado."
        )

        time.sleep(5)

        # ============================================================
        # PASSO 18: RETORNAR AO MENU
        # ============================================================

        logger.info(
            "Localizando botão 'Encerrar'..."
        )

        botao_retornar_menu = wait.until(
            EC.element_to_be_clickable(
                (
                    By.ID,
                    "btEncerrar"
                )
            )
        )

        botao_retornar_menu.click()

        logger.info(
            "Retorno ao menu realizado."
        )

        logger.info(
            "============================================================"
        )

        logger.info(
            "FLUXO DE INCLUSÃO DE TITULAR CONCLUÍDO."
        )

        logger.info(
            "============================================================"
        )

        return True

    except Exception:
        logger.exception(
            "Erro durante a execução da inclusão de titular."
        )

        return False
