#!homework_bot/homework.py
import logging
import os
import requests
import telegram
import time
from dotenv import load_dotenv
from http import HTTPStatus
from sys import stdout

from exceptions import APIException, EnvironmentalVariableException

# ^ Так ведь? ^

# !!! Дальше философствование, если не хочется читать - не обижусь) !!!
# --------------------------------
# По поводу моей токсичности (оправдываюсь =D): я в жизни вообще незлобный
# человек.
# Просто я учил детей, которые даже речи не имеют из-за своих особенностей, и
# их родителей (несколько лет работал с детьми с ОВЗ, психолог по образованию).
# А видя то, как делают тут, могу сказать - так не учат, позиционируя курс как
# якобы для новичков.

# Если это попытка приучить пользоваться интернетом - то тогда в теоретической
# части нет смысла, так как она неконкурентоспособна, источников в сети куда
# больше и они куда качественнее (хотя бы из-за наличия примеров). С таким же
# успехом можно просто давать в задании спринта темы для самостоятельного
# изучения и проект с ревью, без теории.

# Если цель у курса всё же научить своими силами - надо плавно повышать
# сложность и объяснять на пальцах, а проектные задания давать с
# альтернативными, но не отличными от обучающих примеров условиями. Взрослые
# обучаются куда хуже детей.

# А в итоге имеем теорию, в которой объясняют только основы необходимых для
# проекта тем, потом доходим до самого проекта и сложность резко возрастает,
# так как надо: 1) придерживаться заданной структуры кода, примеров которой в
# теории нигде не приводят 2) из-за отсутствия примеров ты начинаешь бороться с
# автотестами, не понимая, какое именно исправление от тебя хотят. И которые
# почти ничему не учат, если пояснения составлены расплывчато.

# Это я ещё не говорю про особенности обучения взрослого человека,
# предполагающие неизбежную ригидность психики, уровень актуального развития +
# зоны ближайшего развития (относительно нового навыка), да банальный уровень
# занятости и подобные более бытовые штуки.
# --------------------------------


load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

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
    check_empty_tokens = [x for x in environmental_variables if x is None]
    if len(check_empty_tokens) != 0:
        logger.critical(f'Token(s) is not filled.')
        raise EnvironmentalVariableException


def send_message(bot, message) -> None:
    """Отправляет сообщение пользователю."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Message has been sent.')
    except telegram.error.TelegramError as error:
        logger.error(error)


def get_api_answer(timestamp) -> dict:
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
        raise requests.RequestException
    finally:
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            logger.error(f'Response status code is: {response.status_code}')
            raise APIException


def check_response(response) -> None:
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


def parse_status(homework) -> str:
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
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if len(response['homeworks']) != 0:
                last_hw_status = parse_status(response['homeworks'][0])
                send_message(bot, last_hw_status)
            time.sleep(RETRY_PERIOD)
        # Понятия не имею, какой эксепшен тут перехватывать. Как говорится в
        # статье, в таких случаях можно использовать хотя бы класс, хоть и
        # нежелательно.
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(message)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
