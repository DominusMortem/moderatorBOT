import sqlite3
import datetime
import psycopg2


class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file, check_same_thread=False, timeout=10)
        """self.connection = psycopg2.connect(dbname='database', user='db_user',
                                password='mypassword', host='localhost')"""
        self.cursor = self.connection.cursor()
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS main(
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           owner_id INT UNIQUE);
        """
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS banned(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INT UNIQUE,
            desc TEXT);"""
        )

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS groups(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT UNIQUE,
            title TEXT,
            silent_mode INT NOT NULL DEFAULT 0,
            pair_game INT NOT NULL DEFAULT 0,
            serial_killer INT NOT NULL DEFAULT 0,
            time_serial TEXT NOT NULL DEFAULT 0,
            setka INT NOT NULL DEFAULT 0,
            lottery INT NOT NULL DEFAULT 0,
            revo INT NOT NULL DEFAULT 0);"""
        )
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS setting(
            id INTEGER PRIMARY KEY,
            money_for_game INT NOT NULL DEFAULT 0,
            id_group_log TEXT UNIQUE,
            exp_for_message INT NOT NULL DEFAULT 0,
            gif INT NOT NULL DEFAULT 0,
            pair_game INT NOT NULL DEFAULT 0);"""
        )
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS constants(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INT UNIQUE,
            from_id INT,
            chat_id TEXT,
            prefix_price INT,
            prefix_period INT,
            mention TEXT,
            person_first_name TEXT,
            person_id INT,
            person_two_first_name TEXT,
            person_two_id INT
            );""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS rpcontext(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            com TEXT,
            desc TEXT,
            until_date TEXT NOT NULL DEFAULT 0,
            prefix TEXT,
            user_id INT);""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS VIP(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            until_date TEXT NOT NULL DEFAULT 0,
            user_id INT);""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS killer(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INT,
            first_name TEXT,
            chat_id INT);""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS lottery(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INT,
                    first_name TEXT,
                    chat_id INT);""")
        self.cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS flame_net(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INT,
                        chat_id INT,
                        username TEXT,
                        create_time TEXT,
                        first_message TEXT,
                        last_message TEXT,
                        wedding TEXT NOT NULL DEFAULT `0`,
                        wedding_time TEXT,
                        ban INT NOT NULL DEFAULT 0,
                        time_ban TEXT,
                        time_mute TEXT,
                        mute INT NOT NULL DEFAULT 0,
                        mute_reason TEXT,
                        is_admin INT NOT NULL DEFAULT 0,
                        cash INT NOT NULL DEFAULT 0,
                        is_moder INT NOT NULL DEFAULT 0,
                        role TEXT NOT NULL DEFAULT `Новичок`,
                        count_message INT NOT NULL DEFAULT 0,
                        exp TEXT NOT NULL DEFAULT `0/300`,
                        first_name TEXT,
                        prefix_off TEXT,
                        message TEXT,
                        count INT,
                        is_active INT NOT NULL DEFAULT 0,
                        message_id INT,
                        reputation INT NOT NULL DEFAULT 0,
                        karma INT NOT NULL DEFAULT 0,
                        items TEXT DEFAULT 0);
                        """
        )
        self.connection.commit()

    def add_user(self, chat_id, user_id, username, first_name, is_active):
        with self.connection:
            return self.cursor.execute(
                f"""INSERT INTO `flame_net`
                (`chat_id`, `user_id`, `username`, `create_time`, `last_message`, `first_name`, `is_active`)
                 VALUES (?,?,?,?,?,?,?);""",
                (
                    chat_id,
                    user_id,
                    username,
                    datetime.date.today(),
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    first_name,
                    is_active
                )
            )

    def __del__(self):
        self.connection.close()