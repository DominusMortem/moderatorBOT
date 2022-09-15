import datetime

from sqlalchemy.sql import exists
from sqlalchemy import func

from query import (
    session,
    FlameNet,
    Main,
    Groups,
    Lottery,
    Banned,
    RPContext,
    VIP,
    Setting,
    Game,
    Constants
)


def time_check(end, time):
    if end in 'мm':
        if time in (1, 21, 31, 41, 51):
            ending = 'минуту'
        elif time in (2, 3, 4, 22, 23, 24, 32, 33, 34, 42, 43, 44, 52, 53, 54):
            ending = 'минуты'
        else:
            ending = 'минут'
    elif end in 'hч':
        if time in (1, 21):
            ending = 'час'
        elif time in (2, 3, 4, 22, 23, 24):
            ending = 'часа'
        else:
            ending = 'часов'
    else:
        ending = 'Ошибка'
    return ending


def wedding_date_now(date):
    duration = date
    day_time = 60 * 60 * 24
    hours = 60 * 60
    minutes = 60
    day = int(duration // day_time)
    hour = int(duration % day_time // hours)
    minute = int(duration % day_time % hours // minutes)
    seconds = int(duration % day_time % hours % minutes)
    return f'{day} д. {hour} ч. {minute} мин. {seconds} сек'


def get_item_user(user, item):
    items_user = [
        x.split(':') for x in [
            item for item in user.items.split(',') if user.items != '0'
        ]
    ]
    i = None
    if not items_user:
        i = None
    items_to_dict = {x: int(y) for x, y in items_user}
    for k in items_to_dict.keys():
        if item.lower() in k.lower():
            i = k
            break
        else:
            i = None
    return i


def items(user, item, delete=0):
    items_user = user.items
    if items_user == '0':
        items_user = f'{item}:1'
    else:
        items_user = [x.split(':') for x in [
            item for item in items_user.split(',')
        ]]
        items_to_dict = {x: int(y) for x, y in items_user}
        if delete:
            items_to_dict[item] = int(items_to_dict.get(item, 0)) - 1
            if items_to_dict[item] == 0:
                del items_to_dict[item]
        else:
            items_to_dict[item] = int(items_to_dict.get(item, 0)) + 1
        items_user = ','.join([f'{k}:{v}' for k, v in items_to_dict.items()])
    return items_user


def roulette_exist(chat_id):
    return session.query(
        exists().where(Groups.group_id == chat_id, Groups.revo == 1)).scalar()


def user_exists(chat_id, user_id):
    """Проверка что пользователь существует в чате"""
    return session.query(exists().where(FlameNet.chat_id == chat_id,
                                        FlameNet.user_id == user_id)).scalar()


def get_user_by_username(chat_id, username):
    return session.query(FlameNet).filter(
        FlameNet.chat_id == chat_id,
        FlameNet.username == username
    ).one_or_none()


def user_lottery(chat_id, user_id):
    """Проверка что пользователь учавствует в лотерее"""
    return session.query(exists().where(Game.chat_id == chat_id,
                                        Game.user_id == user_id)).scalar()


def salent(chat_id):
    """Проверка тихого режима"""
    return session.query(exists().where(Groups.group_id == chat_id,
                                        Groups.silent_mode == 1)).scalar()


def setka(chat_id):
    """Проверка чата на вхождение в сеть"""
    return session.query(
        exists().where(Groups.group_id == chat_id, Groups.setka == 1)).scalar()


def owner_exists(user_id):
    """Проверка что пользователь совладелец"""
    return session.query(exists().where(Main.owner_id == user_id)).scalar()


def serial_exists(chat_id):
    """Проверка что пользователь совладелец"""
    return session.query(exists().where(Groups.group_id == chat_id,
                                        Groups.serial_killer == 1)).scalar()


def lottery_exists(chat_id):
    """Проверка что пользователь совладелец"""
    return not session.query(exists().where(Groups.group_id == chat_id,
                                            Groups.lottery == 0)).scalar()


def get_user(chat_id, user_id):
    """Получаем информацию о пользователе в чате"""
    return session.query(FlameNet).filter(
        FlameNet.chat_id == chat_id, FlameNet.user_id == user_id
    ).one_or_none()


def get_money(user_id):
    """Получаем редства пользователя во всех чатах"""
    return session.query(func.sum(FlameNet.cash)).filter(
        FlameNet.user_id == user_id).scalar()


def get_users(chat_id):
    """Получаем информацию о пользователях чата"""
    return session.query(FlameNet).filter(
        FlameNet.chat_id == chat_id
    ).all()


def get_users_prefix(chat_id):
    """Получаем информацию о пользователях чата"""
    return session.query(FlameNet).filter(
        FlameNet.chat_id == chat_id, FlameNet.prefix_off
    ).all()


def get_groups():
    """Получаем информацию о чатах сети"""
    return session.query(Groups).all()


def get_group(chat_id):
    """Получаем информацию о чате сети"""
    return session.query(Groups).filter(
        Groups.group_id == chat_id).one_or_none()


def get_lottery(chat_id):
    """Получаем информацию о распорядителях лотереи"""
    return session.query(Lottery).filter(Lottery.chat_id == chat_id).all()


def banned_exists(user_id):
    """Проверка пользователя в черном списке"""
    return session.query(exists().where(Banned.user_id == user_id)).scalar()


def get_banned(user_id):
    """Получаем информацию о пользователе в черном списке"""
    return session.query(Banned).filter(
        Banned.user_id == user_id).one_or_none()


def check_rp(com, user_id):
    """Проверка RP команды для пользователя"""
    return session.query(exists().where(RPContext.user_id == user_id,
                                        RPContext.com == com)).scalar()


def get_com_rp(com, user_id):
    """Получение RP команды для пользователя"""
    return session.query(RPContext).filter(
        RPContext.com == com,
        RPContext.user_id == user_id
    ).one_or_none()


def get_rp():
    """Получение RP команд"""
    return session.query(RPContext).all()


def get_rp_by_id(rp_id):
    """Получение RP команд"""
    return session.query(RPContext).filter(RPContext.id == rp_id).one_or_none()


def get_user_rp(user_id):
    """Получение RP команд для пользователя"""
    return session.query(RPContext).filter(RPContext.user_id == user_id).all()


def vip(user_id):
    return session.query(VIP).filter(VIP.user_id == user_id).one_or_none()


def get_vip(user_id):
    """Удаление RP команд при истечении ВИП"""
    user = vip(user_id)
    if user:
        if datetime.datetime.now() >= datetime.datetime.strptime(
                user.until_date, '%Y-%m-%d %H:%M:%S'):
            session.delete(user)
            session.query(RPContext).filter(
                RPContext.user_id == user_id).delete()
            session.commit()
            return True


def get_setting():
    """Получение настроек бота"""
    return session.query(Setting).filter(Setting.id == 1).one_or_none()


def check_vip(user_id):
    """Проверка VIP для пользователя"""
    return session.query(exists().where(VIP.user_id == user_id)).scalar()


def get_all_admin(chat_id):
    """Получение списка всех администраторов бота"""
    owners = session.query(Main)
    owners_first_name = []
    for owner in owners:
        user = session.query(FlameNet).filter(
            FlameNet.user_id == owner.owner_id).all()
        owners_first_name.append(user[0])
    admins = session.query(FlameNet).filter(FlameNet.chat_id == chat_id,
                                            FlameNet.is_admin == 1).all()
    moders = session.query(FlameNet).filter(FlameNet.chat_id == chat_id,
                                            FlameNet.is_moder == 1).all()
    return admins, moders, owners_first_name


def exp(exp_user, count_message):
    exp_rate = {
        'Новичок': range(0, 301),
        'Обыватель': range(301, 1001),
        'Опытный': range(1001, 2001),
        'Ветеран': range(2001, 5001)
    }
    exp_user = int(exp_user.split('/')[0])
    exp_to_mes = get_setting().exp_for_message
    role = None
    if count_message:
        exp_user += exp_to_mes
    if exp_user >= 5000:
        exp_user = exp_user
        role = 'Легендарный'
    else:
        for k, v in exp_rate.items():
            if exp_user in v:
                role = k
                exp_user = f'{exp_user}/{max(v)}'
    return role, exp_user


def get_game(chat_id):
    return session.query(Game).filter(Game.chat_id == chat_id).all()


def stop_victim(chat_id):
    group = get_group(chat_id)
    if group.time_serial != '0':
        if datetime.datetime.now() >= datetime.datetime.strptime(
                str(group.time_serial),
                '%Y-%m-%d %H:%M:%S'
        ):
            group.serial_killer = 0
            group.time_serial = 0
            session.commit()
            return True
    users = get_game(chat_id)
    if len(users) == 25:
        group.serial_killer = 0
        group.time_serial = 0
        session.commit()
        return True
    else:
        return False


def delete_prefix(chat_id, user_id):
    user = get_user(chat_id, user_id)
    if not user.prefix_off:
        return False
    if datetime.datetime.now() >= datetime.datetime.strptime(
            user.prefix_off,
            '%Y-%m-%d %H:%M:%S'
    ):
        user.prefix_off = None
        session.commit()
        return True


def all_owner():
    return session.query(Main).all()


def get_pair(chat_id):
    return session.query(FlameNet).filter(FlameNet.chat_id == chat_id,
                                          FlameNet.wedding != 0,
                                          FlameNet.wedding_time).all()


def get_constant(user_id):
    return session.query(Constants).filter(
        Constants.user_id == user_id).one_or_none()


def get_constant_wedding(chat_id, user_id):
    return session.query(Constants).filter(
        Constants.chat_id == chat_id,
        Constants.user_id == user_id
    ).one_or_none()
