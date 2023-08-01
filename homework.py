import logging
import os
import time
from sys import stdout
from typing import Type
from http import HTTPStatus

import telegram
import requests
from dotenv import load_dotenv

from exceptions import APIException, EnvironmentalVariableException


load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> None:
    """Проверяет доступность переменных окружения."""
    environmental_variables = (
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
    )
    if not all(environmental_variables):
        logger.critical('Token(s) is not filled.')
        raise EnvironmentalVariableException


def send_message(bot: Type[telegram.Bot], message: str) -> None:
    """Отправляет сообщение пользователю."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Message has been sent.')
    except telegram.error.TelegramError as error:
        logger.error(error)


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к API."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={
                'from_date': timestamp,
            },
        )
    except requests.RequestException as error:
        logger.error(error)
        raise APIException
    if response.status_code != HTTPStatus.OK:
        logger.error(APIException)
        raise APIException
    return response.json()


def check_response(response: dict) -> None:
    """Проверяет ответ API на соответствие документации."""
    if not {'homeworks', 'current_date'}.issubset(response):
        logger.error('Keys does not match or missing.')
        raise KeyError
    valid_types = (
        isinstance(response, dict)
        and isinstance(response['homeworks'], list)
        and isinstance(response['current_date'], int)
    )
    if not valid_types:
        logger.error('Wrong object type.')
        raise TypeError


def parse_status(homework: dict) -> str:
    """.
    Извлекает из информации о конкретной домашней работе статус этой
    работы.
    """
    try:
        homework_name = homework['homework_name']
        status = homework['status']
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except KeyError as error:
        logger.error(error, exc_info=True)
        raise KeyError


def main() -> None:
    """Основная логика работы программы."""
    message_cache = ''
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if len(response['homeworks']) != 0:
                last_hw_status = parse_status(response['homeworks'][0])
                if last_hw_status != message_cache:
                    message_cache = last_hw_status
                    send_message(bot, message_cache)
            time.sleep(RETRY_PERIOD)
        except (KeyError,
                TypeError,
                EnvironmentalVariableException,
                telegram.error.TelegramError,
                requests.RequestException,
                APIException) as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(message)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
