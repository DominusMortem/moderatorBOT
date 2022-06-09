import asyncio
from contextlib import suppress
import logging
import re
import time
import datetime

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import (MessageCantBeDeleted, MessageToDeleteNotFound)
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

import config
from database import Database
from utils import time_check, wedding_date_now

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()

db = Database('database.db')
bot = Bot(token=config.TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=storage)


class Reg(StatesGroup):
    period = State()
    group_id = State()


TIMECHECK = {'м': 60,
             'm': 60,
             'h': 3600,
             'ч': 3600}

PERSON_ONE = [0, 0]
PERSON_TWO = [0, 0]
GROUP = {}
short_commands = ['обнять', 'казнить', 'побить', 'любовь', 'недоверие', 'тусить']


async def delete_message(message: types.Message, sleep_time: int = 0):
    await asyncio.sleep(sleep_time)
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await message.delete()


async def mention_text(first_name, user_id):
    return f'<a href = "tg://user?id={user_id}">{first_name}</a>'


async def ent(message: types.Message):
    ents = [entity for entity in message.entities if entity.type == 'text_mention']
    if ents:
        first_name = ents[0].user.first_name
        user_id = ents[0].user.id
    else:
        username = message.text.split()[1]
        user_id, first_name = db.get_user(message.chat.id, username[1:])
    return user_id, first_name


async def downgrade(user_id, chat_id, mention, role=0, user=0):
    print(user_id, user)
    is_owner = db.get_owner(user_id)
    is_admin = db.get_admin(chat_id, user_id)
    is_moder = db.get_moder(chat_id, user_id)
    if role == 0:
        if is_owner:
            for group in db.all_group():
                if db.user_exists(group[0], user_id):
                    await admin_private(user_id, group[0], mention, 1)
            return 'Понижено!'
        elif is_admin:
            db.set_admin(chat_id, user_id, 0)
            db.set_moder(chat_id, user_id, 1)
            await moder_private(user_id, chat_id, mention, 1)
            return 'Понижено!'
        elif is_moder:
            db.set_moder(chat_id, user_id, 0)
            await moder_private(user_id, chat_id, mention, 0)
            return 'Понижено!'
        else:
            return 'Недостаточно прав!'


async def admin_private(user_id, chat_id, mention, admin=0, user=0):
    db.delete_owner(user_id)
    db.set_admin(chat_id, user_id, admin)
    db.set_moder(chat_id, user_id, 0)
    if admin == 1:
        await bot.promote_chat_member(
            chat_id,
            user_id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_restrict_members=True
        )
        time.sleep(1)
        await bot.set_chat_administrator_custom_title(chat_id, user_id, custom_title='Администратор')
        await bot.send_message(chat_id, f'Пользователь {mention} назначен администратором сообщества.')
        return 'Назначение успешно!'
    else:
        await bot.promote_chat_member(
            chat_id, user_id
        )
        await bot.send_message(chat_id, f'Пользователь {mention} снят с должности администратора.')
        return 'Снят с должности!'


async def moder_private(user_id, chat_id, mention, moder=0, user=0):
    db.set_moder(chat_id, user_id, moder)
    db.set_admin(chat_id, user_id, 0)
    if moder == 1:
        await bot.promote_chat_member(
            chat_id,
            user_id,
            can_manage_chat=True
        )
        time.sleep(1)
        await bot.set_chat_administrator_custom_title(chat_id, user_id, custom_title='Модератор')
        await bot.send_message(chat_id, f'Пользователь {mention} назначен модератором сообщества.')
        return 'Назначение успешно!'
    else:
        await bot.promote_chat_member(
            chat_id, user_id
        )
        await bot.send_message(chat_id, f'Пользователь {mention} снят с должности модератора.')
        return 'Назначение не выполнено!'


async def ban_group(user_id, chat_id, mention, ban=0, user=0):
    db.add_ban(chat_id, user_id, ban)
    if not ban:
        await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
        await bot.send_message(chat_id, f'Пользователь {mention} разбанен.')
        return 'Пользователь разбанен!'
    else:
        await bot.ban_chat_member(chat_id, user_id)
        await bot.send_message(chat_id, f'Пользователь {mention} забанен.\nПричина: Систематические нарушения правил.')
        return 'Пользователь забанен!'


