import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

def configurar_logger():
    logger = logging.getLogger("automacao_novo_projeto")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    # Arquivo
    file_handler = logging.FileHandler(LOG_DIR / "execucao.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def limpar_valor(valor):
    if valor is None:
        return ""
    try:
        if str(valor) == "nan":
            return ""
    except Exception:
        pass
    return str(valor).strip()