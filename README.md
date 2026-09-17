# 🤖 Automação de Pré-Cancelamento - Portal Hapvida

Automação em Python utilizando **Selenium** para realizar o login no portal Hapvida e executar o fluxo de pré-cancelamento de titulares em lote, a partir de uma planilha Excel. O projeto gerencia dependências e ambiente de execução de forma moderna e ultrarrápida utilizando o **`uv`**.

---

## 🛠️ Tecnologias Utilizadas

* **Python** (versão gerenciada pelo `uv`)
* **`uv`** (Gerenciador de pacotes e projetos Python)
* **Selenium WebDriver** (Automação web)
* **Pandas & Openpyxl** (Manipulação e leitura/escrita de arquivos Excel)
* **Python-Dotenv** (Gerenciamento de variáveis de ambiente sensíveis)

---

## 📁 Estrutura do Projeto

```text
automacao-hapvida/
├── .env                  # Variáveis de ambiente (URL de login e senha)
├── .gitignore            # Arquivos ignorados pelo Git
├── README.md             # Documentação do projeto
├── pyproject.toml        # Configuração e dependências do uv
├── uv.lock               # Trava de versões do uv
└── src/
    ├── automacao_hap/
    │   ├── __init__.py
    │   ├── actions.py    # Fluxos de login e ações de pré-cancelamento
    │   ├── main.py       # Script principal de execução e controle de lote
    │   └── utils.py      # Funções utilitárias e configuração de logger
    └── data/
        ├── dados.xlsx    # Planilha de entrada com os dados (Empresa, Carteirinha, CPF)
        └── resultado_processamento_*.xlsx # Relatórios gerados após a execução
```

---

## ⚙️ Pré-requisitos

Certifique-se de ter o **`uv`** instalado em sua máquina. Caso não tenha, você pode instalá-lo via terminal:

**Linux / macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
irm https://astral.sh/uv/install.sh | iex
```

---

## 🚀 Instalação e Configuração

1. **Clone o repositório ou acesse a pasta do projeto:**
```bash
cd automacao-hapvida
```

2. **Crie e configure o arquivo `.env` na raiz do projeto contendo as credenciais de acesso:**
```ini
URL_LOGIN=
SENHA_LOGIN=
```

3. **Prepare a planilha de dados:**
O arquivo de entrada deve estar localizado em `src/data/dados.xlsx` contendo obrigatoriamente as seguintes colunas de dados:
* **Empresa**
* **Carteirinha**
* **CPF**

4. **Sincronize as dependências com o `uv`:**
O `uv` criará o ambiente virtual e instalará todas as dependências automaticamente baseando-se no `pyproject.toml`:
```bash
uv sync
```

---

## ▶️ Como Executar

Para rodar a automação utilizando o ambiente virtual gerenciado pelo `uv`, execute:

```bash
uv run python src/automacao_hap/main.py
```

---

## 📊 Relatórios de Saída

Ao finalizar a execução, a automação gerará automaticamente uma planilha de resultado na pasta `src/data/` nomeada com a data e hora exatas da execução (ex: `resultado_processamento_16-09-2026_22-30.xlsx`).

O arquivo conterá todas as colunas originais acrescidas de duas novas colunas de controle:

* **Status:** Indicará `Sucesso` ou `Erro`.
* **Mensagem:** Detalhará o motivo de eventuais falhas (como CPF divergente, código inválido ou campos vazios) ou o sucesso da operação.