async def add_owner(user_id, chat_id, mention, owner=0, user=0):
    if user != config.ADMIN_ID:
        return 'Недостаточно прав!'
    if not db.get_owner(user_id):
        db.set_owner(user_id)

    for group in db.all_group():
        group_id = int(group[0])
        if db.user_exists(group_id, user_id):
            db.set_admin(group_id, user_id, 0)
            db.set_moder(group_id, user_id, 0)
            await bot.promote_chat_member(
                group_id,
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
            time.sleep(1)
            await bot.set_chat_administrator_custom_title(group_id, user_id, custom_title='Совладелец')
            await bot.send_message(group_id, f'<b>Пользователь {mention} назначен совладельцем сети!</b>')
    return 'Назначение успешно!'


async def add_banned(user_id, chat_id, mention, banned=0, user=0):
    if not db.get_banned(user_id):
        db.set_banned(user_id)
    for group in db.all_group():
        group_id = int(group[0])
        if db.user_exists(group_id, user_id):
            await bot.ban_chat_member(group_id, user_id)
            await bot.send_message(group_id, f'Пользователь {mention} забанен.\nПричина: Систематические нарушения правил.')
        if banned:
            db.delete_banned(user_id)
            await bot.unban_chat_member(group_id, user_id)
            await bot.send_message(group_id,
                                   f'Пользователь {mention} разбанен.\n')
    return 'Успешно!'


async def info_message(
        command,
        chat_title,
        chat_id,
        first_name,
        user_id,
        to_first_name,
        to_user_id,
        username = None,
        to_username = None
        ):
    text = (f'#{command}\n\n'
            f'Группа: {chat_title}\n'
            f'[#chat{str(chat_id)[1:]}]\n'
            f'Инициатор: {first_name} [{username or "Не задано"}]\n'
            f'[#user{user_id}]\n'
            f'Пользователь: {to_first_name} [{to_username  or "Не задано"}]\n'
            f'[#user{to_user_id}]\n'
            f'Время: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    group_id = db.get_group_message()
    await bot.send_message(group_id[0], text)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.chat.type == 'private':
        buttons = ['Купить разбан',
                   'Купить разварн',
                   'Купить префикс',
                   'Купить 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮']
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*buttons)
        await message.answer('Добро пожаловать!\n'
                             'Выберите пункт в меню:', reply_markup=keyboard)
    else:
        await message.delete()
        return


@dp.message_handler(commands=['браки'])
async def get_pair(message: types.Message):
    dict_pair = {}
    try:
        pairs = db.get_pair(message.chat.id)
        if pairs:
            for pair in pairs:
                if pair[2] != '0':
                    user_id = str(pair[0])
                    first_name = pair[1]
                    wend = pair[2]
                    wedding_time = datetime.datetime.strptime(pair[3], "%Y-%m-%d %H:%M:%S")
                    wedding_id = pair[2].split('id=')[1].split('"')[0]
                    if wedding_id not in dict_pair:
                        dict_pair[user_id] = (wend, first_name, wedding_time)
            if dict_pair:
                text = 'Пары в группе:\n'
            else:
                text = 'Людей на планете осталось так мало, что последний ЗАГС заколотил двери...'
            for k, v in dict_pair.items():
                mention = await mention_text(v[1], k)
                day_wending = (datetime.datetime.now() - v[2]).total_seconds()
                text += f'{mention} и {v[0]} в браке: {wedding_date_now(day_wending)}.\n'
            await message.answer(f'{text}')
    except Exception as e:
        logging.info(e)
    finally:
        await message.delete()


@dp.message_handler(commands=['свадьба'])
async def wedding(message: types.Message):
    try:
        text = message.text.split()
        if len(text) == 1:
            if not message.reply_to_message:
                await message.reply('Эта команда должна быть ответом на сообщение!')
                return
            user_id = message.reply_to_message.from_user.id
            first_name = message.reply_to_message.from_user.first_name
        else:
            user_id, first_name = await ent(message)
        mention = await mention_text(first_name, user_id)
        mention_one = await mention_text(message.from_user.first_name, message.from_user.id)
        keyboard = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton('Согласиться', callback_data='YES'), types.InlineKeyboardButton('Отказать', callback_data='NO')]
        keyboard.add(*buttons)
        print(message.from_user.first_name, message.from_user.id, first_name, user_id)
        db.delete_constant(message.from_user.id)
        db.delete_constant(user_id)
        db.wedding_constaint(message.chat.id, message.from_user.first_name, message.from_user.id, first_name, user_id)
        person_one_not_wending = db.get_wedding(message.chat.id, message.from_user.id)[0]
        person_two_not_wending = db.get_wedding(message.chat.id, user_id)[0]
        if person_one_not_wending == '0' and person_two_not_wending == '0':
            msg = await message.answer(f'💗{mention}, минуту внимания!\n'
                                 f'{mention_one} сделал(а) вам предложение руки и сердца.🥰', reply_markup=keyboard)
            asyncio.create_task(delete_message(msg, 120))
        else:
            if person_one_not_wending:
                msg = await message.answer(f'Увы, {mention_one}, вы уже в браке!' )
                asyncio.create_task(delete_message(msg, 3))
            if person_two_not_wending:
                msg = await message.answer(f'Увы, {mention}, уже состоит браке!')
                asyncio.create_task(delete_message(msg, 3))
        to_username = db.get_username(message.chat.id, user_id)[0]
        await info_message(
            'свадьба',
            message.chat.title,
            message.chat.id,
            message.from_user.first_name,
            message.from_user.id,
            first_name,
            user_id,
            message.from_user.username,
            to_username
        )
    except Exception as e:
        logging.info(e)
    finally:
        await message.delete()


@dp.message_handler(commands=['развод'])
async def no_marry(message: types.Message):
    wedding = db.get_wedding(message.chat.id, message.from_user.id)[0]
    if wedding != '0':
        mention = await mention_text(message.from_user.first_name, message.from_user.id)
        person_two = wedding.split('id=')[1].split('"')[0]
        db.wedding(message.chat.id, message.from_user.id, '0')
        db.wedding(message.chat.id, int(person_two), '0')
        msg = await message.answer(f'💔Сожалеем {wedding}, {mention} решил(а) разорвать отношения между вами.')
        asyncio.create_task(delete_message(msg, 10))
    await message.delete()


