# Automação Hapvida — Inclusão e Pré-Cancelamento de Titulares

Automação em Python com **Selenium** para login no portal Hapvida e processamento em lote de titulares a partir de uma planilha Excel. O fluxo é controlado pela coluna **Acao**: inclusão de titular ou pré-cancelamento de titular ativo. Dependências e ambiente são gerenciados pelo **`uv`**.

---

## Tecnologias

* **Python** `>= 3.14` (versão pinada em `.python-version`)
* **`uv`** — gerenciador de pacotes e ambiente virtual
* **Selenium WebDriver** — automação no Google Chrome
* **Pandas** e **Openpyxl** — leitura e escrita de Excel
* **python-dotenv** — credenciais via `.env`

---

## O que a automação faz

1. Valida a planilha `src/data/dados.xlsx` (arquivo e colunas obrigatórias conforme as ações presentes).
2. Abre o Chrome, acessa a URL de login e autentica **uma vez**, usando o código da primeira empresa válida da planilha e a senha do `.env`.
3. Percorre cada linha e despacha a operação:
   * **Acao `1`** — Inclusão de Titular
   * **Acao `2`** — Pré-cancelamento de Titular Ativo
4. Gera um relatório Excel com `Status` e `Mensagem` em `src/data/processamentos/`.
5. Grava log em terminal e em `src/logs/execucao.log`.

Há uma pausa de 5 segundos entre registros. O Chrome **não** inicia em modo headless (a opção está comentada em `main.py`).

### Ação 1 — Inclusão de Titular

Acessa **Inclusão de Titular**, busca o CPF e preenche apenas campos que estiverem vazios na tela (dados pessoais, admissão, unidade/plano e endereço). Datas são normalizadas para `dd/mm/yyyy`; CEP e CPF são tratados como dígitos.

> **Estado atual:** o clique no botão final de inclusão está desativado. O fluxo valida o preenchimento, retorna ao menu e registra sucesso sem gravar o cadastro no portal.

### Ação 2 — Pré-cancelamento de Titular Ativo

Acessa **Pré-cancelamento de Titular Ativo**, informa os 11 primeiros caracteres da carteirinha, seleciona o motivo **Demissão Rotativa** e confirma. Falha se o portal retornar código de titular inválido (inexistente, não ativo ou sem dependentes).

---

## Estrutura do projeto

```text
automaca-hap/
├── .env                          # URL de login e senha (não versionado)
├── .gitignore
├── README.md
├── pyproject.toml
├── uv.lock
└── src/
    ├── automaca_hap/
    │   ├── __init__.py
    │   ├── main.py               # Orquestração: validação, login e lote
    │   ├── validador_planilha.py # Carga do Excel e colunas obrigatórias
    │   ├── processador.py        # Iteração das linhas e despacho das ações
    │   ├── actions.py            # Login e fluxos Selenium no portal
    │   └── utils.py              # Logger e limpeza de valores
    ├── data/
    │   ├── dados.xlsx            # Planilha de entrada
    │   └── processamentos/       # Relatórios gerados na execução
    └── logs/
        └── execucao.log          # Log da execução
```

---

## Pré-requisitos

* **`uv`** instalado
* **Google Chrome** instalado (o Selenium usa o ChromeDriver correspondente)
* Arquivo **`.env`** na raiz do projeto
* Planilha **`src/data/dados.xlsx`** preenchida

**Linux / macOS:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```powershell
irm https://astral.sh/uv/install.sh | iex
```

---

## Instalação e configuração

1. Acesse a pasta do projeto:

```bash
cd automaca-hap
```

2. Crie o `.env` na raiz:

```ini
URL_LOGIN=
SENHA_LOGIN=
```

3. Sincronize o ambiente e as dependências:

```bash
uv sync
```

4. Prepare `src/data/dados.xlsx` conforme a seção abaixo.

---

## Planilha de entrada

Arquivo: `src/data/dados.xlsx`

A coluna **Acao** é obrigatória. O validador exige colunas extras de acordo com as ações que existirem no arquivo (não precisa ter todas as colunas se a planilha tiver só um tipo de ação).

| Acao | Operação | Colunas obrigatórias na planilha |
| --- | --- | --- |
| `1` | Inclusão de titular | `Empresa`, `Acao`, `CPF`, `Matricula`, `Nome`, `DataNasc`, `Sexo`, `EstadoCivil`, `Mae`, `DataAdm`, `Unidade`, `Plano`, `CEP`, `Endereco`, `Numero`,`Bairro`, `Cidade`, `Uf` |
| `2` | Pré-cancelamento | `Empresa`, `Acao`, `Carteirinha`, `CPF` |

Colunas opcionais usadas na inclusão, se existirem e o campo na tela estiver vazio: `RG`, `Orgao`, `UfOrgao`, `Logradouro`, `Numero`.

### Regras por linha

* Linhas com `Empresa`, `CPF` ou `Acao` vazios são marcadas como erro e ignoradas.
* Ação `1` exige **Matrícula** preenchida.
* Ação `2` exige **Carteirinha** preenchida.
* Ação diferente de `1` ou `2` é registrada como erro.

O login usa o código da **primeira linha válida** (`Empresa` + `CPF`). Todas as linhas da execução compartilham essa sessão.

---

## Como executar

```bash
uv run python src/automaca_hap/main.py
```

O Chrome abre maximizado. Encerrar a janela no meio da execução interrompe o lote; o `finally` do script fecha o navegador ao terminar (com sucesso ou erro fatal).

---

## Relatórios e logs

Ao final, o processador grava em `src/data/processamentos/` um arquivo no formato:

```text
resultado_processamento_17-09-2026_22-30.xlsx
```

O relatório replica as colunas originais e adiciona:

* **Status** — `Sucesso` ou `Erro`
* **Mensagem** — detalhe da operação ou do motivo da falha (campos vazios, ação desconhecida, código inválido, falha no Selenium, etc.)

O log contínuo fica em `src/logs/execucao.log`.

---

## Observações

* A inclusão ainda está em modo de validação: o cadastro **não** é enviado no portal.
* O pré-cancelamento **é** confirmado no portal quando o fluxo conclui com sucesso.
* Há pausas fixas (`sleep`) em login, submits e AJAX (CEP, admissão, unidade). Ambientes lentos podem exigir ajuste desses tempos em `actions.py`.
* Relatórios e logs não devem ser versionados; o `.gitignore` já ignora `.env` e arquivos de log.

---

## Sugestão de arquitetura (nuvem e integração)

Para uso corporativo sem execução manual local:

1. **Container** — empacotar Python, `uv` e Chrome em modo `--headless` e hospedar em VM (Azure, AWS EC2, etc.).
2. **API (FastAPI)** — endpoint `POST` que recebe o Excel, valida colunas em memória e dispara o processamento.
3. **Power Automate** — gatilho em pasta SharePoint/OneDrive, envio do arquivo à API e gravação do Excel de retorno em pastas de sucesso/erro.
