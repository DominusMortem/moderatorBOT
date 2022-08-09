import asyncio
import random
import sqlite3
from contextlib import suppress
import logging
import re
import time
import datetime

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from telethon import TelegramClient, events
from aiogram import Bot, Dispatcher, executor, types
import aiogram.utils.markdown as fmt
from aiogram.utils import exceptions
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import (MessageCantBeDeleted, MessageToDeleteNotFound, RetryAfter, MessageCantBeEdited)
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import config
from database import Database
import utils
from permissions import is_admin, is_moder, is_owner, is_big_owner
from query import session, FlameNet, Main, Groups, Lottery, Banned, RPContext, Killer, VIP, Constants, Setting

range_tab = {'Очень злой': range(-500, -300),
             'Злой': range(-300, -100),
             'Нейтральный': range(-100, 100),
             'Добрый': range(100, 300),
             'Очень добрый': range(300, 501)}
exp_tab = {
    0: ('Преступник', 'Обитатель', 'Хранитель'),
    200: ('Вне закона', 'Отступник', 'Мученик'),
    550: ('Оппортунист', 'Искатель', 'Страж'),
    1050: ('Грабитель', 'Странник', 'Защитник'),
    1700: ('Толстый Кот', 'Гражданин', 'Почетный'),
    2500: ('Мародер', 'Авантюрист', 'Миротворец'),
    3450: ('Пират', 'Бродяга', 'Рейнджер'),
    4550: ('Разбойник', 'Наемник', 'Защитник'),
    5800: ('Захватчик', 'Городской рейнджер', 'Мститель'),
    7200: ('Бездельник', 'Наблюдатель', 'Образцовый'),
    8750: ('Криминальный Лорд', 'Советник', 'Крестоносец'),
    10450: ('Осквернитель', 'Хранитель', 'Паладин'),
    12300: ('Бугимен', 'Потомок', 'Легендарный'),
    14300: ('Похититель душ', 'Стяжатель душ', 'Светоносный'),
    16450: ('Смертный Дьявол', 'Истинный', 'Мессия')
}

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()

db = Database('database.db')
bot = Bot(token=config.TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)


api_id = 15820816
api_hash = '3a9cf35550d971b31234d1c395a51b15'

client = TelegramClient('session_name', api_id, api_hash)

TIMECHECK = {'м': 60,
             'm': 60,
             'h': 3600,
             'ч': 3600}


box = ['🎸гитара',
       '🎂торт',
       '🔪нож',
       '💰кот в мешке',
       '🛳️Яхта',
       '🛩️Самолет',
       '🧳Чемодан',
       '🔮Магический шар',
       '🎳Набор для боулинга',
       '🎃Тыква на Хеллуин',
       '💴Пачка денег',
       '🧯Огнетушитель',
       '💍Кольцо',
       '🪒Бритва',
       '🧹Метла',
       '🚗Автомобиль',
       '🚁Вертолет']

short_commands = ['обнять', 'казнить', 'побить', 'любовь', 'недоверие', 'тусить', 'поцеловать', 'танец', 'ругать',
                  'цветы', 'сплетни', 'взятка', 'заказать']
killer = ['не справился с управлением и улетел с крутого обрыва.',
          'умер во сне от сердечной недостаточности',
          'попал под поезд на станции',
          'умер от суточного прослушивания Бузовой',
          'сбит машиной на переходе',
          'погиб в результате массового ДТП с участием бензовоза и лесовоза',
          'мистер Cальери передаёт Вам привет...',
          'выпал с фуникулера',
          'отравился газировкой',
          'сожгли на костре инквизиции',
          'уснул в клетке с тигром']


class Tagall(StatesGroup):
    func = State()
    group = State()
    rp = State()
    prefix = State()


@client.on(events.NewMessage(chats=[1202181831, 1629215553, 1781348153, 1101450717]))
async def normal_handler(event):
    message = event.message.to_dict()
    me = await client.get_me()
    chat_id = f"-100{message['peer_id']['channel_id']}"
    if me.username in message['message']:
        return
        #await client.send_message(message['peer_id']['channel_id'], '**Автоответчик**:\n```Абонент вне зоны доступа```', parse_mode='Markdown')
    if message['from_id']['user_id']:
        group = utils.get_group(chat_id)
        if message['entities'] and 'Игра окончена' in message['message'] and message['fwd_from'] is None:
            group.silent_mode = 0
            group.revo = 0
            session.commit()
            if 'Остальные участники:' in message['message']:
                text = message['message'].partition('Остальные участники:')[0]
                winners = list([x for _, x in re.findall(r'(\s{4}(.*?)\s-)', text)])
            elif 'Другие пользователи:' in message['message']:
                text = message['message'].partition('Другие пользователи:')[0]
                winners = list([x for _, x in re.findall(r'(\d.\s(.*?)\s-)', text)])
            else:
                text = message['message'].partition('Другие:')[0]
                winners = list([x for _, x in re.findall(r'(\d.\s.(.*?)\s-)', text)])
            entities = [entity for entity in message['entities'] if entity['_'] == 'MessageEntityMentionName']
            await work_group(winners, entities, chat_id)
        if message['entities']:
            if 'спать во время' in message['message']:
                for entity in message['entities']:
                    if entity['_'] == 'MessageEntityMentionName' and utils.user_exists(chat_id, entity['user_id']):
                        user = utils.get_user(chat_id, entity['user_id'])
                        await add_mute(chat_id, user.first_name, entity['user_id'], '30m', 'АФК')
                        await info_message(
                            'АвтоАФК от бота',
                            group.title,
                            chat_id,
                            dict(await bot.get_me()).get('first_name'),
                            dict(await bot.get_me()).get('id'),
                            user.first_name,
                            entity['user_id'],
                            dict(await bot.get_me()).get('username'),
                            None
                        )
            if 'не выдержал гнетущей атмосферы' in message['message']:
                if group.pair_game:
                    return
                for entity in message['entities']:
                    if entity['_'] == 'MessageEntityMentionName' and utils.user_exists(chat_id, entity['user_id']):
                        user = utils.get_user(chat_id, entity['user_id'])
                        await add_mute(chat_id, user.first_name, entity['user_id'], '30m', 'Вышел из игры')
                        await info_message(
                            'Автолив от бота',
                            group.title,
                            chat_id,
                            dict(await bot.get_me()).get('first_name'),
                            dict(await bot.get_me()).get('id'),
                            user.first_name,
                            entity['user_id'],
                            dict(await bot.get_me()).get('username'),
                            None
                        )
        if 'Наступает ночь' in message['message'] and not group.silent_mode:
            group.silent_mode = 1
            session.commit()
            await bot.send_message(chat_id, 'Включен режим тишины, команды бота недоступны для пользователей без прав!')
client.start()


async def try_delete(message):
    try:
        await message.delete()
        return
    except (MessageToDeleteNotFound, MessageCantBeDeleted):
        pass
    return


@dp.message_handler(lambda m: m.text.lower() == 'заказать')  # действия
async def short_command(message: types.Message):
    if message.chat.type == 'private':
        await try_delete(message)
        return
    if utils.salent(message.chat.id):
        await try_delete(message)
        return
    if not message.reply_to_message:
        await message.reply('Эта команда должна быть ответом на сообщение!')
        return
    person_one = await mention_text(message.from_user.first_name, message.from_user.id)
    person_two = await mention_text(message.reply_to_message.from_user.first_name,
                                    message.reply_to_message.from_user.id)
    await message.answer(f'{fmt.hlink(*person_one)} заказал {fmt.hlink(*person_two)}')
    await asyncio.sleep(1)
    await message.answer(f'{fmt.hlink(*person_two)} {random.choice(killer)}')
    await asyncio.sleep(1)
    await message.answer(f'{fmt.hlink(*person_one)} заказ выполнен!')
    return


@dp.message_handler(commands='revo')
async def revo(message: types.Message):
    await try_delete(message)
    if utils.roulette_exist(message.chat.id):
        return
    if utils.salent(message.chat.id):
        await try_delete(message)
        return
    user_one_id = utils.get_user(message.chat.id, message.from_user.id)
    user_two_id = utils.get_user(message.chat.id, message.reply_to_message.from_user.id)
    mention = await mention_text(user_one_id.first_name, user_one_id.user_id)
    mention_two = await mention_text(user_two_id.first_name, user_two_id.user_id)
    button = [
        types.InlineKeyboardButton('Принять', callback_data=f'game_start_{user_two_id.user_id}_{user_one_id.user_id}'),
        types.InlineKeyboardButton('Отказ', callback_data=f'game_cancel_{user_two_id.user_id}')
    ]
    keyboard = types.InlineKeyboardMarkup().add(*button)
    if user_one_id.cash < 2:
        await message.answer(f'{fmt.hlink(*mention)}, ваших средств не достаточно!')
        return
    if user_one_id.cash < 2:
        await message.answer(f'У {fmt.hlink(*mention_two)} средств не достаточно!')
        return
    msg = await message.answer(f'{fmt.hlink(*mention)} бросил вызов в русскую рулетку {fmt.hlink(*mention_two)}.\nСтавка в игре 2 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮', reply_markup=keyboard)
    await asyncio.create_task(delete_message(msg, 15))


@dp.callback_query_handler(lambda c: 'game' in c.data)
async def pvp(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    revo = utils.get_group(callback_query.message.chat.id)
    command = callback_query.data.split('_')
    if int(command[2]) == callback_query.from_user.id:
        await callback_query.answer()
        if command[1] == 'cancel':
            await asyncio.sleep(2)
            await callback_query.message.answer('Игрок отказался от дуэли')
            revo.revo = 0
            session.commit()
            await try_delete(callback_query.message)
            return
        user_one_id = utils.get_user(callback_query.message.chat.id, command[2])
        user_two_id = utils.get_user(callback_query.message.chat.id, command[3])
        mention = await mention_text(user_one_id.first_name, user_one_id.user_id)
        mention_two = await mention_text(user_two_id.first_name, user_two_id.user_id)
        step = random.choice([0, 0, 0, 1])
        button = [types.InlineKeyboardButton(
            'Стрелять',
            callback_data=f'game_{step}_{user_two_id.user_id}_{user_one_id.user_id}'
        ),
            types.InlineKeyboardButton('Отказ', callback_data=f'game_cancel_{user_two_id.user_id}')
        ]
        keyboard = types.InlineKeyboardMarkup().add(*button)
        if command[1] == 'start':
            revo.revo = 1
            session.commit()
            await callback_query.message.answer(f'{fmt.hlink(*mention)} принял вызов.\n'
                                                f'Первый ход за {fmt.hlink(*mention_two)}\n'
                                                f'Стреляй', reply_markup=keyboard)
        if command[1] == '0':
            await callback_query.message.answer(f'{fmt.hlink(*mention)}, вы слышите щелчок, пуля не выстрелила. Судьба на вашей стороне.\n'
                                                f'Ход за {fmt.hlink(*mention_two)}\n'
                                                f'Стреляй', reply_markup=keyboard)
        if command[1] == '1':
            revo.revo = 0
            user_one_id.cash -= 2
            user_two_id.cash += 2
            session.commit()
            await callback_query.message.answer(f'{fmt.hlink(*mention)} нажимает на спусковой крючок. Раздается выстрел.\n'
                                                      f'Победил {fmt.hlink(*mention_two)}\n\n'
                                                      f'{fmt.hlink(*mention_two)} забирает 2 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮 у {fmt.hlink(*mention)}')


@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    await try_delete(message)
    if not any([
        is_big_owner(message.from_user.id),
        is_owner(message.from_user.id),
        is_admin(message.chat.id, message.from_user.id),
        is_moder(message.chat.id, message.from_user.id)
    ]):
        text = ('Команды доступные пользователям.\n\n'
                '<code>/info</code> - выводит информацию о пользователе.\n'
                '<code>/rp</code> - список RP команд в чате. Команды вводятся в ответ на сообщение.\n'
                '<code>/свадьба (никнейм)</code> - предложение свадьбы, можно использовать в ответ на сообщение.\n'
                '<code>/развод (никнейм)</code> - развестись, можно использовать в ответ на сообщение.\n'
                '<code>/браки</code> - список всех пар в чате.\n'
                '<code>/карма</code> - проверить свою карму.\n'
                '<code>/gift (сумма)</code> - пожертвовать сумму другому пользователю.\n'
                '<code>/money</code> - проверить баланс.\n')
    else:
        text = (f'Помощь по командам доступным для администрации.\n'
                f'Большинство команд можно использовать в ответ на сообщение пользователя.\n'
                f'<code>/info (никнейм) </code> - выводит информацию о пользователе.\n\n'
                f'<code>/карма (никнейм)</code> - проверить карму пользователя.\n'
                f'<code>/ban (никнейм) (1/0)</code> - параметр 1 выдает бан пользователю, 0 - снимает.\n'
                f'<code>/menu (никнейм) </code> - меню действий с пользователем.\n'
                f'<code>/set_admin (никнейм) (1/0)</code> - параметр 1 выдает админа пользователю, 0 - снимает.\n'
                f'<code>/set_moder (никнейм) (1/0)</code> - параметр 1 выдает модера пользователю, 0 - снимает.\n'
                f'<code>/add_money (никнейм) (кол-во)</code> - добавляет установленное количество валюты.\n'
                f'<code>/mute (никнейм) (время) (причина) </code> - дает мут пользователю на указаное кол-во времени\n'
                f'<code>/unmute (никнейм)</code> - снимает мут\n'
                f'<code>/talk (сообщение)</code> - написать от имени бота\n'
                f'<code>/black (id)</code> - добавить в черный список сети\n'
                f'<code>/white (id)</code> - удалить из черного списка сети\n'
                f'<code>/выгрузить</code> - общая статистика по пользователям сети\n'
                f'<code>/stats</code> - статистика в конкретной группе\n'
                f'<code>/news</code> - обновления в боте.\n'
                f'<code>/преф</code> - список пользователей с префиксами, учитывая администраторов.\n'
                f'<code>/pair (on/off)</code> on - включение режима парных игр, off - для отключения.\n'
                f'<code>/prefix (никнейм) (причина)</code> - удаление префикса по причине.\n'
                f'<code>/admins</code> - список администрации.\n')
    await message.answer(text)


@dp.message_handler(commands=['bot'])
async def bot_on(message: types.Message):
    await try_delete(message)
    text = message.text.split()
    if is_big_owner(message.from_user.id):
        return
    group = session.query(Groups).filter(Groups.group_id == message.chat.id).one_or_none()
    if text[1] == 'on':
        group.setka = 1
        session.commit()
        await message.answer('Бот включен')
    else:
        group.setka = 0
        session.commit()
        await message.answer('Бот выключен')


@dp.message_handler(commands=['silent'])
async def silent(message: types.Message):
    await try_delete(message)
    group = session.query(Groups).filter(Groups.group_id == message.chat.id).one_or_none()
    group.silent_mode = 0
    session.commit()
    await message.answer('Тихий режим выключен!')


@dp.message_handler(commands='extermination')
async def extermination(message: types.Message):
    await try_delete(message)
    if not is_big_owner(message.from_user.id):
        return
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton('Да', callback_data=f'ext_{message.from_user.id}'),
               types.InlineKeyboardButton('Нет', callback_data='ext_cancel')]
    keyboard.add(*buttons)
    await message.answer('Вы действительно хотите забанить всех в группе?', reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('ext_'))