@dp.callback_query_handler(lambda m: m.data in ['YES', 'NO'])
async def wedding_answer(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    person_first_name, person_id, person_two_first_name, person_two_id = db.get_wedding_const(callback_query.from_user.id, callback_query.message.chat.id)
    mention_one = await mention_text(person_first_name, person_id)
    mention_two = await mention_text(person_two_first_name, person_two_id)
    if callback_query.from_user.id == person_two_id:
        if callback_query.data == 'YES':
            msg = await bot.send_message(callback_query.message.chat.id, f'💖Поздравляем молодожёнов!\n'
                                                                   f'{mention_one} и {mention_two} теперь в браке.💍')
            await callback_query.message.delete()
            asyncio.create_task(delete_message(msg, 20))
            db.wedding(callback_query.message.chat.id, person_id, mention_two)
            db.wedding(callback_query.message.chat.id, person_two_id, mention_one)
        if callback_query.data == 'NO':
            msg = await bot.send_message(callback_query.message.chat.id,
                                   f'{mention_one}, сожалею, {mention_two} вам отказал(а).💔')
            await callback_query.message.delete()
            asyncio.create_task(delete_message(msg, 20))



@dp.message_handler(commands=['info'])
async def info(message: types.Message):
    if not message.chat.type == 'private':
        try:
            if len(message.text.split()) >= 2:
                from_id = message.from_user.id
                chat_id = message.chat.id
                is_owner = db.get_owner(from_id)
                is_admin = db.get_admin(chat_id, from_id)
                is_moder = db.get_moder(chat_id, from_id)
                if not any([is_owner, is_admin, is_moder]) and config.ADMIN_ID != from_id:
                    return
                user_id, first_name = await ent(message)
                data = db.show_info(message.chat.id, user_id)
                mention = await mention_text(first_name, user_id)
            else:
                data = db.show_info(message.chat.id, message.from_user.id)
                mention = await mention_text(message.from_user.first_name, message.from_user.id)
                user_id = message.from_user.id
            if not data[6]:
                wedding = 'Не женат/Не замужем'
            else:
                wedding = data[6]

            text = (f'Никнейм: @{data[2] or "Не задано"}\n'
                    f'Профиль: {mention}\n'
                    f'Id: {user_id}\n\n'
                    f'Дата первого входа: {data[3]}\n'
                    f'Ранг: {data[16]}\n'
                    f'Семейное положение: {wedding}\n'
                    f'𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮: {data[14]}\n'
                    f'Первое сообщение: {data[4]}\n'
                    f'Последний бан: {data[8] or "Не было"}\n'
                    f'Последнее предупрежедние: {data[10] or "Не было"}\n'
                    f'Количество предупреждений: {data[11] or "Не было"}\n'
                    f'Время последнего сообщения: {data[5]}\n'
                    f'Количество сообщений: {data[17]}\n'
                    f'Опыт: {data[18]}\n'
                    f'Последнее ограничение: {data[12] or "Не было"}\n'
                    )
            await message.answer(text)
        except Exception as e:
            logging.info(e)
        finally:
            await message.delete()


@dp.message_handler(content_types=['new_chat_members']) # Вошел
async def user_joined(message: types.Message):
        if message.new_chat_members[0].username == 'gamemoder_bot':
            db.create_table(message.chat.id, message.chat.title)
            db.add_user(message.chat.id, message.from_user.id, message.from_user.username, message.from_user.first_name, 1)
        else:
            try:
                for user in message.new_chat_members:
                    mention = await mention_text(user.first_name, user.id)
                    if not db.user_exists(message.chat.id, message.from_user.id):
                        db.add_user(message.chat.id, user.id, user.username, user.first_name, 1)
                    else:
                        db.active(message.chat.id, user.id, 0)
                    if user.is_bot:
                        db.set_banned(user.id)
                        await bot.ban_chat_member(message.chat.id, user.id)
                        await message.answer(f'Пользователь {mention} забанен.\nПричина: Бот.')
                        return
                    await message.answer(f'Добро пожаловать {mention}!')
                    if db.get_owner(user.id):
                        await bot.promote_chat_member(
                            message.chat.id,
                            user.id,
                            can_manage_chat=True,
                            can_delete_messages=True,
                            can_restrict_members=True
                        )
                        await bot.set_chat_administrator_custom_title(message.chat.id, user.id, custom_title='Совладелец')
                        await message.answer(f'<b>Пользователь {mention} назначен совладельцем сети!</b>')
                    if db.get_banned(user.id):
                        await bot.ban_chat_member(message.chat.id, user.id)
                        await bot.send_message(
                            message.chat.id,
                            f'Пользователь {mention} забанен.\nПричина: Систематические нарушения правил.'
                        )
            except Exception as e:
                logging.info(e)
            finally:
                await message.delete()


@dp.message_handler(content_types=["left_chat_member"]) # Вышел
async def on_user_exit(message: types.Message):
    db.active(message.chat.id, message.left_chat_member.id, 0)
    await message.delete()


@dp.message_handler(commands=['set_owner']) # /set_owner
async def set_owner(message: types.Message):
    try:
        if message.chat.id == config.ADMIN_ID and message.chat.type == 'private':
            db.set_owner(message.chat.id)
    except Exception as e:
        logging.info(e)
    finally:
        await message.delete()


@dp.message_handler(commands=['ban'])
async def ban(message: types.Message):
    try:
        text = message.text.split()
        from_id = message.from_user.id
        chat_id = message.chat.id
        is_owner = db.get_owner(from_id)
        is_admin = db.get_admin(chat_id, from_id)
        is_moder = db.get_moder(chat_id, from_id)
        if not any([is_owner, is_admin, is_moder]) and config.ADMIN_ID != from_id:
            return
        user_id, first_name = await ent(message)
        is_owner_user = db.get_owner(user_id)
        is_admin_user = db.get_admin(chat_id, user_id)
        is_moder_user = db.get_moder(chat_id, user_id)
        if user_id == config.ADMIN_ID:
            msg = await message.answer('Недостаточно прав!')
            return
        elif is_moder and any([is_moder_user, is_admin_user, is_owner_user]):
            msg = await message.answer('Недостаточно прав!')
            return
        elif is_admin and any([is_owner_user, is_admin_user]):
            msg = await message.answer('Недостаточно прав!')
            return
        elif is_owner and is_owner_user:
            msg = await message.answer('Недостаточно прав!')
            return
        else:
            mention = await mention_text(first_name, user_id)
            db.add_ban(message.chat.id, user_id, text[-1])
            if text[-1] == '1':
                await bot.ban_chat_member(message.chat.id, user_id)
                msg = await message.answer(f'Пользователь {mention} забанен.\nПричина: Систематические нарушения правил.')
            else:
                await bot.unban_chat_member(message.chat.id, user_id, only_if_banned=True)
                msg = await message.answer(f'Пользователь {mention} разбанен.')
        asyncio.create_task(delete_message(msg, 3))
    except Exception as e:
        logging.info(e)
    finally:
        await message.delete()


@dp.message_handler(commands=['id'])
async def id(message: types.Message):
    db.delete_constant(message.from_user.id)
    try:
        text = message.text.split()
        from_id = message.from_user.id
        chat_id = message.chat.id
        is_owner = db.get_owner(from_id)
        is_admin = db.get_admin(chat_id, from_id)
        # is_moder = db.get_moder(chat_id, from_id)
        if not any([is_owner, is_admin]) and config.ADMIN_ID != from_id:
            return
        buttons = []
        if is_owner or from_id == config.ADMIN_ID:
            if from_id == config.ADMIN_ID:
                buttons.append('Назначить совладельцем')
            buttons.extend(
                [
                    'Назначить администратором',
                    'Назначить модератером',
                    'Понизить',
                    'Забанить в группе',
                    'Забанить в сети',
                    'Разбанить в сети',
                    'Разбанить в группе'
                ]
            )
        if is_admin:
            buttons = ['Назначить модератером',
                       'Понизить',
                       'Забанить в группе',
                       'Забанить в сети',
                       'Разбанить в группе']
        chat_id = message.chat.id
        if len(text) == 1:
            if message.reply_to_message is None:
                return await message.delete()

            user_id = message.reply_to_message.from_user.id
            first_name = message.reply_to_message.from_user.first_name
        else:
            user_id, first_name = await ent(message)
        mention = await mention_text(first_name, user_id)
        db.user_contain(message.from_user.id, user_id, chat_id, mention)
        is_owner_user = db.get_owner(user_id)
        is_admin_user = db.get_admin(chat_id, user_id)
        is_moder_user = db.get_moder(chat_id, user_id)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(*buttons)
        if user_id == config.ADMIN_ID:
            msg = await bot.send_message(message.from_user.id, 'Нельзя изменять права владельца!')
            return
        elif message.from_user.id == config.ADMIN_ID:
            msg = await bot.send_message(message.from_user.id, 'Выбрать действие:', reply_markup=keyboard)
        elif is_owner and not is_owner_user:
            msg = await bot.send_message(message.from_user.id, 'Выбрать действие:', reply_markup=keyboard)
        elif is_admin and not any([is_owner_user, is_admin_user]):
            msg = await bot.send_message(message.from_user.id, 'Выбрать действие:', reply_markup=keyboard)
        else:
            msg = await bot.send_message(message.from_user.id, 'Прав не достаточно!')
        asyncio.create_task(delete_message(msg, 3))
    except Exception as e:
        logging.info(e)
        db.delete_constant(message.from_user.id)
    finally:
        await message.delete()


@dp.message_handler(commands=['set_admin']) # /set_admin <username> 1 or 0
async def set_admin(message: types.Message):
    try:
        from_id = message.from_user.id
        chat_id = message.chat.id
        is_owner = db.get_owner(from_id)
        is_admin = db.get_admin(chat_id, from_id)
        is_moder = db.get_moder(chat_id, from_id)
        if not any([is_owner, is_admin]) and config.ADMIN_ID != from_id:
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
            else:
                user_id, first_name = await ent(message)
            is_owner_user = db.get_owner(user_id)
            is_admin_user = db.get_admin(chat_id, user_id)
            is_moder_user = db.get_moder(chat_id, user_id)
            if user_id == config.ADMIN_ID:
                await message.answer('Недостаточно прав!')
                return
            elif is_moder:
                await message.answer('Недостаточно прав!')
                return
            elif is_admin:
                await message.answer('Недостаточно прав!')
                return
            elif is_owner and is_owner_user:
                await message.answer('Недостаточно прав!')
                return
            else:
                mention = await mention_text(first_name, user_id)
                db.set_admin(message.chat.id, user_id, text[-1])
                if db.get_admin(message.chat.id, user_id):
                    await bot.promote_chat_member(
                        chat_id,
                        user_id,
                        can_manage_chat=True,
                        can_delete_messages=True,
                        can_restrict_members=True
                    )
                    time.sleep(5)
                    await bot.set_chat_administrator_custom_title(chat_id, user_id, custom_title='Администратор')
                    await message.answer(f'Пользователь {mention} назначен администратором сообщества.')
                else:
                    await bot.promote_chat_member(
                        chat_id, user_id
                    )
                    await message.answer(f'Пользователь {mention} снят с должности администратора.')
    except Exception as e:
        logging.info(e)
    finally:
        await message.delete()


@dp.message_handler(commands=['tagall'])
async def tag(message: types.Message):
    try:
        from_id = message.from_user.id
        chat_id = message.chat.id
        is_owner = db.get_owner(from_id)
        is_admin = db.get_admin(chat_id, from_id)
        is_moder = db.get_moder(chat_id, from_id)
        if not any([is_owner, is_admin, is_moder]) and config.ADMIN_ID != from_id:
            return
        text = message.text.split()
        if len(text) >= 2:
            for user_id, first_name in db.select_all(message.chat.id):
                mention = await mention_text(first_name, user_id)
                response = f'{" ".join(text[1:])}\n'
                response += f'{mention} '
                msg = await message.answer(response)
                asyncio.create_task(delete_message(msg, 3))
    except Exception as e:
        logging.info(e)
    finally:
        await message.delete()


"""@dp.message_handler(commands=['stop'], state='*')
async def cancel(message: types.Message,  state=FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()"""


@dp.message_handler(commands=['set_moder']) # /set_moder <username> 1 or 0
async def set_moder(message: types.Message):
    try:
        from_id = message.from_user.id
        chat_id = message.chat.id
        is_owner = db.get_owner(from_id)
        is_admin = db.get_admin(chat_id, from_id)
        is_moder = db.get_moder(chat_id, from_id)
        if not any([is_owner, is_admin, is_moder]) and config.ADMIN_ID != from_id:
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
            else:
                user_id, first_name = await ent(message)
            is_owner_user = db.get_owner(user_id)
            is_admin_user = db.get_admin(chat_id, user_id)
            is_moder_user = db.get_moder(chat_id, user_id)
            if user_id == config.ADMIN_ID:
                await message.answer('Недостаточно прав!')
                return
            elif is_moder:
                await message.answer('Недостаточно прав!')
                return
            elif is_admin and any([is_owner_user, is_admin_user]):
                await message.answer('Недостаточно прав!')
                return
            elif is_owner and is_owner_user:
                await message.answer('Недостаточно прав!')
                return
            else:
                mention = await mention_text(first_name, user_id)
                db.set_moder(message.chat.id, user_id, text[-1])
                if db.get_moder(message.chat.id, user_id):
                    await bot.promote_chat_member(
                        chat_id,
                        user_id,
                        can_manage_chat=True,
                    )
                    time.sleep(5)
                    await bot.set_chat_administrator_custom_title(chat_id, user_id, custom_title='Модератор')
                    await message.answer(f'Пользователь {mention} назначен модератором сообщества.')
                else:
                    await bot.promote_chat_member(
                        chat_id, user_id
                    )
                    await message.answer(f'Пользователь {mention} снят с должности модератора.')
    except Exception as e:
        logging.info(e)
    finally:
        await message.delete()


@dp.message_handler(commands=['add_money']) # /add_money @username 1000
async def add_money(message: types.Message):
    text = message.text.split()
    try:
        from_id = message.from_user.id
        chat_id = message.chat.id
        is_owner = db.get_owner(from_id)
        if not any([is_owner,]) and config.ADMIN_ID != from_id:
            return
        if len(text) >= 3:
            user_id, first_name = await ent(message)
        else:
            if not message.reply_to_message:
                await message.reply('Эта команда должна быть ответом на сообщение!')
                return

            user_id = message.reply_to_message.from_user.id
            first_name = message.reply_to_message.from_user.first_name
        if abs(int(text[-1])) > 1000000000:
            await message.answer(f'Число за пределами разумного!')
            return
        db.add_money(message.chat.id, user_id, int(text[-1]))
        mention = await mention_text(first_name, user_id)
        if int(text[-1]) > 0:
            await message.answer(f'Пользователю {mention} начислено {text[-1]} 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮') #Пользователю @х начислено 10 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛💠
        else:
            await message.answer(
                f'Во время налоговой проверки у {mention} изьяли {text[-1]} 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮')  # Пользователю @х начислено 10 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛💠
    except Exception as e:
        logging.info(e)
    finally:
        await message.delete()


@dp.message_handler(commands='setting')
async def setting(message: types.Message):
    if message.chat.type != 'private':
        await message.delete()
        return
    try:
        from_id = message.from_user.id
        is_owner = db.get_owner(from_id)
        if not any([is_owner]) and config.ADMIN_ID != from_id:
            return
        if not db.setting():
            db.create_setting()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        buttons = ['Валюта', 'Опыт', 'Инфогруппа']
        keyboard.add(*buttons)
        await message.answer('Выберите пункт для настройки', reply_markup=keyboard)
    except Exception as e:
        logging.info(e)
    finally:
        await message.delete()


def key_setting():
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton('+', callback_data='+'), types.InlineKeyboardButton('-', callback_data='-')]
    keyboard.add(*buttons)
    return keyboard


