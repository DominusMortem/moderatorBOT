from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///database.db', connect_args={'timeout': 10})
engine.connect()
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()


Base = declarative_base()


class Main(Base):
    __tablename__ = 'main'

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer)
    first_name = Column(String)


class RPContext(Base):
    __tablename__ = 'rpcontext'

    id = Column(Integer, primary_key=True, autoincrement=True)
    com = Column(String)
    desc = Column(String)
    until_date = Column(String, nullable=False, default='0')
    prefix = Column(String)
    user_id = Column(Integer)


class VIP(Base):
    __tablename__ = 'VIP'

    id = Column(Integer, primary_key=True, autoincrement=True)
    until_date = Column(String, nullable=False, default='0')
    user_id = Column(Integer)


class Game(Base):
    __tablename__ = 'game'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    first_name = Column(String)
    chat_id = Column(Integer)


class Lottery(Base):
    __tablename__ = 'lottery'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    first_name = Column(String)
    chat_id = Column(Integer)


class Constants(Base):
    __tablename__ = 'constants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True)
    chat_id = Column(String)
    person_first_name = Column(String)
    person_id = Column(Integer)
    person_two_first_name = Column(String)
    person_two_id = Column(Integer)


class Setting(Base):
    __tablename__ = 'setting'

    id = Column(Integer, primary_key=True)
    money_for_game = Column(Integer, nullable=False, default=0)
    id_group_log = Column(String, unique=True)
    exp_for_message = Column(Integer, nullable=False, default=0)
    hello = Column(Integer, nullable=False, default=0)
    

class Groups(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String, unique=True)
    title = Column(String)
    silent_mode = Column(Integer, nullable=False, default=0)
    pair_game = Column(Integer, nullable=False, default=0)
    serial_killer = Column(Integer, nullable=False, default=0)
    time_serial = Column(String, nullable=False, default='0')
    setka = Column(Integer, nullable=False, default=0)
    lottery = Column(Integer, nullable=False, default=0)
    revo = Column(Integer, nullable=False, default=0)


class Banned(Base):
    __tablename__ = 'banned'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True)
    desc = Column(String)
    admin_id = Column(Integer)


class FlameNet(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    chat_id = Column(Integer)
    username = Column(String)
    create_time = Column(String)
    first_message = Column(String)
    last_message = Column(String)
    wedding = Column(String, nullable=False, default='0')
    wedding_time = Column(String)
    ban = Column(Integer, nullable=False, default=0)
    time_ban = Column(String)
    time_mute = Column(String)
    mute = Column(Integer, nullable=False, default=0)
    mute_reason = Column(String)
    is_admin = Column(Integer, nullable=False, default=0)
    cash = Column(Integer, nullable=False, default=0)
    is_moder = Column(Integer, nullable=False, default=0)
    role = Column(String, nullable=False, default='Новичок')
    count_message = Column(Integer, nullable=False, default=0)
    exp = Column(String, nullable=False, default='0/300')
    first_name = Column(String)
    prefix_off = Column(String)
    count = Column(Integer)
    is_active = Column(Integer, nullable=False, default=0)
    reputation = Column(Integer, nullable=False, default=0)
    karma = Column(Integer, nullable=False, default=0)
    items = Column(String, nullable=False, default='0')