async def exterm(callback_query: types.CallbackQuery):
    data = callback_query.data.split('_')
    if data[1] == 'cancel':
        await callback_query.message.delete()
    if int(data[1]) == callback_query.from_user.id:
        users = utils.get_users(callback_query.message.chat.id)
        for user in users:
            if user.user_id == callback_query.from_user.id:
                continue
            else:
                try:
                    await bot.ban_chat_member(callback_query.message.chat.id, user.user_id)
                except:
                    continue
        await callback_query.answer('Вы забанили всех в группе!!!', show_alert=True)
        await callback_query.message.delete()


@dp.message_handler(commands=['print'])
async def prints(message: types.Message):
    await try_delete(message)
    all = await client.get_participants(message.chat.id, limit=5000)
    count = 0
    noexist = []
    desactive = 0
    for person in all:
        if not utils.user_exists(message.chat.id, person.id):
            count += 1
            db.add_user(message.chat.id, person.id, person.username, person.first_name, 1)
        noexist.append(person.id)
    for person in utils.get_users(message.chat.id):
        if person.user_id not in noexist:
            person.is_active = 0
            desactive += 1
        else:
            person.is_active = 1
    session.commit()
    await message.answer(f'Добавлено {count} пользователей\n Неактивных пользователей {desactive}')


@dp.message_handler(commands=['check'])
async def check(message: types.Message):
    await try_delete(message)
    text = message.text.split()
    if len(text) == 2:
        user_id = text[1]
        data = utils.get_user(message.chat.id, user_id)
        if data:
            mes = (f'Информация о пользователе:\n'
                   f'ID: {data.user_id}\n'
                   f'Name: {data.username}')
        else:
            mes = f'Пользователя нет в базе.'
        await message.answer(mes)


