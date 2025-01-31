from telethon import TelegramClient
import asyncio
import json
import os

# задание API данных
api_id = '28785388'
api_hash = 'd1e47c42d07f3a664e52134acb05408e'
phone_number = '89771078834'

# каналы для парсинга
channels = ['t.me/the_economist_tg', 't.me/w0rld_economy', 't.me/rublya']

# словарь для хранения данных
channel_data = {channel: [] for channel in channels}

# ограничение на количество постов, обрабатываемых парсером за один запрос
POSTS_LIMIT = 10000

# пауза между запросами в секундах
REQUEST_DELAY = 2

# фцнкция для получения постов из канала
async def parse_channel(client, channel_name):
    try:
        # получение объекта канала
        channel = await client.get_entity(channel_name)
        print(f"Парсинг канала: {channel_name}")

        # переменная для хранения ID последнего обработанного поста
        last_post_id = 0

        while True:
            # получение постов из каналов с ограничением по каличеству (POSTS_LIMIT)
            posts = await client.get_messages(channel, limit=POSTS_LIMIT, offset_id=last_post_id, min_id=0)

            # выход из цикла при обработке всех постов канала
            if not posts:
                print(f"Все посты канала {channel_name} обработаны.")
                break

            # обработка постов
            for message in posts:
                # сохранение даты и текста постов
                if message.text:  # пропускаем посты при отсутствии в них текста
                    channel_data[channel_name].append([message.date.isoformat(), message.text])
                last_post_id = message.id

            print(f"Обработано {len(posts)} постов. Последний ID: {last_post_id}")

            # устанавливаем паузу между запросами
            await asyncio.sleep(REQUEST_DELAY)

    except Exception as e:
        print(f"Ошибка при парсинге канала {channel_name}: {e}")

# основная функция
async def run_parser():
    # создание клиента
    client = TelegramClient('session_name', api_id, api_hash)
    await client.start(phone=phone_number)

    try:
        # парсинг каждого канала
        for channel in channels:
            await parse_channel(client, channel)

    finally:
        # закрытие клиента
        await client.disconnect()

        # удаление файла сессии
        if os.path.exists('session_name.session'):
            os.remove('session_name.session')
            print("Файл сессии удален.")

        # сохранение данных в JSON-файл
        with open('channel_data.json', 'w', encoding='utf-8') as f:
            json.dump(channel_data, f, ensure_ascii=False, indent=4)
        print("Данные сохранены в channel_data.json.")