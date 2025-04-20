import re
from telethon import TelegramClient
from typing import Tuple
from flask import Flask, request
from flask_restful import Resource, Api
import asyncio
import json
import os
import pymorphy3

FIRST_SENTENCE_REGEX = r'^(.*?[.!?])'

banking_keywords = [
    "банк", "финанс", "кредит", "инвестиция", "актив", "курс",
    "процент", "ставка", "дебет", "кредитование", "капитал",
    "акция", "вклад", "прибыль", "убыток"
]

oil_gas_keywords = [
    "нефть", "газ", "добыча", "бурение", "транспортировка",
    "переработка", "качество", "нефтепровод", "газопровод",
    "объём", "инфраструктура", "технология", "энергия",
    "рынок", "цена"
]

morph = pymorphy3.MorphAnalyzer()
def determine_sphere(article_text):

    banking_count = 0
    oil_gas_count = 0

    # разделение текста на слова
    words = re.findall(r'\w+', article_text.lower())

    for word in words:
        # лемматизация слова
        lemma = morph.parse(word)[0].normal_form

        if lemma in banking_keywords:
            banking_count += 1
        elif lemma in oil_gas_keywords:
            oil_gas_count += 1

    # определение сферы
    if banking_count > oil_gas_count:
        return "Финансы"
    elif oil_gas_count > banking_count:
        return "Энергетика"
    elif oil_gas_count == banking_count and oil_gas_count > 0:
        return "Финансы/Энергетика"
    else:
        return None


app = Flask(__name__)
api = Api(app)
        

class TG_Parser(Resource):
    def __init__(self) -> None:
        self.api_id = 'получить можно на https://my.telegram.org/auth'
        self.api_hash = 'получить можно на https://my.telegram.org/auth'
        self.phone_number = 'номер от телеграм-аккаунта, используемого при парсинге'
        self.channels = ['https://t.me/+_LQxtUAfsjhlN2Qy', 't.me/economica', 't.me/w0rld_economy', 't.me/ecotopor']
        self.limit = '1'
        self.delay = 2
        self.parsed_data = []

# функция по обработке поста
    def process_message(self, message, channel_name):

        try:
            # пропуск поста при отсутствии в нём текста
            if not message.text:
                return None

            # извлечение первого предложения с помощью регулярного выражения
            match = re.match(FIRST_SENTENCE_REGEX, message.text.strip())
            title = match.group(1) if match else message.text.strip()

            # полный текст сообщения
            article_text = message.text.strip()

            # определение сферы сообщения
            sphere = self.determine_sphere(article_text)

            # если ключевые слова не найдены, пропускаем сообщение
            if sphere is None:
                return None

            # определение даты и времени сообщения
            datetime = message.date.strftime("%Y-%m-%dT%H:%M")

            # определение названия канала как источник
            source = channel_name

            # сохранение данных о посте в виде словаря
            return {
                "title": title,
                "datetime": datetime,
                "article_text": article_text,
                "sphere": sphere,
                "source": source,
            }
        except Exception as e:
            print(f"Ошибка обработки сообщения: {e}")
            return None


    # функция для парсинга одного канала
    async def parse_channel(self, client, channel_name):

        try:
            # получение объекта канала
            channel = await client.get_entity(channel_name)
            print(f"Парсинг канала: {channel_name}")

            # переменная для хранения ID последнего обработанного поста
            last_post_id = 0

            while True:
                # получение постов из канала с ограничением по количеству (POSTS_LIMIT)
                posts = await client.get_messages(channel, limit=self.limit, offset_id=last_post_id, min_id=0)

                # выход из цикла при обработке всех постов канала
                if not posts:
                    print(f"Все сообщения из канала {channel_name} обработаны.")
                    break

                # обработка постов
                for message in posts:
                    # преобразование поста в словарь
                    processed_message = self.process_message(message, channel.title)
                    if processed_message:
                        self.parsed_data.append(processed_message)

                    # обновляем ID последнего обработанного сообщения
                    last_post_id = message.id

                print(f"Обработано {len(posts)} сообщений. Последний ID: {last_post_id}")

                # пауза между запросами
                await asyncio.sleep(self.delay)

        except Exception as e:
            print(f"Ошибка при парсинге канала {channel_name}: {e}")


    # основная функция
    async def run_parser(self):

        # создание клиента
        client = TelegramClient(
            'session_name',
            self.api_id,
            self.api_hash,
            system_version="4.16.30-vxCUSTOM",
            device_model="CustomDevice",
            app_version="1.0"
        )
        await client.start(phone=self.phone_number)

        try:
            # парсинг каждого канала
            for channel in self.channels:
                await self.parse_channel(client, channel)

        finally:
            # закрытие клиента
            await client.disconnect()

            # удаление файла сессии
            if os.path.exists('session_name.session'):
                os.remove('session_name.session')
                print("Файл сессии удален.")

            # сохранение данных в JSON-файл
            with open('parsed_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.parsed_data, f, ensure_ascii=False, indent=4)
            print("Данные сохранены в parsed_data.json.")
    
    def get(self) -> dict:
        return {"limit":"put limit of msgs which u want to scribe from each channel"}
    
    def post(self) -> Tuple[dict, int]:
        data = request.get_json()
        try:
            user_limit = int(data["limit"])
        except Exception as e:
            return {"error": "put int value"}, 400
        self.limit = user_limit

        asyncio.run(self.run_parser())

        return self.parsed_data, 200

api.add_resource('/service.internal/tg_parser', TG_Parser)

if __name__ == '__main__':
    app.run(port=8001, debug=True)