def key_setting_exp():
    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton('+', callback_data='+exp'), types.InlineKeyboardButton('-', callback_data='-exp')]
    keyboard.add(*buttons)
    return keyboard


def key_setting_group(groups):
    keyboard = types.InlineKeyboardMarkup()
    for group in groups:
        GROUP[group[0]] = GROUP.get(group[0], group[1])
        keyboard.add(types.InlineKeyboardButton(f'{group[1]}', callback_data=group[0]))
    return keyboard


@dp.message_handler(lambda m: m.text == 'Валюта')
async def cash(message: types.Message):
    if message.chat.type != 'private':
        return
    from_id = message.from_user.id
    is_owner = db.get_owner(from_id)
    if is_owner or config.ADMIN_ID == from_id:
        money = db.get_money_game()[0]
        msg = await message.answer(f'Количество валюты за победу в игре: {money}', reply_markup=key_setting())
        asyncio.create_task(delete_message(msg, 30))
    else:
        await message.answer('Недостаточно прав')
        return



@dp.message_handler(lambda m: m.text == 'Опыт')
async def exp(message: types.Message):
    if message.chat.type != 'private':
        return
    from_id = message.from_user.id
    is_owner = db.get_owner(from_id)
    if is_owner or config.ADMIN_ID == from_id:
        exp = db.get_exp_message()[0]
        msg = await message.answer(f'Количество опыта за сообщение: {exp}', reply_markup=key_setting_exp())
        asyncio.create_task(delete_message(msg, 30))
    else:
        await message.answer('Недостаточно прав')
        return


