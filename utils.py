import datetime

from sqlalchemy.sql import exists
from sqlalchemy import func

from query import session, FlameNet, Main, Groups, Lottery, Banned, RPContext, VIP, Setting, Killer, Constants


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
    return ending

def wedding_date_now(date):
    duration = date
    day_time = 60*60*24
    hours = 60*60
    minutes = 60
    day = int(duration//day_time)
    hour = int(duration%day_time//hours)
    minute = int(duration%day_time%hours//minutes)
    seconds = int(duration%day_time%hours%minutes)
    return f'{day} д. {hour} ч. {minute} мин. {seconds} сек'


def user_exists(chat_id, user_id):
    """Проверка что пользователь существует в чате"""
    return session.query(exists().where(FlameNet.chat_id == chat_id, FlameNet.user_id == user_id)).scalar()


def get_user_by_username(chat_id, username):
    return session.query(FlameNet).filter(FlameNet.chat_id == chat_id, FlameNet.username == username).one_or_none()


def user_lottery(chat_id, user_id):
    """Проверка что пользователь учавствует в лотерее"""
    return session.query(exists().where(Killer.chat_id == chat_id, Killer.user_id == user_id)).scalar()


def salent(chat_id):
    """Проверка тихого режима"""
    return session.query(exists().where(Groups.group_id == chat_id, Groups.silent_mode == 1)).scalar()

def setka(chat_id):
    """Проверка чата на вхождение в сеть"""
    return session.query(exists().where(Groups.group_id == chat_id, Groups.setka == 1)).scalar()


def owner_exists(user_id):
    """Проверка что пользователь совладелец"""
    return session.query(exists().where(Main.owner_id == user_id)).scalar()


def serial_exists(chat_id):
    """Проверка что пользователь совладелец"""
    return session.query(exists().where(Groups.group_id == chat_id, Groups.serial_killer == 1)).scalar()

def lottery_exists(chat_id):
    """Проверка что пользователь совладелец"""
    return session.query(exists().where(Groups.group_id == chat_id, Groups.lottery == 1)).scalar()


def get_user(chat_id, user_id):
    """Получаем информацию о пользователе в чате"""
    return session.query(FlameNet).filter(
                FlameNet.chat_id == chat_id, FlameNet.user_id == user_id
            ).one_or_none()


def get_money(user_id):
    """Получаем редства пользователя во всех чатах"""
    return session.query(func.sum(FlameNet.cash)).filter(FlameNet.user_id == user_id).scalar()


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
    return session.query(Groups).filter(Groups.group_id == chat_id).one_or_none()


def get_lottery(chat_id):
    """Получаем информацию о распорядителях лотереи"""
    return session.query(Lottery).filter(Lottery.chat_id == chat_id).all()


def banned_exists(user_id):
    """Проверка пользователя в черном списке"""
    return session.query(exists().where(Banned.user_id == user_id)).scalar()


def get_banned(user_id):
    """Получаем информацию о пользователе в черном списке"""
    return session.query(Banned).filter(Banned.user_id == user_id).one_or_none()


def check_rp(com, user_id):
    """Проверка RP команды для пользователя"""
    return session.query(exists().where(RPContext.user_id == user_id, RPContext.com == com)).scalar()


def get_com_rp(com, user_id):
    """Получение RP команды для пользователя"""
    return session.query(RPContext).filter(RPContext.com == com, RPContext.user_id == user_id).one_or_none()


def get_rp():
    """Получение RP команд"""
    return session.query(RPContext).all()


def get_rp_by_id(rp_id):
    """Получение RP команд"""
    return session.query(RPContext).filter(RPContext.id == rp_id).one_or_none()


def get_user_rp(user_id):
    """Получение RP команд для пользователя"""
    return session.query(RPContext).filter(RPContext.user_id == user_id).all()


def get_vip(user_id):
    """Удаление RP команд при истечении ВИП"""
    user = session.query(VIP).filter(VIP.user_id == user_id).one_or_none()
    if user:
        if datetime.datetime.now() >= datetime.datetime.strptime(user.until_date, '%Y-%m-%d %H:%M:%S'):
            session.delete(user)
            get_user_rp(user_id=user_id).delete()
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
    admins = session.query(FlameNet).filter(FlameNet.chat_id == chat_id, FlameNet.is_admin == 1).all()
    moders = session.query(FlameNet).filter(FlameNet.chat_id == chat_id, FlameNet.is_moder == 1).all()
    return admins, moders, owners


def exp(expirience, count_message):
    exp_rate = {
        'Новичок': range(0, 301),
        'Обыватель': range(301, 1001),
        'Опытный': range(1001, 2001),
        'Ветеран': range(2001, 5001)
    }
    exp = int(expirience.split('/')[0])
    exp_to_mes = get_setting().exp_for_message
    if count_message:
        exp += exp_to_mes
    if exp >= 5000:
        exp = exp
        role = 'Легендарный'
    else:
        for k, v in exp_rate.items():
            if exp in v:
                role = k
                exp = f'{exp}/{max(v)}'
    return role, exp


def get_killer(chat_id):
    return session.query(Killer).filter(Killer.chat_id == chat_id).all()


def stop_victim(chat_id):
        group = get_group(chat_id)
        if group.time_serial:
            if datetime.datetime.now() >= datetime.datetime.strptime(group.time_serial, '%Y-%m-%d %H:%M:%S'):
                group.serial_killer = 0
                group.time_serial = 0
                session.commit()
                return True
        users = get_killer(chat_id)
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
    if datetime.datetime.now() >= datetime.datetime.strptime(user.prefix_off, '%Y-%m-%d %H:%M:%S'):
        user.prefix_off = None
        session.commit()
        return True


def all_owner():
    return session.query(Main).all()


def get_pair(chat_id):
    return session.query(FlameNet).filter(FlameNet.chat_id == chat_id, FlameNet.wedding != 0, FlameNet.wedding_time).all()


def get_constant(user_id):
    return session.query(Constants).filter(Constants.user_id == user_id).one_or_none()


def get_constant_wedding(chat_id, user_id):
    return session.query(Constants).filter(Constants.chat_id == chat_id, Constants.user_id == user_id).one_or_none()