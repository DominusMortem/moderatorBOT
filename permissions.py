from sqlalchemy.sql import exists

from query import session, FlameNet, Main
from config import ADMIN_ID


def is_big_owner(user_id):
    return ADMIN_ID == user_id


def is_owner(user_id):
    return session.query(exists().where(Main.owner_id == user_id)).scalar()


def is_admin(chat_id, user_id):
    return session.query(
        exists().where(
            FlameNet.chat_id == chat_id,
            FlameNet.user_id == user_id,
            FlameNet.is_admin == 1
        )
    ).scalar()


def is_moder(chat_id, user_id):
    return session.query(
        exists().where(
            FlameNet.chat_id == chat_id,
            FlameNet.user_id == user_id,
            FlameNet.is_moder == 1
        )
    ).scalar()