@dp.message_handler(commands=['add'])
async def add(message: types.Message):
    await try_delete(message)
    user_id = message.reply_to_message.from_user.id
    username = message.reply_to_message.from_user.username
    first_name = message.reply_to_message.from_user.first_name
    if utils.user_exists(message.chat.id, user_id):
        return
    user = FlameNet(
        chat_id=message.chat.id,
        user_id=user_id,
        username=username,
        first_name=first_name,
        is_active=1,
        create_time=datetime.date.today(),
        first_message=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    session.add(user)
    session.commit()
    await message.answer('Пользователь добавлен!')


@dp.message_handler(lambda message: message.chat.type in ['supergroup', 'group', 'channel'] and not utils.setka(message.chat.id))
async def no_work(message: types.Message):
    return


@dp.message_handler(commands=['выгрузить'])
async def all_stats(message: types.Message):
    await try_delete(message)
    text = 'Статистика сети по пользователям:\n\n'
    count = 0
    count_act = 0
    for group in utils.get_groups():
        if group.setka:
            users = utils.get_users(group.group_id)
            active = [user for user in users if user.is_active]
            count += len(users)
            count_act += len(active)
            text += (f'{group.title:}\n'
                     f'Всего пользователей в базе: {len(users)}\n'
                     f'Активно пользователей: {len(active)}\n'
                     f'Неактивно (вышли с группы): {len(users) - len(active)}\n\n')
    text += (f'Всего пользователей сети в базе: {count}\n'
            f'Активно: {count_act}')
    await message.answer(text)


@dp.message_handler(commands=['розыгрыш'])
async def lottery(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    if utils.salent(message.chat.id):
        await try_delete(message)
        return
    users = [user.user_id for user in utils.get_lottery(message.chat.id)]
    users.append(config.ADMIN_ID)
    if message.from_user.id not in users:
        return
    text = message.text.split()
    if len(text) >= 2:
        user_id, username, first_name = await ent(message)
        user = Lottery(
            user_id=user_id,
            first_name=first_name,
            chat_id=message.chat.id
        )
        session.add(user)
        session.commit()
        await message.answer(fmt.text(fmt.hlink(*await mention_text(first_name, user_id)), ' добавлен распорядителем розыгрыша.'))
        return
    try:
        group = utils.get_group(message.chat.id)
        if group.serial_killer:
            await message.answer('Уже активировано!')
        else:
            dates = datetime.datetime.now() + datetime.timedelta(minutes=10)
            group.time_serial=dates.strftime('%Y-%m-%d %H:%M:%S')
            group.serial_killer = 1
            group.lottery = 1
            session.commit()
            await message.answer('Начинается быстрый розыгрыш 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮. Скоро будет выбран победитель среди активных участников.')
    except Exception as e:
        logging.info(e)


@dp.message_handler(commands=['курьер'])
async def cur(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    if utils.salent(message.chat.id):
        await try_delete(message)
        return
    text = message.text.split()
    try:
        group = utils.get_group(message.chat.id)
        if group.serial_killer:
            time_serial = datetime.datetime.strptime(group.time_serial, '%Y-%m-%d %H:%M:%S')
            await message.answer(f'Курьер прибудет в {time_serial.strftime("%H:%M:%S")}')
        else:
            t = 1
            if len(text) == 2 and text[1].isdigit():
                t = int(text[1])
            dates = datetime.datetime.now() + datetime.timedelta(minutes=t)
            group.time_serial = dates.strftime('%Y-%m-%d %H:%M:%S')
            group.serial_killer = 1
            session.commit()
            await message.answer('Курьерская служба "Рандомные безделушки" начинает свою работу. Скоро курьер доставит посылку.')
    except Exception as e:
        logging.info(e)


@dp.message_handler(commands=['вещи'])
async def items(message: types.Message):
    await try_delete(message)
    user = utils.get_user(message.chat.id, message.from_user.id)
    mention = await mention_text(message.from_user.first_name, message.from_user.id)
    if user.items == '0':
        text = 'Курьер еще не приносил вам вещей!'
    else:
        text = fmt.text(fmt.hlink(*mention), ' - вот ваше имущество:\n')
        items = [x.split(':') for x in [item for item in user.items.split(',')]]
        items_to_dict = {x: int(y) for x, y in items}
        for k, v in items_to_dict.items():
            text += f'{k} - {v} шт.\n'
    await message.answer(text)


@dp.message_handler(commands=['link'])
async def cmd_test(message: types.Message):
    await try_delete(message)
    link = await bot.create_chat_invite_link(-1001781348153)
    await message.answer(link.invite_link)


@dp.message_handler(commands=['news'])
async def news(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    await message.answer('⚠Обновление бота на 13.07.22:\n'
                         'Добавлена функция быстрых розыгрышей. По команде /лотерея, владелец может запустить розыгрыш.'
                         'Для участия необходимо лишь быть активным в чате. Победители определяются по достижении'
                         ' 25 участников или 10 минут. Побеждают 5 человек, награда 3 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮')


@dp.message_handler(commands=['talk'])
async def talk(message: types.Message):
    await try_delete(message)
    if any([
        is_big_owner(message.from_user.id),
        is_owner(message.from_user.id),
        is_admin(message.chat.id, message.from_user.id),
    ]):
        await message.answer(message.text[5:])


@dp.message_handler(commands=['black'])
async def black(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    text = message.text.split()
    if not any([
        is_big_owner(message.from_user.id),
        is_owner(message.from_user.id),
        is_admin(message.chat.id, message.from_user.id),
        is_moder(message.chat.id, message.from_user.id)
    ]):
        await message.answer('Недостаточно прав')
        return
    if is_owner(text[1]):
        await message.answer('Нельзя банить совладельцев!')
        return
    try:
        if session.query(Banned).filter(Banned.user_id == text[1]).one_or_none():
            await message.answer('Пользователь уже в черном списке!')
            return
        mention = await mention_text('Username', text[1])
        await banned(text[1], 0, mention)
        await message.answer(f'ID {text[1]} добавлен в черный список сети!')
        await info_message(
            'black',
            message.chat.title,
            message.chat.id,
            message.from_user.first_name,
            message.from_user.id,
            None,
            text[1],
            message.from_user.username,
            None
        )
    except Exception as e:
        logging.info(e)


@dp.message_handler(commands=['white'])
async def white(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    text = message.text.split()
    if not any([
        is_big_owner(message.from_user.id),
        is_owner(message.from_user.id),
        is_admin(message.chat.id, message.from_user.id),
        is_moder(message.chat.id, message.from_user.id)
    ]):
        await message.answer('Недостаточно прав')
        return
    try:

        mention = await mention_text('Username', text[1])
        await unbanned(text[1], 0, mention)
        await message.answer(f'ID {text[1]} убран из черного списка сети!')
        await info_message(
            'white',
            message.chat.title,
            message.chat.id,
            message.from_user.first_name,
            message.from_user.id,
            None,
            text[1],
            message.from_user.username,
            None
        )
    except Exception as e:
        logging.info(e)


@dp.message_handler(commands=['menu'])
async def menu(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    big_owner = is_big_owner(message.from_user.id)
    owner = is_owner(message.from_user.id)
    admin = is_admin(message.chat.id, message.from_user.id)
    moder = is_moder(message.chat.id, message.from_user.id)
    try:
        if not any([
            big_owner,
            owner,
            admin,
            moder
        ]):
            await message.answer('Недостаточно прав')
            return
        if len(message.text.split()) == 1:
            if not message.reply_to_message:
                await message.reply('Эта команда должна быть ответом на сообщение!')
                return
            user_id = message.reply_to_message.from_user.id
            username = message.reply_to_message.from_user.username
            first_name = message.reply_to_message.from_user.first_name
        else:
            user_id, username, first_name = await ent(message)
        keyboard = types.InlineKeyboardMarkup()
        buttons = []
        owner_user = is_owner(user_id)
        admin_user = is_admin(message.chat.id, user_id)
        moder_user = is_moder(message.chat.id, user_id)
        if user_id == config.ADMIN_ID:
            await message.answer('Нельзя изменять права владельца!')
            return
        if any([admin, moder]) and owner_user:
            await message.answer('Недостаточно прав')
            return
        if moder and any([owner_user, admin_user, moder_user]):
            await message.answer('Недостаточно прав')
            return
        adm = 'Нет данных'
        if owner:
            adm = fmt.text(f'Совладелец {message.from_user.first_name}')
        if admin:
            adm = fmt.text(f'Админ {message.from_user.first_name}')
        if moder:
            adm = fmt.text(f'Модер {message.from_user.first_name}')
        if big_owner:
            adm = fmt.text(f'Владелец {message.from_user.first_name}')
            buttons.append(types.InlineKeyboardButton('Совладелец',
                                                      callback_data=f'menu_owner_{user_id}_{message.from_user.id}'))
        if any([big_owner, owner]):
            buttons.append(types.InlineKeyboardButton('Администратор',
                                                      callback_data=f'menu_admin_{user_id}_{message.from_user.id}'))
            buttons.append(types.InlineKeyboardButton('Разбан по сети',
                                                      callback_data=f'menu_unbanned_{user_id}_{message.from_user.id}'))
        if any([big_owner, owner, admin]):
            buttons.append(types.InlineKeyboardButton('Бан по сети',
                                                      callback_data=f'menu_banned_{user_id}_{message.from_user.id}'))
            buttons.append(types.InlineKeyboardButton('Модератор',
                                                      callback_data=f'menu_moder_{user_id}_{message.from_user.id}'))
            buttons.append(types.InlineKeyboardButton('Понизить',
                                                      callback_data=f'menu_down_{user_id}_{message.from_user.id}'))
        if any([big_owner, owner, admin, moder]):
            buttons.append(types.InlineKeyboardButton('Забанить',
                                                      callback_data=f'menu_ban_{user_id}_{message.from_user.id}'))
            buttons.append(types.InlineKeyboardButton('Разбанить',
                                                      callback_data=f'menu_unban_{user_id}_{message.from_user.id}'))
            buttons.append(types.InlineKeyboardButton('RP команды',
                                                      callback_data=f'menu_userrp_{user_id}_{message.from_user.id}'))
            buttons.append(types.InlineKeyboardButton('Закрыть',
                                                      callback_data=f'menu_close_{user_id}_{message.from_user.id}'))

        keyboard.add(*buttons)
        msg = await message.answer(fmt.text(
            f'Данные о человеке: \n'
            f'Команду вызвал - {adm}\n'
            f'ID - {user_id}\n'
            f'Username - {username}\n'
            f'First Name - {first_name}'), reply_markup=keyboard)
        asyncio.create_task(delete_message(msg, 20))
    except Exception as e:
        logging.info(e)


@dp.callback_query_handler(lambda c: c.data.startswith('menu_'))
async def ban_key(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    _, com, to_user, from_user = callback_query.data.split('_')
    user = utils.get_user(callback_query.message.chat.id, to_user)
    mention = await mention_text(user.first_name, to_user)
    if callback_query.from_user.id == int(from_user):
        if com == 'close':
            await callback_query.message.delete()
            return
        await DICT_COMMANDS[com](to_user, callback_query.message.chat.id, mention, callback_query.from_user.id)


async def user_rp(user_id, chat_id, mention, user=0):
    coms = utils.get_user_rp(user_id=user_id)
    buttons = []
    for com in coms:
        buttons.append(types.InlineKeyboardButton(f'{com.id} -{com.com} - {com.desc}', callback_data=f'deladm_{com.id}_{user}_{user_id}'))
    keyboard = types.InlineKeyboardMarkup(row_width=1).add(*buttons)
    keyboard.add(types.InlineKeyboardButton(f'Закрыть', callback_data=f'deladm_close_{user}_{user_id}'))
    msg = await bot.send_message(chat_id, 'Выберите команду', reply_markup=keyboard)
    asyncio.create_task(delete_message(msg,20))


@dp.callback_query_handler(lambda c: 'deladm_' in c.data)
async def call_user_rp(callback_query: types.CallbackQuery):
    _, rp_id, from_user, to_user = callback_query.data.split('_')
    if callback_query.from_user.id == int(from_user):
        if rp_id == 'close':
            await callback_query.message.delete()
            return
        session.query(RPContext).filter(RPContext.id == rp_id).delete()
        session.commit()
        await callback_query.message.delete()
        await user_rp(to_user, callback_query.message.chat.id, None, from_user)
    await callback_query.answer()



async def downgrade(user_id, chat_id, mention, user=0):
    owner = is_owner(user_id)
    admin = is_admin(chat_id, user_id)
    moder = is_moder(chat_id, user_id)
    if owner:
        for group in utils.get_groups():
            if utils.user_exists(group.group_id, user_id):
                await admin_up(user_id, group.group_id, mention)
        return 'Понижено!'
    elif admin:
        await moder_up(user_id, chat_id, mention)
        return 'Понижено!'
    elif moder:
        await moder_down(user_id, chat_id, mention)
        return 'Понижено!'
    else:
        return 'Недостаточно прав!'


async def admin_up(user_id, chat_id, mention, user=0):
    session.query(Main).filter(Main.owner_id == user_id).delete()
    user = session.query(FlameNet).filter(FlameNet.user_id == user_id, FlameNet.chat_id == chat_id).one_or_none()
    user.is_admin = 1
    user.is_moder = 0
    session.commit()
    await bot.promote_chat_member(
        chat_id,
        user_id,
        can_manage_chat=True,
        can_delete_messages=True,
        can_restrict_members=True
    )
    await asyncio.sleep(1)
    await bot.set_chat_administrator_custom_title(chat_id, user_id, custom_title='Администратор')
    await bot.send_message(chat_id, fmt.text('Пользователь ',fmt.hlink(*mention),' назначен администратором сообщества.'))


async def admin_down(user_id, chat_id, mention, user=0):
    session.query(Main).filter(Main.owner_id == user_id).delete()
    user = session.query(FlameNet).filter(FlameNet.user_id == user_id, FlameNet.chat_id == chat_id).one_or_none()
    user.is_admin = 0
    user.is_moder = 0
    session.commit()
    await bot.promote_chat_member(
        chat_id, user_id
    )
    await bot.send_message(chat_id, fmt.text('Пользователь ', fmt.hlink(*mention), ' снят с должности администратора.'))


async def moder_up(user_id, chat_id, mention, user=0):
    session.query(Main).filter(Main.owner_id == user_id).delete()
    user = session.query(FlameNet).filter(FlameNet.user_id == user_id, FlameNet.chat_id == chat_id).one_or_none()
    user.is_admin = 0
    user.is_moder = 1
    session.commit()
    await bot.promote_chat_member(
        chat_id,
        user_id,
        can_manage_chat=True
    )
    await asyncio.sleep(1)
    await bot.set_chat_administrator_custom_title(chat_id, user_id, custom_title='Модератор')
    await bot.send_message(chat_id, fmt.text('Пользователь ', fmt.hlink(*mention), 'назначен модератором сообщества.'))
    return 'Назначение успешно!'


async def moder_down(user_id, chat_id, mention, user=0):
    session.query(Main).filter(Main.owner_id == user_id).delete()
    user = session.query(FlameNet).filter(FlameNet.user_id == user_id, FlameNet.chat_id == chat_id).one_or_none()
    user.is_admin = 0
    user.is_moder = 0
    session.commit()
    await bot.promote_chat_member(
        chat_id, user_id
    )
    await bot.send_message(chat_id, fmt.text('Пользователь ', fmt.hlink(*mention),' снят с должности модератора.'))


async def unban_group(user_id, chat_id, mention, user=0):
    user = session.query(FlameNet).filter(FlameNet.user_id == user_id, FlameNet.chat_id == chat_id).one_or_none()
    user.ban = 0
    session.commit()
    await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
    await bot.send_message(chat_id, fmt.text('Пользователь ', fmt.hlink(*mention), ' разбанен.'))
    return 'Пользователь разбанен!'


async def ban_group(user_id, chat_id, mention, user=0):
    user = session.query(FlameNet).filter(FlameNet.user_id == user_id, FlameNet.chat_id == chat_id).one_or_none()
    user.ban = 1
    session.commit()
    await bot.ban_chat_member(chat_id, user_id)
    await bot.send_message(chat_id, fmt.text('Пользователь ', fmt.hlink(*mention), ' забанен.\nПричина: Систематические нарушения правил.'))
    return 'Пользователь забанен!'


async def add_owner(user_id, chat_id, mention, user=0):
    if not is_big_owner(user):
        return 'Недостаточно прав!'
    if not utils.owner_exists(user_id):
        user = Main(owner_id=user_id)
        session.add(user)
        session.commit()
    for group in utils.get_groups():
        if utils.user_exists(group.group_id, user_id):
            user = session.query(FlameNet).filter(FlameNet.user_id == user_id, FlameNet.chat_id == chat_id).one_or_none()
            user.is_admin = 0
            user.is_moder = 0
            session.commit()
            await bot.promote_chat_member(
                group.group_id,
                user_id,
                can_manage_chat=True,
                can_delete_messages=True,
                can_restrict_members=True,
                can_promote_members=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_manage_video_chats=True
            )
            await asyncio.sleep(1)
            await bot.set_chat_administrator_custom_title(group.group_id, user_id, custom_title='Совладелец')
            await bot.send_message(group.group_id, fmt.text('Пользователь ', fmt.hlink(*mention), ' назначен совладельцем сети!'))


async def banned(user_id, chat_id, mention, user=0):
    if not utils.banned_exists(user_id):
        baned = Banned(user_id=user_id, desc='Добавлен в черный список')
        session.add(baned)
        session.commit()
    try:
        for group in utils.get_groups():
            if utils.user_exists(group.group_id, user_id):
                if any([is_owner(user_id), is_admin(group.group_id, user_id), is_moder(group.group_id, user_id)]):
                    await bot.send_message(group.group_id, 'Нельзя забанить администраторов!')
                    return
                await bot.ban_chat_member(group.group_id, user_id)
                await bot.send_message(group.group_id,
                                       fmt.text('Пользователь ', fmt.hlink(*mention), ' забанен.\nПричина: Пользователь в черном списке сети.'))
    except Exception as e:
        print(e)


async def unbanned(user_id, chat_id, mention, user=0):
    session.query(Banned).filter(Banned.user_id == user_id).delete()
    session.commit()
    for group in utils.get_groups():
        if utils.user_exists(group.group_id, user_id):
            await bot.unban_chat_member(group.group_id, user_id)
            await bot.send_message(group.group_id,
                                   fmt.text('Пользователь ', fmt.hlink(*mention), ' разбанен.\n'))


@dp.message_handler(commands=['преф'])
async def pref(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    if not any([
        is_big_owner(message.from_user.id),
        is_owner(message.from_user.id),
        is_admin(message.chat.id, message.from_user.id),
        is_moder(message.chat.id, message.from_user.id)
    ]):
        return
    msg = await bot.get_chat_administrators(message.chat.id)
    await message.answer(f'Количество пользователей с префиксом: {len(msg)}\n Максимальное количество - 50')
    text = ''
    for user in msg:
        mention = await mention_text(user.user.first_name, user.user.id)
        text += fmt.text(fmt.hlink(*mention), ' - ', user.custom_title, '\n')
    msg = await message.answer(text)
    asyncio.create_task(delete_message(msg, 5))


@dp.message_handler(lambda m: m.text.lower() in [i.com.lower() for i in utils.get_rp()])
async def command(message: types.Message):
    if message.chat.type == 'private':
        return
    if utils.salent(message.chat.id):
        await try_delete(message)
        return
    if not message.reply_to_message:
        return
    mention = await mention_text(message.from_user.first_name, message.from_user.id)
    if utils.get_vip(message.from_user.id):
        await message.answer(fmt.text(fmt.hlink(*mention), 'Время действия VIP истек!'))
        return
    person_one = await mention_text(message.from_user.first_name, message.from_user.id)
    person_two = await mention_text(message.reply_to_message.from_user.first_name,
                                      message.reply_to_message.from_user.id)
    if utils.check_rp(com=message.text.lower(), user_id=message.from_user.id):
        rp = utils.get_com_rp(message.text.lower(), message.from_user.id)
        if not rp:
            return
    else:
        rp = utils.get_com_rp(message.text.lower(), 0)
        if not rp:
            return
    pref = ''
    if rp.prefix:
        pref = f'{rp.prefix}'
    postfix = ''
    if rp.until_date != '0':
        postfix = rp.until_date
    com = rp.desc
    text = fmt.text(pref, fmt.hlink(*person_one), com, fmt.hlink(*person_two), postfix)
    await message.answer(text)


@dp.message_handler(commands=['RP'])
async def rp_all(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    if utils.get_group(message.chat.id).silent_mode:
        return
    text = 'Доступные RP команды:\n\n'
    count = 0
    for rp in utils.get_rp():
        if rp.user_id == 0:
            text += (f'<code>{rp.com}</code> ')
            count += 1
            if count == 3:
                count = 0
                text += '\n'
    if text[-1] != '\n':
        text += '\n'
    text += '<code>заказать</code>\nКоманда пишется в ответ на сообщение пользователя.'
    msg = await message.answer(text)
    asyncio.create_task(delete_message(msg, 10))


@dp.message_handler(commands=['pair'])
async def pair_game(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    mes = message.text.split()
    if not any([
        is_big_owner(message.from_user.id),
        is_owner(message.from_user.id),
        is_admin(message.chat.id, message.from_user.id),
        is_moder(message.chat.id, message.from_user.id)
    ]):
        return
    group = utils.get_group(message.chat.id)
    if len(mes) == 2 and mes[1] == 'on':
        group.pair_game = 1
        session.commit()
        text = 'Включен режим парных игр. Автонаказание за лив отключено. Наказание за лив при нарушении правил в ручном режиме.'
    else:
        group.pair_game = 0
        session.commit()
        text = 'Режим парных игр отключен. Автонаказание за лив включено. Приятной игры.'
    msg = await message.answer(text)
    asyncio.create_task(delete_message(msg, 10))
    await info_message(
        'парные игры',
        message.chat.title,
        message.chat.id,
        message.from_user.first_name,
        message.from_user.id,
        message.from_user.first_name,
        message.from_user.id,
        message.from_user.username,
        message.from_user.username
    )
    try:
        await message.delete()
    except (MessageToDeleteNotFound, MessageCantBeDeleted):
        pass


async def work_group(winners, entities, chat_id):
    if winners:
        text_winners = 'Поздравляем победителей!\n'
        count = 1
        setting = utils.get_setting()
        money = setting.money_for_game
        for entity in entities[:len(winners)]:
            if utils.user_exists(chat_id, entity['user_id']):
                user = utils.get_user(chat_id, entity['user_id'])
                user.cash += money
                session.commit()
                mention = await mention_text(user.first_name, entity['user_id'])
                text_winners += fmt.text(count, ') ', fmt.hlink(*mention), ' - ', money, ' 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n')
                count += 1
                group = utils.get_group(chat_id)
                await info_message(
                    'Автоначисление от бота',
                    group.title,
                    chat_id,
                    dict(await bot.get_me()).get('first_name'),
                    dict(await bot.get_me()).get('id'),
                    user.first_name,
                    entity['user_id'],
                    dict(await bot.get_me()).get('username'),
                    None
                )
        await bot.send_message(chat_id, text_winners)
        await bot.send_message(chat_id, 'Выключен режим тишины, команды бота доступны!')


async def delete_message(message: types.Message, sleep_time: int = 0):
    await asyncio.sleep(sleep_time)
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await message.delete()


async def mention_text(first_name, user_id):
    return first_name, f'tg://user?id={user_id}'


async def ent(message: types.Message):
    ents = [entity for entity in message.entities if entity.type == 'text_mention']
    if ents:
        first_name = ents[0].user.first_name
        user_id = ents[0].user.id
        username = ents[0].user.username
    else:
        username = message.text.split()[1]
        user = utils.get_user_by_username(message.chat.id, username[1:])
        if not user:
            return
        user_id = user.user_id
        first_name = user.first_name
        username = username[1:]
    return user_id, first_name, username


async def info_message(
        command,
        chat_title,
        chat_id,
        first_name,
        user_id,
        to_first_name,
        to_user_id,
        username=None,
        to_username=None
):
    text = fmt.text(
        f'#{command}\n\n'
        f'Группа: {chat_title}\n'
        f'[#chat{str(chat_id)[1:]}]\n'
        f'Инициатор: {fmt.quote_html(first_name)} [{username or "Не задано"}]\n'
        f'[#user{user_id}]\n'
        f'Пользователь: {fmt.quote_html(to_first_name)} [{to_username or "Не задано"}]\n'
        f'[#user{to_user_id}]\n'
        f'Время: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    group_id = utils.get_setting().id_group_log
    await bot.send_message(group_id, text)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.chat.type == 'private':
        buttons = ['Купить разбан',
                   'Купить разварн',
                   'Купить префикс',
                   'Купить 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮']
        if utils.check_vip(message.from_user.id):
            buttons.append('VIP RP команда')
        else:
            buttons.append('Купить VIP')
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*buttons)
        await message.answer('Добро пожаловать!\n\n'
                             'Выберите услугу из списка ниже:\n'
                             'Разбан снимает бан с пользователя в группе.\n'
                             'Цена разбана - 200 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n\n'
                             'Разварн снимает все предупреждения с пользователя в группе.\n'
                             'Цена разварна - 150 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n\n'
                             'Купить префикс:\nна 3 дня - 50 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n'
                             'на неделю - 100 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n\n'
                             'Вы можете купить VIP.\n'
                             'Цена услуги - 300 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮. Срок - 1 месяц.\n\n'
                             f'Ваши средства - {utils.get_money(message.from_user.id)} 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n'
                             'Выберите пункт в меню:', reply_markup=keyboard)
    else:
        await message.delete()
        return


@dp.message_handler(commands=['stats'])
async def stats(message: types.Message):
    if message.chat.type == 'private':
        return
    await try_delete(message)
    if not any([
        is_big_owner(message.from_user.id),
        is_owner(message.from_user.id),
        is_admin(message.chat.id, message.from_user.id),
        is_moder(message.chat.id, message.from_user.id)
    ]):
        return
    users = utils.get_users(message.chat.id)
    date_create = users[0].create_time
    user_in_db = len(users)
    user_active = len([user for user in users if user.is_active])
    count_message = sum([user.count_message for user in users])
    max_message = max([(user.count_message, user.user_id, user.first_name) for user in users])
    mention_max = await mention_text(max_message[2], max_message[1])
    min_message = min([(user.count_message, user.user_id, user.first_name) for user in users])
    mention_min = await mention_text(min_message[2], min_message[1])
    wedding = len([user.wedding for user in users if user.wedding]) // 2
    cash = sum([user.cash for user in users])
    max_cash = max([(user.cash, user.user_id, user.first_name) for user in users])
    mention_cash = await mention_text(max_cash[2], max_cash[1])
    min_cash = min([(user.cash, user.user_id, user.first_name) for user in users])
    mention_cash_min = await mention_text(min_cash[2], min_cash[1])
    mute_max = max([(user.mute, user.user_id, user.first_name) for user in users])
    mention_mute = await mention_text(mute_max[2], mute_max[1])
    text = fmt.text(
        f'Статистика чата с {date_create}:\n\n',
        f'Всего пользователей: {user_in_db}\n',
        f'Активно пользователей: {user_active}\n',
        f'Всего сообщений: {count_message}\n',
        f'Больше всего сообщений у ',
        fmt.hlink(*mention_max),
        f' - {max_message[0]}\n',
        f'Меньше всего сообщений у ',
        fmt.hlink(*mention_min),
        f' - {min_message[0]}\n',
        f'Пар в чате - {wedding}\n',
        f'Всего средств в чате: {cash} 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n',
        f'Самый богатый: ',
        fmt.hlink(*mention_cash),
        f' - {max_cash[0]} 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n',
        f'Самый бедный: ',
        fmt.hlink(*mention_cash_min),
        f'- {min_cash[0]} 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n',
        f'Самый злостный нарушитель: ',
        fmt.hlink(*mention_mute),
        f'- {mute_max[0]} нарушений\n'
    )
    await message.answer(text)


@dp.message_handler(commands=['браки'])
async def get_pair(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    if utils.salent(message.chat.id):
        return
    dict_pair = {}
    pairs = utils.get_pair(message.chat.id)
    if not pairs:
        text = 'Людей на планете осталось так мало, что последний ЗАГС заколотил двери...'
    for user in pairs:
        user_id = user.user_id
        first_name = user.first_name
        wend = user.wedding
        wedding_time = datetime.datetime.strptime(user.wedding_time, "%Y-%m-%d %H:%M:%S")
        if wend not in dict_pair:
            dict_pair[user_id] = (wend, first_name, wedding_time)
    if dict_pair:
        text = f'Всего пар в {message.chat.title}: <b>{len(dict_pair)}</b>:\n'
        dict_pair = {k: v for k, v in sorted(dict_pair.items(), key=lambda item: item[1][2])}
    count = 1
    for k, v in dict_pair.items():
        mention = await mention_text(v[1], k)
        user_two = utils.get_user(message.chat.id, v[0])
        if user_two:
            mention_two = await mention_text(user_two.first_name, v[0])
            day_wending = (datetime.datetime.now() - v[2]).total_seconds()
            text += fmt.text(fmt.text(count), ') ', fmt.hlink(*mention), f' и {fmt.hlink(*mention_two)} в браке: {utils.wedding_date_now(day_wending)}.\n')
            count += 1
    await message.answer(text)


@dp.message_handler(commands=['свадьба'])
async def wedding(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    if utils.salent(message.chat.id):
        return
    text = message.text.split()
    if len(text) == 1:
        if not message.reply_to_message:
            await message.reply('Эта команда должна быть ответом на сообщение!')
            return
        user_id = message.reply_to_message.from_user.id
        first_name = message.reply_to_message.from_user.first_name
        username = message.reply_to_message.from_user.username
        is_bot = message.reply_to_message.from_user.is_bot
    else:
        user_id, first_name, username = await ent(message)
        is_bot = 0
    if user_id == message.from_user.id:
        await message.answer('В нашем мире пока нельзя жениться на самом себе!')
        return
    if is_bot:
        await message.answer('Законодательно запретили браки между роботами и людьми!')
        return
    mention_two = await mention_text(first_name, user_id)
    mention_one = await mention_text(message.from_user.first_name, message.from_user.id)
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton('Согласиться', callback_data='YES'),
               types.InlineKeyboardButton('Отказать', callback_data='NO')]
    keyboard.add(*buttons)
    if not utils.user_exists(message.chat.id, user_id):
        await message.answer('Я еще не знаю такого человека!')
    if not utils.user_exists(message.chat.id, message.from_user.id):
        await message.answer('Я еще не знаю такого человека!')
    user_const = utils.get_constant(user_id)
    if user_const:
        session.delete(user_const)
        session.commit()
    person_one = utils.get_user(message.chat.id, message.from_user.id)
    person_two = utils.get_user(message.chat.id, user_id)
    if not person_one and not person_two:
        return
    if not person_one.wedding and not person_two.wedding:
        msg = await message.answer(f'💗{fmt.hlink(*mention_two)}, минуту внимания!\n'
                                   f'{fmt.hlink(*mention_one)} сделал(а) вам предложение руки и сердца.🥰',
                                   reply_markup=keyboard)
        asyncio.create_task(delete_message(msg, 120))
    else:
        user_const = utils.get_constant(user_id)
        if user_const:
            session.delete(user_const)
            session.commit()
        if person_one.wedding:
            msg = await message.answer(f'Увы, {fmt.hlink(*mention_one)}, вы уже в браке!')
            asyncio.create_task(delete_message(msg, 3))
        if person_two.wedding:
            msg = await message.answer(f'Увы, {fmt.hlink(*mention_two)}, уже состоит браке!')
            asyncio.create_task(delete_message(msg, 3))
    weddings = Constants(chat_id=message.chat.id,
                         user_id=user_id,
                         person_first_name=message.from_user.first_name,
                         person_id=message.from_user.id,
                         person_two_first_name=first_name,
                         person_two_id=user_id)
    session.add(weddings)
    session.commit()
    await info_message(
        'свадьба',
        message.chat.title,
        message.chat.id,
        message.from_user.first_name,
        message.from_user.id,
        first_name,
        user_id,
        message.from_user.username,
        username
    )


@dp.message_handler(commands=['развод'])
async def no_marry(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    if utils.salent(message.chat.id):
        return
    user = utils.get_user(message.chat.id, message.from_user.id)
    if user.wedding:
        mention = await mention_text(message.from_user.first_name, message.from_user.id)
        person_two = utils.get_user(message.chat.id, user.wedding)
        mention_two = await mention_text(person_two.first_name, person_two.user_id)
        user.wedding = 0
        user.wedding_time = None
        person_two.wedding = 0
        person_two.wedding_time = None
        session.commit()
        msg = await message.answer(f'💔Сожалеем {fmt.hlink(*mention_two)}, {fmt.hlink(*mention)} решил(а) разорвать отношения между вами.')
        asyncio.create_task(delete_message(msg, 10))
        await info_message(
            'развод',
            message.chat.title,
            message.chat.id,
            message.from_user.first_name,
            message.from_user.id,
            person_two.first_name,
            person_two.user_id,
            message.from_user.username,
            person_two.username
        )


@dp.callback_query_handler(lambda m: m.data in ['YES', 'NO'])
async def wedding_answer(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    wedding_constant = utils.get_constant_wedding(
        callback_query.message.chat.id, callback_query.from_user.id)
    if wedding_constant:
        session.delete(wedding_constant)
        session.commit()
    try:
        if callback_query.from_user.id == wedding_constant.person_two_id:
            mention_one = await mention_text(wedding_constant.person_first_name, wedding_constant.person_id)
            mention_two = await mention_text(wedding_constant.person_two_first_name, wedding_constant.person_two_id)
            if callback_query.data == 'YES':
                msg = await bot.send_message(callback_query.message.chat.id, f'💖Поздравляем молодожёнов!\n'
                                                                             f'{fmt.hlink(*mention_one)} и {fmt.hlink(*mention_two)} теперь в браке.💍')
                await callback_query.message.delete()
                asyncio.create_task(delete_message(msg, 20))
                person_one = utils.get_user(callback_query.message.chat.id, wedding_constant.person_id)
                person_two = utils.get_user(callback_query.message.chat.id, wedding_constant.person_two_id)
                person_one.wedding = wedding_constant.person_two_id
                person_two.wedding = wedding_constant.person_id
                person_one.wedding_time = person_two.wedding_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                session.commit()
            if callback_query.data == 'NO':
                msg = await bot.send_message(callback_query.message.chat.id,
                                             f'{fmt.hlink(*mention_one)}, сожалею, {fmt.hlink(*mention_two)} вам отказал(а).💔')
                await callback_query.message.delete()
                asyncio.create_task(delete_message(msg, 20))
    except Exception as e:
        logging.info(
            f'{callback_query.message.text} - {callback_query.message.chat.id} - {callback_query.message.from_user.id}',
            exc_info=e)


@dp.message_handler(commands=['карма'])
async def carma(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    if utils.salent(message.chat.id):
        return
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        first_name = message.reply_to_message.from_user.first_name
    else:
        user_id = message.from_user.id
        first_name = message.from_user.first_name
    user = utils.get_user(message.chat.id, user_id)
    rank = ''
    for k, v in range_tab.items():
        if user.reputation in v:
            rank = k
            break
    karma_title = ''
    for k, v in exp_tab.items():
        if user.karma >= 16450:
            karma_title = exp_tab[16450]
            break
        if user.karma <= k:
            karma_title = v
            break
    if rank == 'Нейтральный':
        karma_title = karma_title[1]
    elif rank in ('Добрый','Очень добрый'):
        karma_title = karma_title[2]
    else:
        karma_title = karma_title[0]
    mention = await mention_text(first_name, user_id)
    text = fmt.text(fmt.hlink(*mention),
            f'\n✨|Ваша карма: {rank} ({user.reputation})\n',
            f'🏅|Очки кармы: {user.karma}\n',
            f'☯️|Ваш кармический титул: {karma_title}')
    await message.answer(text)


@dp.message_handler(lambda m: m.text in ('-','+'))
async def add_karma(message: types.Message):
    if message.reply_to_message:
        await try_delete(message)
        user_id = message.reply_to_message.from_user.id
        if user_id == message.from_user.id:
            await message.delete()
            await message.answer('Изменять карму самому себе нельзя!')
            return
        first_name = message.reply_to_message.from_user.first_name
        if utils.user_exists(message.chat.id, user_id):
            user = utils.get_user(message.chat.id, user_id)
            if not user:
                return
            if message.text == '+':
                user.reputation += 1
            else:
                user.reputation -= 1
            if user.reputation > 500:
                user.reputation = 500
            if user.reputation < -500:
                user.reputation = -500
            rank = ''
            for k, v in range_tab.items():
                if user.reputation in v:
                    rank = k
                    break
            session.commit()
            mention_one = await mention_text(first_name, user_id)
            mention_two = await mention_text(message.from_user.first_name, message.from_user.id)
            await message.answer(fmt.text(fmt.hlink(*mention_one), ', вам изменил карму ', fmt.hlink(*mention_two), f'.\nВаша карма: {rank} ({user.reputation})'))


@dp.message_handler(commands=['info'])
async def info(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    if utils.salent(message.chat.id):
        return
    if len(message.text.split()) >= 2:
        if not any([
            is_big_owner(message.from_user.id),
            is_owner(message.from_user.id),
            is_admin(message.chat.id, message.from_user.id),
            is_moder(message.chat.id, message.from_user.id)
        ]):
            return
        user_id, first_name, username = await ent(message)
    else:
        user_id = message.from_user.id
        username = message.from_user.id
        first_name = message.from_user.first_name
    mention = await mention_text(first_name, user_id)
    user = utils.get_user(message.chat.id, user_id)
    if not utils.user_exists(message.chat.id, user_id):
        await message.answer('Пользователь отсутствует в базе, добавить - /add  ответ на сообщение')
    if user.wedding:
        wend = utils.get_user(message.chat.id, user.wedding)
        wedding = wend.first_name
    else:
        wedding = 'Не женат/Не замужем'
    rank = ''
    for k, v in range_tab.items():
        if user.reputation in v:
            rank = k
    text = (f'🔤|Никнейм: @{user.username or "Не задано"}\n'
            f'👤|Профиль: {fmt.hlink(*mention)}\n'
            f'🔢|Id: <code>{user.user_id}</code>\n\n'
            f'🕛|Дата первого входа: {user.create_time}\n'
            f'💠|Ранг: {user.role}\n'
            f'↕️|Карма: {rank} ({user.reputation})\n'
            f'👫|Семейное положение: {fmt.hlink(*await mention_text(wedding, user.wedding))}\n'
            f'💰|𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮 в чате: {user.cash}\n'
            f'🕐|Первое сообщение: {user.first_message}\n'
            f'🕐|Последний бан: {user.time_ban or "Не было"}\n'
            f'🕐|Последнее предупрежедние: {user.time_mute or "Не было"}\n'
            f'⚠️|Количество предупреждений: {user.mute or "Не было"}\n'
            f'🕛|Время последнего сообщения: {user.last_message}\n'
            f'💬|Количество сообщений: {user.count_message}\n'
            f'🆙|Опыт: {user.exp}\n'
            f'🕐|Последнее ограничение: {user.mute_reason or "Не было"}\n'
            )
    await message.answer(text)
    await info_message(
        'info',
        message.chat.title,
        message.chat.id,
        message.from_user.first_name,
        message.from_user.id,
        first_name,
        user_id,
        message.from_user.username,
        username
    )


@dp.message_handler(commands=['admins'])
async def admins(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    if utils.salent(message.chat.id):
        return
    if not any([
        is_big_owner(message.from_user.id),
        is_owner(message.from_user.id),
        is_admin(message.chat.id, message.from_user.id),
        is_moder(message.chat.id, message.from_user.id)
    ]):
        return
    admins, moders, owners = utils.get_all_admin(message.chat.id)
    text = fmt.text(fmt.hlink(*await mention_text('Владелец', config.ADMIN_ID)), '\n')
    for owner in owners:
        mention = await mention_text('Совладелец', owner.owner_id)
        text += fmt.text(fmt.hlink(*mention), '\n')
    text += 'Администраторы:\n'
    for admin in admins:
       mention = await mention_text(admin.first_name, admin.user_id)
       text += fmt.text(fmt.hlink(*mention), '\n')
    text += 'Модераторы:\n'
    for moder in moders:
        mention = await mention_text(moder.first_name, moder.user_id)
        text += fmt.text(fmt.hlink(*mention), '\n')
    msg = await message.answer(text)
    asyncio.create_task(delete_message(msg, 15))
    await info_message(
        'admins',
        message.chat.title,
        message.chat.id,
        message.from_user.first_name,
        message.from_user.id,
        message.from_user.first_name,
        message.from_user.id,
        message.from_user.username,
        message.from_user.username
    )


@dp.message_handler(content_types=['new_chat_members'])  # Вошел
async def user_joined(message: types.Message):
    await try_delete(message)
    if message.new_chat_members[0].id == dict(await bot.get_me()).get('id'):
        group = Groups(group_id=message.chat.id, title=message.chat.title)
        user = FlameNet(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            is_active=1,
            create_time=datetime.date.today(),
            first_message=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        session.add(group)
        session.add(user)
        session.commit()
    else:
        if not utils.setka(message.chat.id):
            return
        for user in message.new_chat_members:
            mention = await mention_text(user.first_name, user.id)
            if not utils.user_exists(message.chat.id, message.from_user.id):
                user = FlameNet(
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    is_active=1,
                    create_time=datetime.date.today(),
                    first_message=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                session.add(user)
            else:
                user = utils.get_user(message.chat.id, message.from_user.id)
                user.is_active = 1
            session.commit()
            if utils.banned_exists(user.id):
                await bot.ban_chat_member(message.chat.id, user.id)
                await bot.send_message(
                    message.chat.id,
                    f'Пользователь {fmt.hlink(*mention)} забанен.\nПричина: Систематические нарушения правил.'
                )
            if message.chat.id == -1001781348153:
                text = f'{fmt.hlink(*mention)}, добро пожаловать в увлекательный мир мафии, {message.chat.title}.\nПожалуйста, ознакомьтесь с правилами группы👥. Желаем вам приятных игр 👻🔥'
                button = types.InlineKeyboardButton('Правила группы', url='https://t.me/flamee_RuleS')
                keyboard = types.InlineKeyboardMarkup().add(button)
                msg = await message.answer(text, reply_markup=keyboard)
                asyncio.create_task(delete_message(msg, 10))
            elif message.chat.id == -1001629215553:
                setting = utils.get_setting()
                if setting.gif:
                    text = (f'{fmt.hlink(*mention)}|<code>{user.user_id}</code>\n'
                            f'Добро пожаловать в увлекательный мир комбат мафии🥷👻'
                            f'Ниже ты найдешь полезные ссылки, которые помогут тебе быстрее освоиться в чате {message.chat.title}\n'
                            f'📌Идет игра и желаешь присоединиться? Жми /join\n'
                            f'💢Обрати внимание, что только первые 3 захода бесплатны, советую всем зайти на ссылке ниже:')
                    buttons = [
                        types.InlineKeyboardButton('Правила', url='https://t.me/flamecombatrules'),
                        types.InlineKeyboardButton('Описание ролей', url='https://t.me/flamecombatroles'),
                        types.InlineKeyboardButton('Чат с ботами', url='https://t.me/+Ddvm07b6rKYxOTQy'),
                        types.InlineKeyboardButton('Канал Владельца', url='https://t.me/derzkyi')
                        ]
                    keyboard = types.InlineKeyboardMarkup(row_width=1).add(*buttons)
                    msg = await message.answer(text, reply_markup=keyboard)
                    asyncio.create_task(delete_message(msg, 10))
            if utils.owner_exists(user.id):
                await bot.promote_chat_member(
                    message.chat.id,
                    user.id,
                    can_manage_chat=True,
                    can_delete_messages=True,
                    can_restrict_members=True
                )
                await bot.set_chat_administrator_custom_title(message.chat.id, user.id, custom_title='Совладелец')
                await message.answer(f'<b>Пользователь {fmt.hlink(*mention)} назначен совладельцем сети!</b>')
            await info_message(
                'Новый пользователь',
                message.chat.title,
                message.chat.id,
                message.from_user.first_name,
                message.from_user.id,
                user.first_name,
                user.user_id,
                message.from_user.username,
                user.username
            )


@dp.message_handler(content_types=["left_chat_member"])  # Вышел
async def on_user_exit(message: types.Message):
    await try_delete(message)
    if not utils.setka(message.chat.id):
        return
    user = utils.get_user(message.chat.id, message.left_chat_member.id)
    user.is_active = 0
    session.commit()
    await info_message(
        'Вышел из чата',
        message.chat.title,
        message.chat.id,
        message.from_user.first_name,
        message.from_user.id,
        message.left_chat_member.first_name,
        message.left_chat_member.id,
        message.from_user.username,
        message.left_chat_member.username
    )


@dp.message_handler(commands=['ban'])
async def ban(message: types.Message):
    if message.chat.type == 'private':
        return
    text = message.text.split()
    from_id = message.from_user.id
    chat_id = message.chat.id
    big_owner = is_big_owner(message.from_user.id)
    owner = is_owner(message.from_user.id)
    admin = is_admin(message.chat.id, message.from_user.id)
    moder = is_moder(message.chat.id, message.from_user.id)
    if not any([
        big_owner,
        owner,
        admin,
        moder
    ]):
        return
    user_id, first_name, username = await ent(message)
    if not utils.user_exists(message.chat.id, user_id):
        await message.answer('Пользователь отсутствует в базе, обновите базу через /print')
    is_owner_user = is_owner(user_id)
    is_admin_user = is_admin(chat_id, user_id)
    is_moder_user = is_moder(chat_id, user_id)
    if user_id == big_owner:
        await message.answer('Недостаточно прав!')
        return
    elif moder and any([is_moder_user, is_admin_user, is_owner_user]):
        await message.answer('Недостаточно прав!')
        return
    elif admin and any([is_owner_user, is_admin_user]):
        await message.answer('Недостаточно прав!')
        return
    elif owner and is_owner_user:
        await message.answer('Недостаточно прав!')
        return
    else:
        mention = await mention_text(first_name, user_id)
        user = utils.get_user(chat_id, from_id)
        if text[-1] == '0':
            user.ban = 0
            await bot.unban_chat_member(message.chat.id, user_id, only_if_banned=True)
            await message.answer(f'Пользователь {fmt.hlink(*mention)} разбанен.')
        else:
            user.ban = 1
            user.time_ban = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            await bot.ban_chat_member(message.chat.id, user_id)
            await message.answer(f'Пользователь {fmt.hlink(*mention)} забанен.\nПричина: Систематические нарушения правил.')
        session.commit()
    await info_message(
        'ban',
        message.chat.title,
        chat_id,
        message.from_user.first_name,
        from_id,
        first_name,
        user_id,
        message.from_user.username,
        username
    )


@dp.message_handler(commands=['set_admin'])  # /set_admin <username> 1 or 0
async def set_admin(message: types.Message):
    if message.chat.type == 'private':
        return
    from_id = message.from_user.id
    big_owner = is_big_owner(message.from_user.id)
    owner = is_owner(message.from_user.id)
    admin = is_admin(message.chat.id, message.from_user.id)
    moder = is_moder(message.chat.id, message.from_user.id)
    if not any([
        big_owner,
        owner,
        admin,
        moder
    ]):
        return
    text = message.text.split()
    chat_id = message.chat.id
    if message.from_user.id == config.ADMIN_ID:
        if len(text) == 2:
            if not message.reply_to_message:
                await message.reply('Эта команда должна быть ответом на сообщение!')
                return

            user_id = message.reply_to_message.from_user.id
            first_name = message.reply_to_message.from_user.first_name
            username = message.reply_to_message.from_user.username
        else:
            user_id, first_name, username = await ent(message)
        if not utils.user_exists(message.chat.id, user_id):
            await message.answer('Пользователь отсутствует в базе, добавить - /add  ответ на сообщение')
        is_owner_user = is_owner(user_id)
        if user_id == big_owner:
            await message.answer('Недостаточно прав!')
            return
        elif moder:
            await message.answer('Недостаточно прав!')
            return
        elif admin:
            await message.answer('Недостаточно прав!')
            return
        elif owner and is_owner_user:
            await message.answer('Недостаточно прав!')
            return
        else:
            mention = await mention_text(first_name, user_id)
            user = utils.get_user(chat_id, from_id)
            user.is_admin = int(text[-1])
            session.commit()
            if user.is_admin:
                await bot.promote_chat_member(
                    chat_id,
                    user_id,
                    can_manage_chat=True,
                    can_delete_messages=True,
                    can_restrict_members=True
                )
                await asyncio.sleep(1)
                await bot.set_chat_administrator_custom_title(chat_id, user_id, custom_title='Администратор')
                await message.answer(f'Пользователь {fmt.hlink(*mention)} назначен администратором сообщества.')
            else:
                await bot.promote_chat_member(
                    chat_id, user_id
                )
                await message.answer(f'Пользователь {fmt.hlink(*mention)} снят с должности администратора.')
        await info_message(
            'set_admin',
            message.chat.title,
            chat_id,
            message.from_user.first_name,
            from_id,
            first_name,
            user_id,
            message.from_user.username,
            username
        )
    try:
        await message.delete()
    except (MessageToDeleteNotFound, MessageCantBeDeleted):
        pass
    return


@dp.message_handler(commands=['tag'])
async def tag_set(message: types.Message):
    if message.chat.type == 'private':
        return
    big_owner = is_big_owner(message.from_user.id)
    owner = is_owner(message.from_user.id)
    admin = is_admin(message.chat.id, message.from_user.id)
    moder = is_moder(message.chat.id, message.from_user.id)
    if not any([
        big_owner,
        owner,
        admin,
        moder
    ]):
        await message.answer('Прав недостаточно!')
        return
    await Tagall.func.set()
    await message.answer('Введите команду /run (текст призыва)')
    try:
        await message.delete()
    except (MessageToDeleteNotFound, MessageCantBeDeleted):
        pass
    return


@dp.message_handler(commands=['run'], state=Tagall.func)
async def tag(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    text = message.text.split()
    try:
        await message.delete()
    except (MessageToDeleteNotFound, MessageCantBeDeleted):
        pass
    try:
        if len(text) >= 2:
            count = 0
            response = f'{" ".join(text[1:])}\n'
            users = utils.get_users(chat_id)[:101]
            random.shuffle(users)
            for user in users:
                if not await state.get_state():
                    break
                mention = await mention_text(user.first_name, user.user_id)
                response += f'{fmt.hlink(*mention)}\n'
                count += 1
                if count == 5:
                    msg = await message.answer(response)
                    asyncio.create_task(delete_message(msg, 2))
                    await asyncio.sleep(3)
                    count = 0
                    response = f'{" ".join(text[1:])}\n'
    except RetryAfter:
        await asyncio.sleep(2)
    finally:
        await message.answer('Призыв окончен!')
        await state.finish()


@dp.message_handler(commands=['чек'], state='*')
async def check_tag(message: types.Message, state: FSMContext):
    if await state.get_state():
        await message.answer(f'текущее стостояние {fmt.quote_html(await state.get_state())}')
    else:
        await message.answer('Не установлено')


@dp.message_handler(Text(equals="стоп", ignore_case=True), state=Tagall.func)
@dp.message_handler(Text(equals="отмена", ignore_case=True), state=Tagall.func)
async def stop(message: types.Message,  state=FSMContext):
    await state.finish()
    mention = await mention_text(message.from_user.first_name, message.from_user.id)
    await message.answer(f'{fmt.hlink(*mention)}, призыв остановлен!')


@dp.message_handler(commands=['игнор'])
async def ignore(message: types.Message):
    mention = await mention_text(message.from_user.first_name, message.from_user.id)
    user = utils.get_user(message.chat.id, message.from_user.id)
    user.is_active = 0
    session.commit()
    await message.answer(f'{fmt.hlink(*mention)}, Вы исключены из призыва!')


@dp.message_handler(commands=['set_moder'])  # /set_moder <username> 1 or 0
async def set_moder(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    from_id = message.from_user.id
    big_owner = is_big_owner(message.from_user.id)
    owner = is_owner(message.from_user.id)
    admin = is_admin(message.chat.id, message.from_user.id)
    moder = is_moder(message.chat.id, message.from_user.id)
    if not any([
        big_owner,
        owner,
        admin,
        moder
    ]):
        return
    text = message.text.split()
    chat_id = message.chat.id
    if message.from_user.id == config.ADMIN_ID:
        if len(text) == 2:
            if not message.reply_to_message:
                await message.reply('Эта команда должна быть ответом на сообщение!')
                return
            user_id = message.reply_to_message.from_user.id
            first_name = message.reply_to_message.from_user.first_name
            username = message.reply_to_message.from_user.username
        else:
            user_id, first_name, username = await ent(message)
        if not utils.user_exists(message.chat.id, user_id):
            await message.answer('Пользователь отсутствует в базе, добавить - /add  ответ на сообщение')
        is_owner_user = is_owner(user_id)
        is_admin_user = is_admin(chat_id, user_id)
        if user_id == big_owner:
            await message.answer('Недостаточно прав!')
            return
        elif moder:
            await message.answer('Недостаточно прав!')
            return
        elif admin and any([is_owner_user, is_admin_user]):
            await message.answer('Недостаточно прав!')
            return
        elif owner and is_owner_user:
            await message.answer('Недостаточно прав!')
            return
        else:
            mention = await mention_text(first_name, user_id)
            user = utils.get_user(message.chat.id, user_id)
            user.is_moder = int(text[-1])
            session.commit()
            if user.is_moder:
                await bot.promote_chat_member(
                    chat_id,
                    user_id,
                    can_manage_chat=True,
                )
                await asyncio.sleep(5)
                await bot.set_chat_administrator_custom_title(chat_id, user_id, custom_title='Модератор')
                await message.answer(f'Пользователь {fmt.hlink(*mention)} назначен модератором сообщества.')
            else:
                await bot.promote_chat_member(
                    chat_id, user_id
                )
                await message.answer(f'Пользователь {fmt.hlink(*mention)} снят с должности модератора.')
        await info_message(
            'set_moder',
            message.chat.title,
            chat_id,
            message.from_user.first_name,
            from_id,
            message.from_user.first_name,
            from_id,
            message.from_user.username,
            message.from_user.username
        )


@dp.message_handler(commands=['add_money'])  # /add_money @username 1000
async def add_money(message: types.Message):
    try:
        await try_delete(message)
        if message.chat.type == 'private':
            return
        text = message.text.split()
        from_id = message.from_user.id
        if not any([
            is_big_owner(from_id),
            is_owner(from_id)
        ]):
            return
        if len(text) >= 3:
            user_id, first_name, username = await ent(message)
        else:
            if not message.reply_to_message:
                await message.reply('Эта команда должна быть ответом на сообщение!')
                return

            user_id = message.reply_to_message.from_user.id
            first_name = message.reply_to_message.from_user.first_name
            username = message.reply_to_message.from_user.username
        if not utils.user_exists(message.chat.id, user_id):
            await message.answer('Пользователь отсутствует в базе, добавить - /add  ответ на сообщение')
        if abs(int(text[-1])) > 1000000000:
            await message.answer(f'Число за пределами разумного!')
            return
        chat_id = message.chat.id
        if chat_id in [-1001496141543]:
            chat_id = -1001781348153
        user = utils.get_user(chat_id, user_id)
        mention = await mention_text(first_name, user_id)
        if int(text[-1]) > 0:
            user.cash += int(text[-1])
            await message.answer(
                f'Пользователю {fmt.hlink(*mention)} начислено {text[-1]} 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮')  # Пользователю @х начислено 10 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛💠
        else:
            user.cash -= int(text[-1])
            await message.answer(
                f'Во время налоговой проверки у {fmt.hlink(*mention)} изьяли {text[-1]} 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮')  # Пользователю @х начислено 10 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛💠
        session.commit()
        await info_message(
            'add_money',
            message.chat.title,
            message.chat.id,
            message.from_user.first_name,
            from_id,
            first_name,
            user_id,
            message.from_user.username,
            username
        )
    except Exception as e:
        logging.info(e)


@dp.message_handler(commands='gift')
async def gift(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    if utils.salent(message.chat.id):
        return
    text = message.text.split()
    from_id = message.from_user.id
    if len(text) >= 3:
        user_id, first_name, username = await ent(message)
    else:
        if not message.reply_to_message:
            await message.reply('Эта команда должна быть ответом на сообщение!')
            return

        user_id = message.reply_to_message.from_user.id
        first_name = message.reply_to_message.from_user.first_name
        username = message.reply_to_message.from_user.username
    if not utils.user_exists(message.chat.id, user_id):
        await message.answer('Пользователь отсутствует в базе, обновите базу через /print')
    user = utils.get_user(message.chat.id, message.from_user.id)
    user_two = utils.get_user(message.chat.id, user_id)
    if int(text[-1]) <= 0:
        await message.answer('Нельзя отнимать деньги!')
        return
    if user.cash < int(text[-1]):
        await message.answer('Слишком мало денег на счету.')
    else:
        user.cash -= int(text[-1])
        user_two.cash += int(text[-1])
        mention = await mention_text(first_name, user_id)
        donater = await mention_text(message.from_user.first_name, from_id)
        await message.answer(
            f'{fmt.hlink(*donater)} пожертвовал пользователю {fmt.hlink(*mention)} {text[-1]} 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮')
    await info_message(
        'gift',
        message.chat.title,
        message.chat.id,
        message.from_user.first_name,
        from_id,
        first_name,
        user_id,
        message.from_user.username,
        username
    )


@dp.message_handler(commands='setting')
async def setting(message: types.Message):
    await try_delete(message)
    if message.chat.type != 'private':
        return
    big_owner = is_big_owner(message.from_user.id)
    owner = is_owner(message.from_user.id)
    if not any([big_owner, owner]):
        return
    if not utils.get_setting():
        setting = Setting(id=1)
        session.add(setting)
        session.commit()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = ['Валюта', 'Опыт', 'Инфогруппа', 'Приветствие в группе']
    keyboard.add(*buttons)
    await message.answer('Выберите пункт для настройки', reply_markup=keyboard)
    try:
        await message.delete()
    except (MessageToDeleteNotFound, MessageCantBeDeleted):
        pass
    return


def key_setting():
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton('+', callback_data='+'), types.InlineKeyboardButton('-', callback_data='-')]
    keyboard.add(*buttons)
    return keyboard


def key_setting_exp():
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton('+', callback_data='+exp'),
               types.InlineKeyboardButton('-', callback_data='-exp')]
    keyboard.add(*buttons)
    return keyboard


def key_setting_group(groups):
    keyboard = types.InlineKeyboardMarkup()
    for group in groups:
        keyboard.add(types.InlineKeyboardButton(f'{group.title}', callback_data=group.group_id))
    return keyboard


def key_setting_gif():
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton('Включить', callback_data='gifon'),
               types.InlineKeyboardButton('Выключить', callback_data='gifoff')]
    keyboard.add(*buttons)
    return keyboard


@dp.message_handler(lambda m: m.text == 'Валюта')
async def cash(message: types.Message):
    if message.chat.type != 'private':
        return
    big_owner = is_big_owner(message.from_user.id)
    owner = is_owner(message.from_user.id)
    if not any([big_owner, owner]):
        await message.answer('Недостаточно прав')
        return
    setting = utils.get_setting()
    money = setting.money_for_game
    msg = await message.answer(f'Количество валюты за победу в игре: {money}', reply_markup=key_setting())
    asyncio.create_task(delete_message(msg, 10))


@dp.message_handler(lambda m: m.text == 'Приветствие в группе')
async def gif(message: types.Message):
    if message.chat.type != 'private':
        return
    big_owner = is_big_owner(message.from_user.id)
    owner = is_owner(message.from_user.id)
    if not any([big_owner, owner]):
        await message.answer('Недостаточно прав')
        return
    setting = utils.get_setting()
    if setting.gif:
        params = 'Да'
    else:
        params = 'Нет'
    msg = await message.answer(f'Приветствие: {params}', reply_markup=key_setting_gif())
    asyncio.create_task(delete_message(msg, 10))


@dp.callback_query_handler(lambda m: 'gif' in m.data)
async def gif_swith(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    if callback_query.data == 'gifon':
        gif = 1
    else:
        gif = 0
    setting = utils.get_setting()
    setting.gif = gif
    session.commit()
    if setting.gif:
        params = 'Да'
    else:
        params = 'Нет'
    msg = await bot.edit_message_text(
        f'Приветствие: {params}',
        callback_query.message.chat.id,
        callback_query.message.message_id,
        reply_markup=key_setting_gif()
    )
    asyncio.create_task(delete_message(msg, 10))


@dp.message_handler(lambda m: m.text == 'Опыт')
async def exp(message: types.Message):
    if message.chat.type != 'private':
        return
    big_owner = is_big_owner(message.from_user.id)
    owner = is_owner(message.from_user.id)
    if not any([big_owner, owner]):
        await message.answer('Недостаточно прав')
        return
    setting = utils.get_setting()
    exp = setting.exp_for_message
    msg = await message.answer(f'Количество опыта за сообщение: {exp}', reply_markup=key_setting_exp())
    asyncio.create_task(delete_message(msg, 10))


@dp.message_handler(lambda m: m.text == 'Инфогруппа')
async def info_group(message: types.Message):
    if message.chat.type != 'private':
        return
    big_owner = is_big_owner(message.from_user.id)
    owner = is_owner(message.from_user.id)
    if not any([big_owner, owner]):
        await message.answer('Недостаточно прав')
        return
    groups = utils.get_groups()
    msg = await message.answer(f'Выберите группу для пересылки команд бота.', reply_markup=key_setting_group(groups))
    asyncio.create_task(delete_message(msg, 10))


@dp.callback_query_handler(lambda m: 'exp' in m.data)
async def set_exp_game(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    setting = utils.get_setting()
    exp = setting.exp_for_message
    if callback_query.data[0] == '+':
        exp += 1
    if exp > 0 and callback_query.data[0] == '-':
        exp -= 1
    setting.exp = exp
    session.commit()
    msg = await bot.edit_message_text(
        f'Количество опыта за сообщение: {exp}',
        callback_query.message.chat.id,
        callback_query.message.message_id,
        reply_markup=key_setting_exp()
    )
    asyncio.create_task(delete_message(msg, 10))


@dp.callback_query_handler(lambda m: m.data in '+-')
async def set_money_game(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    setting = utils.get_setting()
    money = setting.money_for_game
    if callback_query.data == '+':
        money += 1
    if money > 0 and callback_query.data == '-':
        money -= 1
    setting.money_for_game = money
    session.commit()
    msg = await bot.edit_message_text(
        f'Количество валюты за победу в игре: {money}',
        callback_query.message.chat.id,
        callback_query.message.message_id,
        reply_markup=key_setting()
    )
    asyncio.create_task(delete_message(msg, 10))


@dp.callback_query_handler(lambda m: m.data.startswith('-100'))
async def set_info_group(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    group = utils.get_group(callback_query.data)
    setting = utils.get_setting()
    setting.id_group_log = callback_query.data
    session.commit()
    msg = await bot.edit_message_text(
        f'Установлена группа: {group.title}',
        callback_query.message.chat.id,
        callback_query.message.message_id
    )
    asyncio.create_task(delete_message(msg, 30))


@dp.message_handler(commands=['mute'])  # /mute <username> 1m or 1h  reason
async def mute(message: types.Message):
    if message.chat.type == 'private':
        return
    await try_delete(message)
    try:
        from_id = message.from_user.id
        chat_id = message.chat.id
        big_owner = is_big_owner(message.from_user.id)
        owner = is_owner(message.from_user.id)
        admin = is_admin(message.chat.id, message.from_user.id)
        moder = is_moder(message.chat.id, message.from_user.id)
        if not any([big_owner, owner, admin, moder]):
            return
        text = message.text.split()
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            first_name = message.reply_to_message.from_user.first_name
            username = message.reply_to_message.from_user.username
        else:
            user_id, first_name, username = await ent(message)
        if not utils.user_exists(message.chat.id, user_id):
            await message.answer('Пользователь отсутствует в базе, добавить - /add  ответ на сообщение')
        is_owner_user = is_owner(user_id)
        is_admin_user = is_admin(chat_id, user_id)
        is_moder_user = is_moder(chat_id, user_id)
        if user_id == big_owner:
            await message.answer('Недостаточно прав!')
            return
        elif moder and any([is_moder_user, is_admin_user, is_owner_user]):
            await message.answer('Недостаточно прав!')
            return
        elif admin and any([is_owner_user, is_admin_user]):
            await message.answer('Недостаточно прав!')
            return
        elif owner and is_owner_user:
            await message.answer('Недостаточно прав!')
            return
        else:
            mention = await mention_text(first_name, user_id)
            index = 0
            for word in text:
                if word.isalnum() and ('h' in word or 'm' in word):
                    index = text.index(word)
            mute_sec = int(text[index][:-1])
            end = text[index][-1]
            ending = utils.time_check(end, mute_sec)
            await bot.restrict_chat_member(message.chat.id, user_id,
                                           until_date=int(time.time()) + mute_sec * TIMECHECK.get(end, 1))
            user = utils.get_user(chat_id, user_id)
            user.mute += 1
            user.mute_reason = ' '.join(text[index:])
            user.time_mute = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if user.mute >= 20:
                await bot.send_message(
                    chat_id,
                    f'{fmt.hlink(*mention)} у вас очень много нарушений.\nСкоро бот выдаст автоматический бан.\nРекомендуется купить разварн в магазине!')
            if user.mute >= 25:
                user.ban = 1
                user.time_ban = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                await bot.ban_chat_member(chat_id, user_id)
                await bot.send_message(
                    chat_id,
                    f'Пользователь {fmt.hlink(*mention)} забанен.\nПричина: Количество нарушений превысило лимит.')
                return
            session.commit()
            await message.answer(
                    f'Пользователь {fmt.hlink(*mention)} получил мут на {mute_sec} {ending}.\nПричина: {" ".join(text[index + 1:])}\nНарушений: {user.mute}')
        await info_message(
            'mute',
            message.chat.title,
            message.chat.id,
            message.from_user.first_name,
            from_id,
            first_name,
            user_id,
            message.from_user.username,
            username
        )
    except (TypeError, ValueError) as e:
        await message.answer(f'Ой, ошибка: {e.args}')


@dp.message_handler(commands=['unmute'])
async def unmute(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    from_id = message.from_user.id
    chat_id = message.chat.id
    big_owner = is_big_owner(message.from_user.id)
    owner = is_owner(message.from_user.id)
    admin = is_admin(message.chat.id, message.from_user.id)
    moder = is_moder(message.chat.id, message.from_user.id)
    if not any([big_owner, owner, admin, moder]):
        return
    text = message.text.split()
    if len(text) == 1:
        if not message.reply_to_message:
            await message.reply('Эта команда должна быть ответом на сообщение!')
            return
        user_id = message.reply_to_message.from_user.id
        first_name = message.reply_to_message.from_user.first_name
        username = message.reply_to_message.from_user.username
    else:
        user_id, first_name, username = await ent(message)
    if not utils.user_exists(message.chat.id, user_id):
        await message.answer('Пользователь отсутствует в базе, обновите базу через /print')
    mention = await mention_text(first_name, user_id)
    await bot.restrict_chat_member(message.chat.id, user_id,
                                   permissions=types.ChatPermissions(True, True, True, True, True, True, True,
                                                                     True))
    user = utils.get_user(chat_id, user_id)
    if user.mute:
        user.mute -= 1
    else:
        user.mute = 0
    session.commit()
    await message.answer(f'C пользователя {fmt.hlink(*mention)} сняты ограничения.')
    await info_message(
        'unmute',
        message.chat.title,
        message.chat.id,
        message.from_user.first_name,
        from_id,
        first_name,
        user_id,
        message.from_user.username,
        username
    )


async def add_mute(chat_id, first_name, user_id, times, reason):
    await bot.restrict_chat_member(chat_id, user_id,
                                   until_date=int(time.time()) + int(times[:-1]) * TIMECHECK.get(times[-1], 1))
    user = utils.get_user(chat_id, user_id)
    user.mute += 1
    user.mute_reason = f'{times} {reason}'
    user.time_mute = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    mention = await mention_text(first_name, user_id)
    if user.mute >= 20:
        await bot.send_message(
            chat_id, f'{fmt.hlink(*mention)} у вас очень много нарушений.\nСкоро бот выдаст автоматический бан.\nРекомендуется купить разварн в магазине!')
    if user.mute >= 25:
        user.ban = 1
        user.time_ban = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        await bot.ban_chat_member(chat_id, user_id)
        await bot.send_message(
        chat_id, f'Пользователь {fmt.hlink(*mention)} забанен.\nПричина: Количество нарушений превысило лимит.')
        return
    session.commit()
    await bot.send_message(
        chat_id,
        f'Пользователь {fmt.hlink(*mention)} получил мут на {times[:-1]} {utils.time_check(times[-1], int(times[:-1]))}.\nПричина: {reason}\nНарушений: {user.mute}'
    )


@dp.message_handler(lambda m: m.text == 'Купить разбан', state='*')
async def unban(message: types.Message, state=FSMContext):
    if message.chat.type != 'private':
        await message.delete()
        return
    await state.finish()
    keyboard = await group_keyboard(message.chat.id, 'unban')
    await message.answer('Выберите группу:', reply_markup=keyboard)


@dp.message_handler(lambda m: m.text == 'Купить разварн', state='*')
async def unwarn(message: types.Message, state=FSMContext):
    if message.chat.type != 'private':
        await message.delete()
        return
    await state.finish()
    keyboard = await group_keyboard(message.chat.id, 'unwarn')
    await message.answer('Выберите группу:', reply_markup=keyboard)


@dp.message_handler(lambda m: m.text == 'Купить VIP', state='*')
async def vip(message: types.Message, state=FSMContext):
    if message.chat.type != 'private':
        await message.delete()
        return
    await state.finish()
    if utils.get_money(message.from_user.id) >= 300:
        await buy(message.from_user.id, 300)
        dates = datetime.datetime.now() + datetime.timedelta(days=30)
        vip = VIP(until_date=dates.strftime('%Y-%m-%d %H:%M:%S'), user_id=message.from_user.id)
        session.add(vip)
        session.commit()
        await message.answer('Вы приобрели VIP\n /start что бы вернутся', reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer('Недостаточно средств')


@dp.message_handler(lambda m: m.text == 'VIP RP команда', state='*')
async def vip_rp(message: types.Message, state=FSMContext):
    if message.chat.type != 'private':
        await message.delete()
        return
    await state.finish()
    await Tagall.rp.set()
    if utils.check_vip(message.from_user.id):
        rp_user = utils.get_user_rp(message.from_user.id)
        text = f'У Вас уже создано {len(rp_user)} команд:\n'
        for com in rp_user:
            text += f'<code>{com.com}</code> '
        msg = await message.answer(text)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('Пример в чате', callback_data='rp_show'))
        keyboard.add(types.InlineKeyboardButton('Удалить записи', callback_data='rp_delete'))
        m = await message.answer('Для создание своей команды в чате пришлите сообщение в формате:\n'
                             'смайл|команда|действие. Например 🤗|обнять|обнял.\n', reply_markup=keyboard)
        state = Dispatcher.get_current().current_state()
        await state.update_data(message_id=m.message_id)
        await asyncio.create_task(delete_message(msg, 5))


@dp.message_handler(lambda m: '|' in m.text, state=Tagall.rp)
async def rp_commands(message: types.Message, state=FSMContext):
    if message.chat.type != 'private':
        return
    text = message.text.split('|')
    data = await state.get_data()
    if len(text) == 3:
        smile, command, desc = text
        await state.update_data(prefix=smile, com=command.lower(), desc=desc)
        text = f'Ваша команда выглядит так:\n {smile}|@yourname {desc} @someuser'
    elif len(text) == 4:
        smile, command, desc, postfix = text
        await state.update_data(prefix=smile, com=command.lower(), desc=desc, postfix=postfix)
        text = f'Ваша команда выглядит так:\n {smile}|@yourname {desc} @someuser {postfix}'
    else:
        await message.answer('Что то не так, вернитесь в начало командой /start')
        return
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Сохранить', callback_data='rp_ok'))
    keyboard.add(types.InlineKeyboardButton('Изменить', callback_data=f'rp_cancel_{command}'))
    try:
        await bot.edit_message_text(text, message.from_user.id, data['message_id'], reply_markup=keyboard)
    except MessageCantBeEdited:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('Пример в чате', callback_data='rp_show'))
        await message.delete()
        await message.answer('Для создание своей команды в чате пришлите сообщение в формате:\n'
                                            'смайл|команда|действие. Например 🤗|обнять|обнял.\n',
                                            reply_markup=keyboard)


def keyboard_rp(user_id):
    rp_user = utils.get_user_rp(user_id)
    buttons = []
    for com in rp_user:
        buttons.append(types.InlineKeyboardButton(f'{com.id} -{com.com} - {com.desc}', callback_data=f'rpdel_{com.id}'))
    keyboard = types.InlineKeyboardMarkup(row_width=1).add(*buttons)
    keyboard.add(types.InlineKeyboardButton(f'Закрыть', callback_data=f'rpdel_close'))
    return keyboard


@dp.callback_query_handler(lambda m: 'rp_' in m.data, state=Tagall.rp)
async def rp_call(callback_query: types.CallbackQuery, state=FSMContext):
    if 'show' in callback_query.data:
        await callback_query.answer('🤗|yourname обнял somename', show_alert=True)
    if 'ok' in callback_query.data:
        user_data = await state.get_data()
        rp = RPContext(
            com=user_data['com'],
            desc=user_data['desc'],
            prefix=user_data['prefix'],
            until_date=user_data.get('postfix', '0'),
            user_id=callback_query.from_user.id
        )
        await state.finish()
        session.add(rp)
        session.commit()
        await callback_query.answer('Ваша команда успешно сохранена.', show_alert=True)
        await callback_query.message.delete()
        keyboard = types.ReplyKeyboardMarkup().add(types.KeyboardButton('VIP RP команда'))
        await callback_query.message.answer('Введите /start что бы вернутся к началу или нажмите кнопку для создания команды.', reply_markup=keyboard)
    if 'cancel' in callback_query.data:
        await state.finish()
        await Tagall.rp.set()
        await bot.answer_callback_query(callback_query.id)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('Пример в чате', callback_data='rp_show'))
        await callback_query.message.delete()
        m = await callback_query.message.answer('Для создание своей команды в чате пришлите сообщение в формате:\n'
                             'смайл|команда|действие. Например 🤗|обнять|обнял.\n', reply_markup=keyboard)
        state = Dispatcher.get_current().current_state()
        await state.update_data(message_id=m.message_id)
    if 'delete' in callback_query.data:
        await bot.answer_callback_query(callback_query.id)
        await callback_query.message.delete()
        await callback_query.message.answer('Выберите команду:', reply_markup=keyboard_rp(callback_query.from_user.id))



@dp.callback_query_handler(lambda m: 'rpdel_' in m.data, state=Tagall.rp)
async def rp_delete(callback_query: types.CallbackQuery, state=FSMContext):
    if callback_query.data.split('_')[-1] == 'close':
        await state.finish()
        await callback_query.message.delete()
        return
    rp_com = utils.get_rp_by_id(callback_query.data.split('_')[-1])
    session.delete(rp_com)
    session.commit()
    await callback_query.answer('Удалено.')
    await callback_query.message.delete()
    await callback_query.message.answer('Выберите команду:', reply_markup=keyboard_rp(callback_query.from_user.id))


@dp.message_handler(lambda m: m.text == 'Купить префикс', state='*')
async def prefix(message: types.Message, state=FSMContext):
    if message.chat.type != 'private':
        await message.delete()
        return
    await state.finish()
    await Tagall.prefix.set()
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton('На 3 дня, 50 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮', callback_data='3day'),
               types.InlineKeyboardButton('На неделю, 100 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮', callback_data='week')]
    keyboard.add(*buttons)
    await message.answer('Выберите период:', reply_markup=keyboard)


async def group_keyboard(user_id, command):
    groups = utils.get_groups()
    buttons = []
    for group in groups:
        if utils.user_exists(group.group_id, user_id):
            if command == 'prefix':
                buttons.append(types.InlineKeyboardButton(group.title, callback_data=f'p{group.group_id}'))
            elif command == 'unban':
                buttons.append(types.InlineKeyboardButton(group.title, callback_data=f'b{group.group_id}'))
            else:
                buttons.append(types.InlineKeyboardButton(group.title, callback_data=f'w{group.group_id}'))
    return types.InlineKeyboardMarkup(row_width=2).add(*buttons)


@dp.callback_query_handler(lambda m: m.data in ['3day', 'week'], state=Tagall.prefix)
async def prefix_buy(callback_query: types.CallbackQuery, state=FSMContext):
    try:
        await bot.answer_callback_query(callback_query.id)
        if callback_query.data == '3day':
            await state.update_data(price=50, period=3)
        else:
            await state.update_data(price=100, period=7)
        keyboard = await group_keyboard(callback_query.message.chat.id, command='prefix')
        await callback_query.message.answer('Выберите группу:', reply_markup=keyboard)
    except Exception as e:
        await state.finish()
        logging.info(
            f'{callback_query.message.text} - {callback_query.message.chat.id} - {callback_query.message.from_user.id}',
            exc_info=e)
    finally:
        await callback_query.message.delete()


@dp.callback_query_handler(lambda m: m.data.startswith('b-100'))
async def unban_cash(callback_query: types.CallbackQuery):
    chat_id = callback_query.data[1:]
    try:
        if utils.get_money(callback_query.from_user.id) >= 200:
            await buy(callback_query.from_user.id, 200)
            user = utils.get_user(chat_id, callback_query.from_user.id)
            user.ban = 0
            session.commit()
            await bot.unban_chat_member(chat_id, callback_query.from_user.id)
            await callback_query.message.answer('Успешно!\n /start что бы вернутся', reply_markup=types.ReplyKeyboardRemove())
            await info_message(
                'Покупка разбана',
                callback_query.message.chat.title,
                callback_query.message.chat.id,
                callback_query.message.from_user.first_name,
                callback_query.message.from_user.id,
                None,
                None,
                callback_query.message.from_user.username,
                None
            )
        else:
            await callback_query.message.answer('Недостаточно средств')
    except Exception as e:
        await callback_query.message.answer(f'{e}')


@dp.callback_query_handler(lambda m: m.data.startswith('w-100'))
async def warn_cash(callback_query: types.CallbackQuery):
    chat_id = callback_query.data[1:]
    try:
        if utils.get_money(callback_query.from_user.id) >= 150:
            await buy(callback_query.from_user.id, 150)
            user = utils.get_user(chat_id, callback_query.from_user.id)
            user.mute = 0
            session.commit()
            await callback_query.message.answer(f'Успешно!\n /start что бы вернутся', reply_markup=types.ReplyKeyboardRemove())
            await info_message(
                'Покупка разварна',
                callback_query.message.chat.title,
                callback_query.message.chat.id,
                callback_query.message.from_user.first_name,
                callback_query.message.from_user.id,
                None,
                None,
                callback_query.message.from_user.username,
                None
            )
        else:
            await callback_query.message.answer('Недостаточно средств')
    except Exception as e:
        await callback_query.message.answer(f'{e}')


@dp.callback_query_handler(lambda m: m.data.startswith('p-100'), state=Tagall.prefix)
async def set_group(callback_query: types.CallbackQuery, state=FSMContext):
    await bot.answer_callback_query(callback_query.id)
    try:
        chat_id = callback_query.data[1:]
        msg = await bot.get_chat_administrators(chat_id)
        if len(msg) >= 50:
            m = await callback_query.message.answer(f'Количество пользователей с префиксом: {len(msg)}\n Максимальное количество - 50')
            asyncio.create_task(delete_message(m, 5))
        user_data = await state.get_data()
        await state.update_data(group=chat_id)
        if utils.get_money(callback_query.from_user.id) >= user_data['price']:
            await callback_query.message.answer('Введите желаемый префикс, не превышающий 16 символов.\n'
                                                'За оскорбительный префикс вы получите бан!')
        else:
            await callback_query.message.answer('Недостаточно средств!')
    except Exception as e:
        logging.info(
            f'{callback_query.message.text} - {callback_query.message.chat.id} - {callback_query.message.from_user.id}',
            exc_info=e)
    finally:
        await callback_query.message.delete()


async def buy(user_id, price):
    groups = utils.get_groups()
    for group in groups:
        if utils.user_exists(group.group_id, user_id):
            user = utils.get_user(group.group_id, user_id)
            if user.cash >= price:
                user.cash -= price
                session.commit()
                break
            price -= user.cash
            user.cash -= price
            session.commit()


@dp.message_handler(commands=['money'])
async def money_user(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    if utils.salent(message.chat.id):
        return
    user = utils.get_user(message.chat.id, message.from_user.id)
    cash = utils.get_money(message.from_user.id)
    text = f'Баланс в {message.chat.title}: {user.cash} 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n\nБаланс в сети: {cash} 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n'
    mention = await mention_text(message.from_user.first_name, message.from_user.id)
    if cash <= 0:
        answer = [', нас ограбили, милорд!', ', нужно больше золота!!', 'нашу казну поел долгоносик, милорд!', ', вот бы скинулись бы все Китайцы по 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮']
        text += f'{fmt.hlink(*mention)}{random.choice(answer)}'
    elif cash == 50:
        text += f'{fmt.hlink(*mention)} уже можно купить преф на 3 дня!'
    elif cash == 100:
        text += f'{fmt.hlink(*mention)} уже можно купить преф на 7 дней!'
    elif cash == 150:
        text += f'{fmt.hlink(*mention)} можно снять с себя все наказания!'
    elif cash == 200:
        text += f'{fmt.hlink(*mention)}, если забанят, есть шанс разбана!'
    elif cash == 300:
        text += f'{fmt.hlink(*mention)}, пора за VIP-ом!'
    elif cash <= 100:
        answer = [', можно не экономить на себе! Чебурек на все!!!',
                  ', эх, еще пару 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮 и заживем!',
                  ', с такими средствами можно и инвестировать! В еду...',
                  ', говорила мама, ищи хорошую работу...',
                  ', копим на мечту']
        text += f'{fmt.hlink(*mention)}{random.choice(answer)}'
    elif cash <= 1000:
        answer = [', ещё подкопить и на Канары...', ', ешь ананасы, рябчиков жуй!', ', пора ехать тратить на себя.']
        text += f'{fmt.hlink(*mention)}{random.choice(answer)}'
    else:
        answer = [', такое состояние никому нельзя показывать!',
                  ', Лос Анжелес ждет! Все на дабл зеро!',
                  ', слетать в космос или купить себе еще один остров?...',
                  ', "... царевич там над златом чахнет..."',
                  ', Вы заняли первое место в рейтинге самых успешных людей!']
        text += f'{fmt.hlink(*mention)}{random.choice(answer)}'
    await message.answer(text)
    await info_message(
        'money',
        message.chat.title,
        message.chat.id,
        message.from_user.first_name,
        message.from_user.id,
        None,
        None,
        message.from_user.username,
        None
    )


@dp.message_handler(state=Tagall.prefix)
async def prefix_sets(message: types.Message, state=FSMContext):
    if message.chat.type != 'private':
        return
    user_data = await state.get_data()
    await state.finish()
    try:
        if len(message.text) > 16:
            await message.answer('Слишком длинный префикс! Введите не более 16 символов!')
        elif message.text in config.WORDS:
            await message.answer('Префикс содержит запрещенные слова! Попробуйте снова!')
        else:
            await bot.promote_chat_member(
                user_data['group'],
                message.from_user.id,
                can_manage_chat=True
            )
            await asyncio.sleep(1)
            await bot.set_chat_administrator_custom_title(user_data['group'], message.from_user.id, custom_title=message.text)
            await buy(message.chat.id, user_data['price'])
            user = utils.get_user(user_data['group'], message.from_user.id)
            dates = (datetime.datetime.now() + datetime.timedelta(days=user_data['period'])).strftime('%Y-%m-%d %H:%M:%S')
            user.prefix_off = dates
            await message.answer(f'Вам установлен префикс <b>{message.text}</b>\n Дата окончания: {dates}\n /start что бы вернутся', reply_markup=types.ReplyKeyboardRemove())
            await info_message(
                'Покупка префикса',
                message.chat.title,
                message.chat.id,
                message.from_user.first_name,
                message.from_user.id,
                None,
                None,
                message.from_user.username,
                None
            )
    except Exception as e:
        await bot.promote_chat_member(
            user_data['chat_id'],
            message.from_user.id,
            can_manage_chat=False
        )
        await message.answer(f'{e}')
        logging.info(f'{message.text} - {message.chat.id} - {message.from_user.id}', exc_info=e)
    finally:
        await state.finish()
        await message.delete()


@dp.message_handler(lambda m: m.text == 'Купить 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮')
async def coins(message: types.Message):
    owners = utils.all_owner()
    text = ''
    for owner in owners:
        mention = await mention_text('Владелец', owner.owner_id)
        text += f'{fmt.hlink(*mention)}\n'
    await message.answer(f'Для покупки 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮 свяжитесь с\n{text}\n /start что бы вернутся', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands=['снять'])
async def down(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    try:
        chat_id = message.chat.id
        big_owner = is_big_owner(message.from_user.id)
        owner = is_owner(message.from_user.id)
        admin = is_admin(message.chat.id, message.from_user.id)
        moder = is_moder(message.chat.id, message.from_user.id)
        if not any([big_owner, owner, admin, moder]):
            return
        user_id, first_name, username = await ent(message)
        mention = await mention_text(first_name, user_id)
        await bot.promote_chat_member(
            chat_id,
            user_id
        )
        await message.answer(f'{fmt.hlink(*mention)}, вы сняты с должности.')
    except Exception as e:
        logging.info(f'{message.text} - {message.chat.id} - {message.from_user.id}', exc_info=e)


@dp.message_handler(commands='prefix')
async def prefix(message: types.Message):
    await try_delete(message)
    if message.chat.type == 'private':
        return
    try:
        text = message.text.split()
        chat_id = message.chat.id
        big_owner = is_big_owner(message.from_user.id)
        owner = is_owner(message.from_user.id)
        admin = is_admin(message.chat.id, message.from_user.id)
        moder = is_moder(message.chat.id, message.from_user.id)
        if not any([big_owner, owner, admin, moder]):
            return
        user_id, first_name, username = await ent(message)
        mention = await mention_text(first_name, user_id)
        await bot.promote_chat_member(
            chat_id,
            user_id
        )
        await message.answer(f'{fmt.hlink(*mention)}, Вам удален префикс!.\nПричина: {text[-1]}.')
        await info_message(
            'delete prefix',
            message.chat.title,
            message.chat.id,
            message.from_user.first_name,
            message.from_user.id,
            first_name,
            user_id,
            message.from_user.username,
            username
        )
    except Exception as e:
        logging.info(f'{message.text} - {message.chat.id} - {message.from_user.id}', exc_info=e)


async def check_url(message):
    if not message.entities:
        return
    chat_id = message.chat.id
    from_id = message.from_user.id
    for entity in message.entities:
        if entity.type in ['url', 'text_link']:
            if not any([
                is_big_owner(from_id),
                is_owner(from_id),
                is_admin(chat_id, from_id),
                is_moder(chat_id, from_id)
            ]):
                if not utils.banned_exists(message.from_user.id):
                    baned = Banned(user_id=message.from_user.id, desc='Добавлен в черный список')
                    session.add(baned)
                    session.commit()
                for group in utils.get_groups():
                    mention = await mention_text(message.from_user.first_name, message.from_user.id)
                    if utils.user_exists(group.group_id, message.from_user.id):
                        await bot.ban_chat_member(group.group_id, message.from_user.id)
                        await bot.send_message(group.group_id,
                                               f'Пользователь {fmt.hlink(*mention)} забанен.\nПричина: Рекламные ссылки.')
                        await info_message(
                            'Бан за рекламные ссылки',
                            message.chat.title,
                            message.chat.id,
                            dict(await bot.get_me()).get('first_name'),
                            dict(await bot.get_me()).get('id'),
                            message.from_user.first_name,
                            message.from_user.id,
                            dict(await bot.get_me()).get('username'),
                            message.from_user.username
                        )
            await try_delete(message)


async def lottery_result(message):
    if utils.serial_exists(message.chat.id):
        if not utils.user_lottery(message.chat.id, message.from_user.id):
            victim = Killer(user_id=message.from_user.id, first_name=message.from_user.first_name, chat_id=message.chat.id)
            session.add(victim)
        if utils.stop_victim(message.chat.id):
            users_lottery = utils.get_killer(message.chat.id)
            session.query(Killer).filter(Killer.chat_id == message.chat.id).delete()
            session.commit()
            if utils.lottery_exists(message.chat.id):
                group = utils.get_group(message.chat.id)
                group.lottery = 0
                session.commit()
                text = 'Участники:\n'
                c = 1
                for user_lottery in users_lottery:
                    mention = await mention_text(user_lottery.first_name, user_lottery.user_id)
                    text += fmt.text(c, ') ', fmt.hlink(*mention), '\n')
                    c += 1
                await message.answer(text)
                await message.answer('Выбираем победителей!')
                await asyncio.sleep(10)
                if len(users_lottery) >= 5:
                    x = 5
                else:
                    x = len(users_lottery)
                users_random = random.sample(users_lottery, k=x)
                text = 'Поздравляем победителей:\n'
                for user_random in users_random:
                    user = utils.get_user(message.chat.id, user_random.user_id)
                    user.cash += 3
                    mention = await mention_text(user_random.first_name, user_random.user_id)
                    text += fmt.text(fmt.hlink(*mention), ' - 3 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n')
            else:
                user_random = random.choice(users_lottery)
                user = utils.get_user(message.chat.id, user_random.user_id)
                mention = await mention_text(user_random.first_name, user_random.user_id)
                item = random.choice(box)
                text = fmt.text(fmt.hlink(*mention), f'к вам прибыл курьер и доставил вам посылку. Никто не знает что внутри.\nВы аккуратно вскрываете ее и вам достается - {item}\n')
                items = user.items
                if items == '0':
                    items = f'{item}:1'
                else:
                    items = [x.split(':') for x in [item for item in items.split(',')]]
                    items_to_dict = {x: int(y) for x, y in items}
                    items_to_dict[item] = int(items_to_dict.get(item, 0)) + 1
                    items = ','.join([f'{k}:{v}' for k, v in items_to_dict.items()])
                user.items = items
            await message.answer(text)


async def prefix_check(message):
    users = utils.get_users_prefix(message.chat.id)
    chat_id = message.chat.id
    from_id = message.from_user.id
    for user in users:
        if utils.delete_prefix(message.chat.id, user.user_id) and not any([
            is_big_owner(from_id),
            is_owner(from_id),
            is_admin(chat_id, from_id),
            is_moder(chat_id, from_id)
        ]):
            mention = await mention_text(user.first_name, user.user_id)
            await message.answer(f'{fmt.hlink(*mention)}, срок префикса истек!')
            await bot.promote_chat_member(
                chat_id,
                user.user_id
            )
            await info_message(
                'Удаление префикса',
                message.chat.title,
                message.chat.id,
                dict(await bot.get_me()).get('first_name'),
                dict(await bot.get_me()).get('id'),
                user.first_name,
                user.user_id,
                dict(await bot.get_me()).get('username'),
                user.username
            )


@dp.message_handler()
async def mess_handler(message: types.Message):
    if not message.chat.id in [int(group.group_id) for group in utils.get_groups()]:
        return
    text = message.text
    chat_id = message.chat.id
    from_id = message.from_user.id
    if not utils.user_exists(chat_id, from_id):
        user = FlameNet(
            chat_id=chat_id,
            user_id=from_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            is_active=1,
            create_time=datetime.date.today(),
            first_message=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        session.add(user)
        session.commit()
    user = utils.get_user(chat_id, from_id)
    user.last_message = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not user.count_message:
        user.first_message = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user.username = message.from_user.username
    user.first_name = message.from_user.first_name
    user.karma += 1
    user.role, user.exp = utils.exp(user.exp, user.count_message)
    user.count_message += 1
    user.message = text
    user.message_id = message.message_id
    user.is_active = 1
    session.commit()

    mention = await mention_text(message.from_user.first_name, message.from_user.id)
    if utils.get_vip(message.from_user.id):
        await message.answer(fmt.text(fmt.hlink(*mention), 'Время действия VIP истек!'))

    await lottery_result(message)
    await check_url(message)
    await prefix_check(message)


async def log_send(text):
    setting = utils.get_setting()
    await bot.send_message(setting.id_group_log, text, parse_mode=None)


@dp.errors_handler(exception=exceptions.UserIsAnAdministratorOfTheChat)
async def bot_blocked_admin_chat(update: types.Update, exception: exceptions.UserIsAnAdministratorOfTheChat):
    text = fmt.text('Группа: ',
                    update.message.chat.title or update.message.chat.first_name,
                    ' - инициатор: ',
                    fmt.hlink(*await mention_text(update.message.from_user.first_name, update.message.from_user.id)),
                    ' -  текст сообщения: ',
                    update.message.text,
                    ' - Ошибка: ',
                    exception)
    await log_send(text)


@dp.errors_handler(exception=exceptions.MessageToDeleteNotFound)
async def bot_not_found_message(update: types.Update, exception: exceptions.MessageToDeleteNotFound):
    text = fmt.text('Группа: ',
                    update.message.chat.title or update.message.chat.first_name,
                    ' - инициатор: ',
                    fmt.hlink(*await mention_text(update.message.from_user.first_name, update.message.from_user.id)),
                    ' -  текст сообщения: ',
                    update.message.text,
                    ' - Ошибка: ',
                    exception)
    await log_send(text)


@dp.errors_handler(exception=exceptions.MessageCantBeDeleted)
async def bot_message_delete(update: types.Update, exception: exceptions.MessageCantBeDeleted):
    text = fmt.text('Группа: ',
                    update.message.chat.title or update.message.chat.first_name,
                    ' - инициатор: ',
                    fmt.hlink(*await mention_text(update.message.from_user.first_name, update.message.from_user.id)),
                    ' -  текст сообщения: ',
                    update.message.text,
                    ' - Ошибка: ',
                    exception)
    await log_send(text)


@dp.errors_handler(exception=exceptions.ChatAdminRequired)
async def bot_blocked_admin_required(update: types.Update, exception: exceptions.ChatAdminRequired):
    text = fmt.text('Группа: ',
                    update.message.chat.title or update.message.chat.first_name,
                    ' - инициатор: ',
                    fmt.hlink(*await mention_text(update.message.from_user.first_name, update.message.from_user.id)),
                    ' -  текст сообщения: ',
                    update.message.text,
                    ' - Ошибка: ',
                    exception)
    await log_send(text)


@dp.errors_handler(exception=exceptions.NotEnoughRightsToRestrict)
async def bot_no_enough_rights(update: types.Update, exception: exceptions.NotEnoughRightsToRestrict):
    text = fmt.text('Группа: ',
                    update.message.chat.title or update.message.chat.first_name,
                    ' - инициатор: ',
                    fmt.hlink(*await mention_text(update.message.from_user.first_name, update.message.from_user.id)),
                    ' -  текст сообщения: ',
                    update.message.text,
                    ' - Ошибка: ',
                    exception)
    await log_send(text)


@dp.errors_handler(exception=sqlite3.OperationalError)
async def bot_sqlite(update: types.Update, exception: sqlite3.OperationalError):
    text = fmt.text('Группа: ',
                    update.message.chat.title or update.message.chat.first_name,
                    ' - инициатор: ',
                    fmt.hlink(*await mention_text(update.message.from_user.first_name, update.message.from_user.id)),
                    ' -  текст сообщения: ',
                    update.message.text,
                    ' - Ошибка: ',
                    exception)
    await log_send(text)


@dp.errors_handler(exception=exceptions.UserIsAnAdministratorOfTheChat)
async def bot_sqlite(update: types.Update, exception: exceptions.UserIsAnAdministratorOfTheChat):
    text = fmt.text('Группа: ',
                    update.message.chat.title or update.message.chat.first_name,
                    ' - инициатор: ',
                    fmt.hlink(*await mention_text(update.message.from_user.first_name, update.message.from_user.id)),
                    ' -  текст сообщения: ',
                    update.message.text,
                    ' - Ошибка: ',
                    exception)
    await update.message.answer('Нельзя ограничить администратора чата!')
    await log_send(text)


@dp.errors_handler(exception=exceptions.BotKicked)
async def bot_bad_request(update: types.Update, exception: exceptions.BotKicked):
    text = fmt.text('Группа: ',
                    update.message.chat.title or update.message.chat.first_name,
                    ' - инициатор: ',
                    fmt.hlink(*await mention_text(update.message.from_user.first_name, update.message.from_user.id)),
                    ' -  текст сообщения: ',
                    update.message.text,
                    ' - Ошибка: ',
                    exception)
    await log_send(text)


@dp.errors_handler(exception=exceptions.BadRequest)
async def bot_bad_request(update: types.Update, exception: exceptions.BadRequest):
    message = update.message or update.callback_query.message
    text = fmt.text('Группа: ',
                    message.chat.title or update.message.chat.first_name,
                    ' - инициатор: ',
                    fmt.hlink(*await mention_text(message.from_user.first_name, message.from_user.id)),
                    ' -  текст сообщения: ',
                    message.text,
                    ' - Ошибка: ',
                    exception)
    await log_send(text)


@dp.errors_handler(exception=TypeError)
async def bot_type_error(update: types.Update, exception: TypeError):
    text = fmt.text('Группа: ',
                    update.message.chat.title or update.message.chat.first_name,
                    ' - инициатор: ',
                    fmt.hlink(*await mention_text(update.message.from_user.first_name, update.message.from_user.id)),
                    ' -  текст сообщения: ',
                    update.message.text,
                    ' - Ошибка: ',
                    exception,
                    update)
    await log_send(text)


@dp.errors_handler(exception=ValueError)
async def bot_value_error(update: types.Update, exception: ValueError):
    text = fmt.text('Группа: ',
                    update.message.chat.title or update.message.chat.first_name,
                    ' - инициатор: ',
                    fmt.hlink(*await mention_text(update.message.from_user.first_name, update.message.from_user.id)),
                    ' -  текст сообщения: ',
                    update.message.text,
                    ' - Ошибка: ',
                    exception,
                    update)
    await log_send(text)


@dp.errors_handler(exception=IndexError)
async def bot_index_error(update: types.Update, exception: IndexError):
    text = fmt.text('Группа: ',
                    update.message.chat.title or update.message.chat.first_name,
                    ' - инициатор: ',
                    fmt.hlink(*await mention_text(update.message.from_user.first_name, update.message.from_user.id)),
                    ' -  текст сообщения: ',
                    update.message.text,
                    ' - Ошибка: ',
                    exception)
    await log_send(text)


if __name__ == "__main__":
    DICT_COMMANDS = {
        'owner': add_owner,
        'admin': admin_up,
        'moder': moder_up,
        'down': downgrade,
        'banned': banned,
        'ban': ban_group,
        'unbanned': unbanned,
        'unban': unban_group,
        'userrp': user_rp
    }

    executor.start_polling(dp, skip_updates=True)
    asyncio.create_task(client.run_until_disconnected())

