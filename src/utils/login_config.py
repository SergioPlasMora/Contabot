import logging

def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler('contabot.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)