@dp.message_handler(lambda m: m.text == 'Инфогруппа')
async def exp(message: types.Message):
    if message.chat.type != 'private':
        return
    from_id = message.from_user.id
    is_owner = db.get_owner(from_id)
    if is_owner or config.ADMIN_ID == from_id:
        group = db.all_group()
        msg = await message.answer(f'Выберите группу для пересылки команд бота.', reply_markup=key_setting_group(group))
        asyncio.create_task(delete_message(msg, 30))
    else:
        await message.answer('Недостаточно прав')
        return


@dp.callback_query_handler(lambda m: 'exp' in m.data)
async def set_money_game(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    exp = db.get_exp_message()[0]
    if callback_query.data[0] == '+':
        exp += 1
    if exp > 0 and callback_query.data[0] == '-':
        exp -= 1
    db.set_exp_message(exp)
    msg = await bot.edit_message_text(
        f'Количество опыта за сообщение: {exp}',
        callback_query.message.chat.id,
        callback_query.message.message_id,
        reply_markup=key_setting_exp()
    )
    asyncio.create_task(delete_message(msg, 30))


@dp.callback_query_handler(lambda m: m.data in '+-')
async def set_money_game(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    money = db.get_money_game()[0]
    if callback_query.data == '+':
        money += 1
    if money > 0 and callback_query.data == '-':
        money -= 1
    db.set_money_game(money)
    msg = await bot.edit_message_text(
        f'Количество валюты за победу в игре: {money}',
        callback_query.message.chat.id,
        callback_query.message.message_id,
        reply_markup=key_setting()
    )
    asyncio.create_task(delete_message(msg, 30))


@dp.callback_query_handler(lambda m: m.data.startswith('-100'))
async def set_money_game(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    db.set_group_message(callback_query.data)
    msg = await bot.edit_message_text(
        f'Установлена группа: {GROUP[callback_query.data]}',
        callback_query.message.chat.id,
        callback_query.message.message_id
    )
    asyncio.create_task(delete_message(msg, 30))


@dp.message_handler(commands=['mute']) # /mute <username> 1m or 1h  reason
async def mute(message: types.Message):
    from_id = message.from_user.id
    chat_id = message.chat.id
    is_owner = db.get_owner(from_id)
    is_admin = db.get_admin(chat_id, from_id)
    is_moder = db.get_moder(chat_id, from_id)
    if not any([is_owner, is_admin, is_moder]) and config.ADMIN_ID != from_id:
        return
    try:
        text = message.text.split()
        if len(text) == 3:
            if not message.reply_to_message:
                await message.reply('Эта команда должна быть ответом на сообщение!')
                return
            user_id = message.reply_to_message.from_user.id
            first_name = message.reply_to_message.from_user.first_name
        else:
            user_id, first_name = await ent(message)
        is_owner_user = db.get_owner(user_id)
        is_admin_user = db.get_admin(chat_id, user_id)
        is_moder_user = db.get_moder(chat_id, user_id)
        if user_id == config.ADMIN_ID:
            await message.answer('Недостаточно прав!')
            return
        elif is_moder and any([is_moder_user, is_admin_user, is_owner_user]):
            await message.answer('Недостаточно прав!')
            return
        elif is_admin and any([is_owner_user, is_admin_user]):
            await message.answer('Недостаточно прав!')
            return
        elif is_owner and is_owner_user:
            await message.answer('Недостаточно прав!')
            return
        else:
            mention = await mention_text(first_name, user_id)
            mute_sec = int(text[-2][:-1])
            end = text[-2][-1]
            ending = time_check(end, mute_sec)
            await bot.restrict_chat_member(message.chat.id, user_id, until_date=int(time.time())+mute_sec*TIMECHECK.get(end, 1))
            mute_db = db.mute(message.chat.id, user_id) + 1
            db.add_mute(message.chat.id, user_id, mute_db, ' '.join(text[-2:]))
            if mute_db >= 25:
                db.add_ban(message.chat.id, user_id, 1)
                await bot.ban_chat_member(message.chat.id, user_id)
                await message.answer(f'Пользователь {mention} забанен.\nПричина: Систематические нарушения правил.')
            else:
                await message.answer(f'Пользователь {mention} получил мут на {mute_sec} {ending}.\nПричина: {text[-1]}\nНарушений: {mute_db}')
    except Exception as e:
        logging.info(e)
    finally:
        await message.delete()


@dp.message_handler(commands=['help'])
async def mute(message: types.Message):
    if message.chat.type != 'private':
        return
    try:
        from_id = message.from_user.id
        chat_id = message.chat.id
        is_owner = db.get_owner(from_id)
        is_admin = db.get_admin(chat_id, from_id)
        is_moder = db.get_moder(chat_id, from_id)
        if not any([is_owner, is_admin, is_moder]) and config.ADMIN_ID != from_id:
            return
        text = (f'Помощь по командам доступным для администрации.\n\n'
                f'<code>/info (никнейм) </code> - Выводит информацию о пользователе.\n\n'
                f'<code>/ban (никнейм) (1/0)</code> - параметр 1 выдает бан пользователю, 0 - снимает.\n\n'
                f'<code>/id (никнейм) </code> - меню действий с пользователем.\n\n'
                f'<code>/set_admin (никнейм) (1/0)</code> - параметр 1 выдает админа пользователю, 0 - снимает.\n\n'
                f'<code>/set_moder (никнейм) (1/0)</code> - параметр 1 выдает модера пользователю, 0 - снимает.\n\n'
                f'<code>/tagall текст (1/0)</code> - тегает пользователей с заданным текстом\n\n'
                f'<code>/add_money (никнейм) (кол-во)</code> - добавляет установленное количество валюты.\n\n'
                f'<code>/mute (никнейм) (время) (причина) </code> - дает мут пользователю на указаное кол-во времени\n\n'
                f'<code>/unmute (никнейм)</code> - снимает мут')
        await message.answer(text)
    except Exception as e:
        logging.info(e)
    finally:
        await message.delete()


@dp.message_handler(commands=['unmute'])
async def mute(message: types.Message):
    try:
        from_id = message.from_user.id
        chat_id = message.chat.id
        is_owner = db.get_owner(from_id)
        is_admin = db.get_admin(chat_id, from_id)
        is_moder = db.get_moder(chat_id, from_id)
        if not any([is_owner, is_admin, is_moder]) and config.ADMIN_ID != from_id:
            return
        text = message.text.split()
        if len(text) == 1:
            if not message.reply_to_message:
                await message.reply('Эта команда должна быть ответом на сообщение!')
                return
            user_id = message.reply_to_message.from_user.id
            first_name = message.reply_to_message.from_user.first_name
        else:
            user_id, first_name = await ent(message)
        mention = await mention_text(first_name, user_id)
        await bot.restrict_chat_member(message.chat.id, user_id, permissions=types.ChatPermissions(True,True,True,True,True,True,True,True))
        await message.answer(f'C пользователя {mention} сняты ограничения.')
    except Exception as e:
        logging.info(e)
    finally:
        await message.delete()


@dp.message_handler(lambda m: m.text.lower() in short_commands) # действия
async def test(message: types.Message):
    if not message.reply_to_message:
        await message.reply('Эта команда должна быть ответом на сообщение!')
        return
    person_one = await mention_text(message.from_user.first_name, message.from_user.id)
    person_two = await mention_text(message.reply_to_message.from_user.first_name, message.reply_to_message.from_user.id)
    if message.text.lower() == 'обнять':
        text = f'{person_one} обнял {person_two}'
    elif message.text.lower() == 'казнить':
        text = f'{person_one} казнил {person_two}'
    elif message.text.lower() == 'побить':
        text = f'{person_one} побил {person_two}'
    elif message.text.lower() == 'любовь':
        text = f'{person_one} признался в любви {person_two}'
    elif message.text.lower() == 'недоверие':
        text = f'{person_one} недоверяет {person_two}'
    else:
        text = f'{person_one} тусит с {person_two}'
    await message.answer(text)


async def add_mute(chat_id, first_name, user_id, times, reason):
    await bot.restrict_chat_member(chat_id, user_id,
                                   until_date=int(time.time()) + int(times[:-1]) * TIMECHECK.get(times[-1], 1))
    mute_db = db.mute(chat_id, user_id) + 1
    db.add_mute(chat_id, user_id, mute_db, f'{times} {reason}')
    mention = await mention_text(first_name, user_id)
    await bot.send_message(
        chat_id,
        f'Пользователь {mention} получил мут на {times[:-1]} {time_check(times[-1], int(times[:-1]))}.\nПричина: {reason}\nНарушений: {mute_db}'
    )


@dp.message_handler(lambda m: m.text == 'Купить разбан')
async def unban(message: types.Message):
    if message.chat.type != 'private':
        await message.delete()
        return
    keyboard = await group_keyboard(message.chat.id, 'unban')
    await message.answer('Выберите группу:', reply_markup=keyboard)


@dp.message_handler(lambda m: m.text == 'Купить разварн')
async def unwarn(message: types.Message):
    if message.chat.type != 'private':
        await message.delete()
        return
    keyboard = await group_keyboard(message.chat.id, 'unwarn')
    await message.answer('Выберите группу:', reply_markup=keyboard)


@dp.message_handler(lambda m: m.text == 'Купить префикс')
async def prefix(message: types.Message):
    if message.chat.type != 'private':
        await message.delete()
        return

    keyboard = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton('На 3 дня', callback_data='3day'),
               types.InlineKeyboardButton('На неделю', callback_data='week')]
    keyboard.add(*buttons)
    await message.answer('Выберите период:', reply_markup=keyboard)


async def group_keyboard(user_id, command):
    groups = db.all_group()
    buttons = []
    for group in groups:
        if db.user_exists(group[0], user_id):
            if command == 'prefix':
                buttons.append(types.InlineKeyboardButton(group[1], callback_data=f'p{group[0]}'))
            elif command == 'unban':
                buttons.append(types.InlineKeyboardButton(group[1], callback_data=f'b{group[0]}'))
            else:
                buttons.append(types.InlineKeyboardButton(group[1], callback_data=f'w{group[0]}'))
    return types.InlineKeyboardMarkup().add(*buttons)


@dp.callback_query_handler(lambda m: m.data in ['3day', 'week'])
async def prefix_buy(callback_query: types.CallbackQuery):
    try:
        await bot.answer_callback_query(callback_query.id)
        if callback_query.data == '3day':
            db.period_contain(user_id=callback_query.from_user.id, price=50, period=3)
        else:
            db.period_contain(user_id=callback_query.from_user.id, price=100, period=7)
        keyboard = await group_keyboard(callback_query.message.chat.id, command='prefix')
        await callback_query.message.answer('Выберите группу:', reply_markup=keyboard)
    except Exception as e:
        db.delete_constant(callback_query.message.from_user.id)
        logging.info(e)
    finally:
        await callback_query.message.delete()


@dp.callback_query_handler(lambda m: m.data.startswith('b-100'))
async def unban_cash(callback_query: types.CallbackQuery):
    chat_id = callback_query.data[1:]
    if db.cash_db(chat_id, callback_query.from_user.id) >= 200:
        db.add_money(chat_id, callback_query.from_user.id, -200)
        db.add_ban(chat_id, callback_query.from_user.id, 0)
        await callback_query.message.answer('Успешно!')
    else:
        'Недостаточно средств'


@dp.callback_query_handler(lambda m: m.data.startswith('w-100'))
async def warn_cash(callback_query: types.CallbackQuery):
    chat_id = callback_query.data[1:]
    if db.cash_db(chat_id, callback_query.from_user.id) >= 100:
        db.add_money(chat_id, callback_query.from_user.id, -100)
        text = db.unwarn(chat_id, callback_query.from_user.id, 5)
        await callback_query.message.answer(f'{text or "Успешно!"}')
    else:
        'Недостаточно средств'



@dp.callback_query_handler(lambda m: m.data.startswith('p-100'))
async def set_group(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    try:
        chat_id = callback_query.data[1:]
        db.period_contain(chat_id=chat_id, user_id=callback_query.from_user.id)
        price, x, y = db.period_contain(user_id=callback_query.from_user.id, params=1)
        if db.cash_db(chat_id, callback_query.from_user.id) >= price:
            await callback_query.message.answer('Введите желаемый префикс, не превышающий 16 символов.\n'
                                                'За оскорбительный префикс вы получите бан!\n\n'
                                                'Начните ввод префикса с "!" ("!Префикс")')
        else:
            await callback_query.message.answer('Недостаточно средств!')
            db.delete_constant(callback_query.message.from_user.id)
    except Exception as e:
        db.delete_constant(callback_query.message.from_user.id)
        logging.info(e)
    finally:
        await callback_query.message.delete()


@dp.message_handler(commands=['money'])
async def money_user(message: types.Message):
    try:
        cash = db.cash_db(message.chat.id, message.from_user.id)
        text = f'Баланс: {cash} 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n'
        mention = await mention_text(message.from_user.first_name, message.from_user.id)
        if cash <= 0:
            text += f'{mention}, нас ограбили, милорд!'
        elif cash <= 100:
            text += f'Ну наконец {mention} может не экономить на себе! Чебурек на все!!!'
        elif cash <= 1000:
            text += f'{mention}, ещё подкопить и на Канары...'
        else:
            text += f'{mention}, такое состояние никому нельзя показывать!'
        await message.answer(text)
    except Exception as e:
        logging.info(e)
    finally:
        await message.delete()


@dp.message_handler(lambda m: m.text.startswith('!'))
async def prefix_sets(message: types.Message):
    if not db.check_constaints:
        return
    price, period, chat_id = db.period_contain(user_id=message.from_user.id, params=1)
    try:
        if len(message.text[1:]) > 16:
            await message.answer('Слишком длинный префикс! Введите не более 16 символов!')
        elif message.text[1:] in config.WORDS:
            await message.answer('Префикс содержит запрещенные слова! Попробуйте снова!')
        else:
            await bot.promote_chat_member(
                chat_id,
                message.from_user.id,
                can_manage_chat=True
            )
            time.sleep(10)
            await bot.set_chat_administrator_custom_title(chat_id, message.from_user.id, custom_title=message.text[1:])
            db.add_money(chat_id, message.from_user.id, int(f'-{price}'))
            dates = db.set_period(chat_id, message.from_user.id, period)
            await message.answer(f'Вам установлен префикс <b>{message.text[1:]}</b>\n Дата окончания: {dates}')
    except Exception as e:
        await bot.promote_chat_member(
            chat_id,
            message.from_user.id,
            can_manage_chat=False
        )
        logging.info(e)
    finally:
        db.delete_constant(message.from_user.id)
        await message.delete()


@dp.message_handler(lambda m: m.text == 'Купить 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮')
async def coins(message: types.Message):
    owners = db.owners()
    text = ''
    for owner in owners:
        mention = await mention_text('Владелец', owner[0])
        text += f'{mention}\n'
    await message.answer(f'Для покупки 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮 свяжитесь с\n{text}')


@dp.message_handler()
async def mess_handler(message: types.Message):
    if message.chat.type == 'private':
        text = message.text
        if text in DICT_COMMANDS:
            print(db.user_contain(user_id=message.from_user.id, read=1))
            from_id, chat_id, mention = db.user_contain(user_id=message.from_user.id, read=1)
            if 'Понизить' in text or 'Забанить' in text:
                role = 0
            else:
                role = 1
            answer = await DICT_COMMANDS[text](from_id, chat_id, mention, role, message.from_user.id)
            msg = await message.answer(answer, reply_markup=types.ReplyKeyboardRemove())
            asyncio.create_task(delete_message(msg, 3))
        await message.delete()
        return

    if not db.user_exists(message.chat.id, message.from_user.id):
        db.add_user(message.chat.id, message.from_user.id, message.from_user.username, message.from_user.first_name, 1)
    print(message)
    text = message.text
    from_id = message.from_user.id
    chat_id = message.chat.id
    is_owner = db.get_owner(from_id)
    is_admin = db.get_admin(chat_id, from_id)
    is_moder = db.get_moder(chat_id, from_id)
    if db.check_flood(chat_id, text, from_id):
        if not any([is_owner, is_admin, is_moder]) or config.ADMIN_ID != from_id:
            await add_mute(chat_id, message.from_user.first_name, from_id, '30m', 'Флуд')
    db.add_time_message(chat_id, from_id)


    winners = ''
    if 'Игра окончена' in text:
        if message.from_user.id == 1634167847 or message.forward_from.id == 1634167847:
            text = text.partition('Другие:')[0]
            winners = list([x for _,x in re.findall(r'(\d.\s.(.*?)\s-)', text)])
        elif message.from_user.id == 1044037207 or message.forward_from.id == 1044037207:
            text = text.partition('Другие пользователи:')[0]
            winners = list([x for _, x in re.findall(r'(\d.\s(.*?)\s-)', text)])
        else:
            text = text.partition('Остальные участники:')[0]
            winners = list([x for _, x in re.findall(r'(\s{4}(.*?)\s-)', text)])
    if winners:
        count = 0
        text_winners = 'Игра окончена!'
        for entity in message.entities:
            if entity.type == 'text_mention' and db.user_exists(message.chat.id, entity.user.id):
                if count == len(winners):
                    break
                money = db.get_money_game()[0]
                db.add_money(message.chat.id, entity.user.id, money)
                mention = await mention_text(entity.user.first_name, entity.user.id)
                text_winners += f'{mention} - {money} 𝐹𝑙𝑎𝑚𝑒 𝐶𝑜𝑖𝑛 💮\n'
                count += 1
        await message.answer(text_winners)

    if 'не выдержал гнетущей атмосферы' in text:
        for entity in message.entities:
            if entity.type == 'text_mention' and db.user_exists(message.chat.id, entity.user.id):
                await add_mute(message.chat.id, entity.user.first_name, entity.user.id, '30m', 'Вышел из игры')
    if 'спать во время' in text:
        for entity in message.entities:
            if entity.type == 'text_mention' and db.user_exists(message.chat.id, entity.user.id):
                await add_mute(message.chat.id, entity.user.first_name, entity.user.id, '30m', 'АФК')

    for word in config.WORDS:
        if word in text.lower():
            await message.delete()

    for entity in message.entities:
        if entity.type in ["url", "text_link"] and not any([is_owner, is_admin, is_moder]):
            await bot.send_message(
                message.from_user.id,
                "Eсли Вы хотите отправлять ссылки со своей рекламой, обратитесь к администратору @admin"
            )
            await message.delete()
    if db.delete_prefix(message.chat.id, message.from_user.id) and not any([is_owner, is_admin, is_moder]):
        await bot.promote_chat_member(
            chat_id,
            message.from_user.id
        )

    db.update_user(message.chat.id, message.from_user.id, message.from_user.username, message.from_user.first_name)
    db.exp(message.chat.id, message.from_user.id)


if __name__ == "__main__":
    DICT_COMMANDS = {
        'Назначить совладельцем': add_owner,
        'Назначить администратором': admin_private,
        'Назначить модератером': moder_private,
        'Понизить': downgrade,
        'Забанить в сети': add_banned,
        'Забанить в группе': ban_group,
        'Разбанить в сети': add_banned,
        'Разбанить в группе': ban_group
    }
    executor.start_polling(dp, skip_updates=True)