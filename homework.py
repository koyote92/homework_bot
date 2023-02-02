import logging
import requests
import os
import telegram
import time
from dotenv import load_dotenv
from logging import StreamHandler
from sys import stdout
from http import HTTPStatus
from pprint import pprint

# Привет.
# Как всегда. "Обожаю" Яндекс. "Вот вам примеры в начале теории. Но в финальном
# задании спринта мы сделаем вам свою структуру кода, а пример с такой
# структурой не покажем. Вы новички, а новички должны страдать. Те, кто
# переживёт - молодец. Те, кто не переживёт - тупой, пошли вон с курса."
# Я наверное очень токсичный студент, но НОВИЧКОВ так не учат, ИМХО.

# Вообще, может моё мнение неверное, но пихать в автотесты "подсказки" типа
# "Убедитесь, что при корректном ответе API функция `check_response`
# не вызывает исключений." это издевательство. У меня она блин не вызывает
# исключений, почему нельзя просто сказать, чего от меня хотят???

# И да, я извиняюсь за свои докстринги, но менять их принципиально не хочу.
# В своё оправдание скажу, что я сейчас занимаюсь автоматизацией на селениуме
# и ОБЯЗАТЕЛЬНО пишу докстринги. Меня просто до глубины души раздражает
# подача материала, поэтому я психую. На эту угадайку "что имел в виду автор
# теста" ночью уходит по три часа. Я в это время могу спать, блин. Но нет, не
# угадал, как обойти assert - сиди, тыкайся.

# Из-за этого вроде бы интересная тема ботов превращается в бодание с ассертами
# и единственное, что ты запоминаешь - это мысли "да какого чёрта тебе надо,
# автор тестов, подавись уже".

# Другое дело, когда ты присылаешь ревью и говоришь - вот тут не так, лучше
# поменять на вот это, потому что вот так.


load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stdout)
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


def check_tokens():
    """Puta mierda."""
    environmental_variables = (
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    )
    for variable in environmental_variables:
        if variable is None:
            logger.critical(f'Token {variable} is not filled.')
            raise Exception


def send_message(bot, message):
    """Puta mierda."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Всё ок.')
    except Exception as error:
        logger.error(error)


def get_api_answer(timestamp):
    """Puta mierda."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={
                'from_date': timestamp,
            },
        )
        return response.json()
    except requests.RequestException as error:
        logger.error(error)
        raise requests.RequestException
    finally:
        if response.status_code != HTTPStatus.OK:
            logger.error(f'Response status code is: {response.status_code}')
            raise Exception


def check_response(response):
    """Puta mierda."""
    if not isinstance(response, dict):
        logger.error('Wrong object type.')
        raise TypeError
    if ('homeworks' or 'current_date') not in response:
        logger.error('Blah-blah-blah.')
        raise KeyError
    if not isinstance(response['homeworks'], list):
        logger.error('Wrong object type.')
        raise TypeError
    if not response['current_date']:
        logger.error('Blah-blah-blah.')
        raise KeyError


def parse_status(homework):
    """Puta mierda."""
    try:
        homework_name = homework['homework_name']
        status = homework['status']
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except 'homework_name' or 'status' not in homework.keys():
        logger.error('Тьфу')
        raise KeyError


def main():
    """Puta mierda."""
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
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(message)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
