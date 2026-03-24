import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


def info(message):
    logging.info(message)


def warning(message):
    logging.warning(message)


def error(message):
    logging.error(message)
