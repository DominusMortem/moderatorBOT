import sqlite3
import datetime
import psycopg2


class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
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
            lottery INT NOT NULL DEFAULT 0);"""
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
        self.connection.commit()

    def create_table(self, id_group, title):
        with self.connection:
            self.cursor.execute(
                f"""CREATE TABLE IF NOT EXISTS `{str(id_group)}`(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INT UNIQUE,
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
            self.cursor.execute(f"insert into `groups` (`group_id`, `title`) values (?,?);", (id_group, title))
            self.connection.commit()


    def create_tables(self):
        with self.connection:
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
            for group in self.all_group():
                for user in self.info_chat(group[0]):
                    self.cursor.execute('''insert into `flame_net` (`user_id`,
                                                                    `chat_id`,
                                                                    `username`,
                                                                    `create_time`,
                                                                    `first_message`,
                                                                    `last_message`,
                                                                    `wedding`,
                                                                    `wedding_time`,
                                                                    `ban`,
                                                                    `time_ban`,
                                                                    `time_mute`,
                                                                    `mute`,
                                                                    `mute_reason`,
                                                                    `is_admin`,
                                                                    `cash`,
                                                                    `is_moder`,
                                                                    `role`,
                                                                    `count_message`,
                                                                    `exp`,
                                                                    `first_name`,
                                                                    `prefix_off`,
                                                                    `message`,
                                                                    `count`,
                                                                    `is_active`,
                                                                    `message_id`,
                                                                    `reputation`,
                                                                    `karma`,
                                                                    `items`) 
                                                                    values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);''',
                                        (user[1], group[0], *user[2:]))



    def items(self, chat_id, user_id):
        with self.connection:
            return self.cursor.execute(f'select `items` from `{str(chat_id)}` where `user_id` = ?', (user_id, )).fetchone()

    def add_items(self, chat_id, user_id, items):
        with self.connection:
            return self.cursor.execute(f'update `{str(chat_id)}` set `items` = ? where `user_id` = ?', (items, user_id))

# серийный убийца -----------------------------------

    def get_serial(self, chat_id):
        with self.connection:
            return self.cursor.execute('select `serial_killer` from `groups` where `group_id` = ?;', (chat_id,)).fetchone()[0]

    def get_lottery(self, chat_id):
        with self.connection:
            return self.cursor.execute('select `lottery` from `groups` where `group_id` = ?;', (chat_id,)).fetchone()[0]

    def add_lottery(self, chat_id):
        with self.connection:
            return self.cursor.execute(f'update `groups` set `lottery` = ? where `group_id` = ?;',
                                        (1, chat_id))

    def add_serial(self, chat_id, t):
        with self.connection:
            dates = datetime.datetime.now() + datetime.timedelta(minutes=t)
            return self.cursor.execute(f'update `groups` set `serial_killer` = ?, `time_serial` = ? where `group_id` = ?;',
                                        (1, dates.strftime('%Y-%m-%d %H:%M:%S'), chat_id))

    def get_time_serial(self, chat_id):
        with self.connection:
            return self.cursor.execute(f'select `time_serial` from `groups` where `group_id` = ?;', (chat_id,)).fetchone()[0]

    def add_victim(self, chat_id, user_id, first_name):
        with self.connection:
            if not bool(len(self.cursor.execute('select * from `killer` where `chat_id` = ? and `user_id` = ?;', (chat_id, user_id)).fetchall())):
                return self.cursor.execute('insert into `killer` (`user_id`, `chat_id`, `first_name`) values (?,?,?);', (user_id, chat_id, first_name))

    def add_user_lottery(self, chat_id, user_id, first_name):
        with self.connection:
            if not bool(len(self.cursor.execute('select * from `lottery` where `chat_id` = ? and `user_id` = ?;', (chat_id, user_id)).fetchall())):
                return self.cursor.execute('insert into `lottery` (`user_id`, `chat_id`, `first_name`) values (?,?,?);', (user_id, chat_id, first_name))

    def del_victim(self, chat_id):
        with self.connection:
            return self.cursor.execute('delete from `killer` where `chat_id` = ?;', (chat_id,))

    def get_victim(self, chat_id):
        with self.connection:
            return self.cursor.execute('select `user_id`, `first_name` from `killer` where `chat_id` = ?;', (chat_id,)).fetchall()

    def get_user_lottery(self, chat_id):
        with self.connection:
            return [user[0] for user in self.cursor.execute('select `user_id` from `lottery` where `chat_id` = ?;', (chat_id,)).fetchall()]

    def stop_victim(self, chat_id):
        with self.connection:
            until = self.cursor.execute('select `time_serial` from `groups` where `group_id` = ?;', (chat_id,)).fetchone()
            if until and until[0]:
                if datetime.datetime.now() >= datetime.datetime.strptime(until[0], '%Y-%m-%d %H:%M:%S'):
                    self.cursor.execute(f'update `groups` set `serial_killer` = ?, `time_serial` = ?, `lottery` = ? where `group_id` = ?;',
                                        (0, 0, 0, chat_id))
                    return True
            users = self.cursor.execute('select * from `killer` where `chat_id` = ?;', (chat_id,)).fetchall()
            if len(users) == 25:
                self.cursor.execute(
                    f'update `groups` set `serial_killer` = ?, `time_serial` = ?, `lottery` = ? where `group_id` = ?;',
                    (0, 0, 0, chat_id))
                return True
            else:
                return False
# -------------------------------------

    def check_setka(self, chat_id):
        with self.connection:
            group = self.cursor.execute('select `setka` from `groups` where `group_id` = ?;', (chat_id,)).fetchone()
            if group:
                return group[0]
            else:
                return

    def setka(self, chat_id, param):
        with self.connection:
            return self.cursor.execute(f'update `groups` set `setka` = ? where `group_id` = ?;',
                                        (param, chat_id))


# карма -----------------------------------

    def karma_add(self, chat_id, user_id, point):
        with self.connection:
            rep = self.cursor.execute(f"select `reputation` from `{str(chat_id)}` where `user_id` = ?;", (user_id, )).fetchone()[0]
            rep += point
            if rep >= 500:
                rep = 500
            if rep <= -500:
                rep = -500
            return self.cursor.execute(f"update `{str(chat_id)}` set `reputation` = ? where `user_id` = ?;", (rep, user_id))

    def karma(self, chat_id, user_id):
        with self.connection:
            k = self.cursor.execute(f'select `karma` from `{str(chat_id)}` where `user_id` = ?;', (user_id,)).fetchone()[0]
            k += 1
            return self.cursor.execute(f'update `{str(chat_id)}` set `karma` = ? where `user_id` = ?;', (k, user_id))

# -------------------------------------------
    def get_all_id(self, chat_id):
        with self.connection:
            return self.cursor.execute(f'select `user_id` from `{str(chat_id)}`;').fetchall()

    def pair_game(self, chat_id, mode):
        with self.connection:
            return self.cursor.execute(f"update `groups` set `pair_game` = ? where `group_id` = ?;", (mode, chat_id))

    def get_pair_game(self, chat_id):
        with self.connection:
            return bool(self.cursor.execute(f"select `pair_game` from `groups` where `group_id` = ?;", (chat_id,)).fetchone()[0])

    def get_silent_mode(self, chat_id):
        with self.connection:
            return bool(self.cursor.execute('select `silent_mode` from `groups` where `group_id` = ?;', (chat_id,)).fetchone()[0])

    def set_silent_mode(self, chat_id, mode):
        with self.connection:
            return self.cursor.execute(f"update `groups` set `silent_mode` = ? where `group_id` = ?;", (mode, chat_id))

    def create_vip(self, user_id, params=0):
        with self.connection:
            user = self.cursor.execute('select * from `VIP` where `user_id` = ?;', (user_id,)).fetchone()
            if params == 1:
                dates = datetime.datetime.now() + datetime.timedelta(days=30)
                return self.cursor.execute('insert into `VIP` (`user_id`, `until_date`) values (?,?);', (user_id, dates.strftime('%Y-%m-%d %H:%M:%S')))
            if user and user[0]:
                return True
            return False

    def delete_vip(self, user_id):
        with self.connection:
            user = self.cursor.execute(f'select `until_date` from `VIP` where `user_id` = ?;',
                                (user_id,)).fetchone()
            if user and user[0]:
                if datetime.datetime.now() >= datetime.datetime.strptime(
                        self.cursor.execute(f'select `until_date` from `VIP` where user_id = ?;',
                                            (user_id,)).fetchone()[0], '%Y-%m-%d %H:%M:%S'):
                    self.cursor.execute(f'delete from `VIP` where `user_id` = ?;',
                                        (user_id,))
                    return True

    def get_chat_title(self, chat_id):
        with self.connection:
            return self.cursor.execute('select `title` from `groups` where `group_id` = ?;', (chat_id,)).fetchone()[0]

    def black_list(self, user_id):
        with self.connection:
            if not bool(len(self.cursor.execute('select * from `banned` where `user_id` = ?', (user_id,)).fetchall())):
                return self.cursor.execute('insert into `banned` (`user_id`, `desc`) values (?,?);', (user_id, 'Добавлен в черный список'))

    def create_rp(self, cont, desc, pref, user_id):
        with self.connection:

            dates = self.cursor.execute(f'select `until_date` from `VIP` where user_id = ?;', (user_id,)).fetchone()[0]
            return self.cursor.execute('insert into `rpcontext` (`com`, `desc`, `prefix`, `until_date`, `user_id`) values (?,?,?,?,?);', (cont, desc, pref, dates, user_id))

    def delete_rp(self, user_id):
        with self.connection:
            user = self.cursor.execute(f'select `until_date` from `rpcontext` where `user_id` = ?;',
                                (user_id,)).fetchone()
            if user and user[0]:
                return self.cursor.execute(f'delete from `rpcontext` where user_id = ?;',
                                    (user_id,))

    def get_all_admin(self, chat_id):
        with self.connection:
            owners = self.owners()
            admins = self.cursor.execute(f'select `first_name`, `user_id` from `{str(chat_id)}` where `is_admin` = ?;', (1,)).fetchall()
            moders = self.cursor.execute(f'select `first_name`, `user_id` from `{str(chat_id)}` where `is_moder` = ?;', (1,)).fetchall()
            return admins, moders, owners

    def get_all_rp(self):
        with self.connection:
            return self.cursor.execute('select * from `rpcontext` where `user_id` = ?', (0,)).fetchall()

    def get_rp(self, com):
        with self.connection:
            return self.cursor.execute('select `desc`, `prefix`, `user_id` from `rpcontext` where `com` = ?', (com, )).fetchone()

    def rp_user(self, user_id):
        with self.connection:
            return self.cursor.execute('select `com`, `desc`, `id` from `rpcontext` where `user_id` = ?',
                                       (user_id, )).fetchall()

    def rp_delete(self, user_id, com):
        with self.connection:
            return self.cursor.execute('delete from `rpcontext` where `user_id` = ? and `com` = ?',
                                       (user_id, com))

    def rp_delete_by_id(self, rp_id):
        with self.connection:
            return self.cursor.execute('delete from `rpcontext` where `id` = ?', (int(rp_id), ))

    def check_rp(self):
        with self.connection:
            return self.cursor.execute('select `com` from `rpcontext`').fetchall()

    def info_chat(self, chat_id):
        with self.connection:
            return self.cursor.execute(f'select * from `{str(chat_id)}`').fetchall()

    def refresh(self):
        with self.connection:
            weddings = self.cursor.execute('select `wedding`, `user_id` from `-1001781348153`').fetchall()
            for wedding in weddings:
                if wedding[0] != '0':
                    wed = wedding[0].split('](')
                    weds = f'<a href = "tg://user?id={wed[1][13:-1]}">{wed[0][1:]}</a>'
                    print(weds)
                    print(self.cursor.execute('update `-1001781348153` set `wedding` = ? where `user_id` = ?;', (weds, wedding[1])))


    # антифлуд

    def check_flood(self, chat_id, message, user_id, message_id):
        with self.connection:
            mes, count, last_message, mes_id = self.cursor.execute(f'select `message`, `count`, `last_message`, `message_id` from `{str(chat_id)}` where `user_id` = ?;', (user_id,)).fetchone()
            limit = datetime.datetime.now().second - datetime.datetime.strptime(last_message, '%Y-%m-%d %H:%M:%S').second
            if count == 3:
                self.cursor.execute(f'update `{str(chat_id)}` set `message` = ?, `count` = ? where user_id = ?;',
                                           (message, 0, user_id))
                return mes_id
            if mes:
                if mes == message and limit < 3:
                    count += 1
                    message_id = mes_id
                else:
                    count = 0
                    message_id = message_id
                self.cursor.execute(f'update `{str(chat_id)}` set `message` = ?, `count` = ?, `message_id` = ? where user_id = ?;',
                                           (message, count, message_id, user_id))
                return
            else:
                self.cursor.execute(f'update `{str(chat_id)}` set `message` = ?, `count` = ?, `message_id` = ? where user_id = ?;', (message, 0, message_id, user_id))
                return


                # Блок храненения
    def period_contain(self, chat_id=0, user_id=0, price=0, period=0, params=None):
        with self.connection:
            if params:
                return self.cursor.execute('select `prefix_price`, `prefix_period`, `chat_id` from `constants` where `user_id` = ?;', (user_id,)).fetchone()
            elif chat_id:
                return self.cursor.execute('update `constants` set `chat_id` = ? where user_id = ?', (chat_id, user_id))
            else:
                return self.cursor.execute('insert into `constants` (`prefix_price`, `prefix_period`, `user_id`) values (?,?,?);', (price, period, user_id))

    def check_constaints(self, user_id):
        with self.connection:
            return bool(len(self.cursor.execute('select * from `constants` where `user_id` = ?;', (user_id,)).fetchall()))

    def delete_constant(self, user_id):
        with self.connection:
            return self.cursor.execute('DELETE from `constants` where `user_id` = ?', (user_id,))

    def set_period(self, chat_id, user_id, period):
        with self.connection:
            dates = datetime.datetime.now() + datetime.timedelta(days=period)
            self.cursor.execute(f'update `{str(chat_id)}` set `prefix_off` = ? where `user_id` = ?;', (dates.strftime('%Y-%m-%d %H:%M:%S'), user_id))
            return dates.strftime('%Y-%m-%d %H:%M:%S')


    def all_pref(self, chat_id):
        with self.connection:
            return self.cursor.execute(f'select `prefix_off`, `user_id` from `{str(chat_id)}`;').fetchall()

    def delete_prefix(self, chat_id, user_id):
        with self.connection:
            if self.cursor.execute(f'select `prefix_off` from `{str(chat_id)}` where user_id = ?;', (user_id,)).fetchone()[0]:
                if datetime.datetime.now() >= datetime.datetime.strptime(self.cursor.execute(f'select `prefix_off` from `{str(chat_id)}` where user_id = ?;', (user_id,)).fetchone()[0],'%Y-%m-%d %H:%M:%S'):
                    self.cursor.execute(f'update `{str(chat_id)}` set `prefix_off` = ? where user_id = ?;',
                                        ('', user_id))
                    return True

    def get_prefix(self, chat_id, user_id):
        with self.connection:
            if self.cursor.execute(f'select `prefix_off` from `{str(chat_id)}` where user_id = ?;', (user_id,)).fetchone()[0]:
                self.cursor.execute(f'update `{str(chat_id)}` set `prefix_off` = ? where user_id = ?;',
                                    ('', user_id))
                return True
            else:
                return False


    def user_contain(self, user_id, from_id=0, chat_id=0, mention=0, read=0):
        with self.connection:
            if not read:
                return self.cursor.execute(f'insert into `constants` (`user_id`, `from_id`, `chat_id`, `mention`) values (?,?,?,?);', (user_id, from_id, chat_id, mention))
            else:
                return self.cursor.execute(f'select `from_id`, `chat_id`, `mention` from `constants` where user_id = ?;', (user_id,)).fetchone()

    def wedding_constaint(self, chat_id, person_first_name, person_id, person_two_first_name, person_two_id):
        with self.connection:
            return self.cursor.execute(f'insert into `constants` (`user_id`, `chat_id`, `person_first_name`, `person_id`, `person_two_first_name`, `person_two_id`) values (?,?,?,?,?,?);', (person_two_id, chat_id, person_first_name, person_id, person_two_first_name, person_two_id))

    def get_wedding_const(self, user_id, chat_id):
        with self.connection:
            return self.cursor.execute('select `person_first_name`, `person_id`, `person_two_first_name`, `person_two_id` from `constants` where `user_id` = ? and `chat_id` = ?;', (user_id, chat_id)).fetchone()


    def create_setting(self):
        with self.connection:
            self.cursor.execute(
                """insert into `setting` (`id`) values (?);""",
                (1,)
            )

    def wedding(self, chat_id, user_id, wedding):
        with self.connection:
            self.cursor.execute(f'update `{str(chat_id)}` set `wedding` = ?, `wedding_time` = ? where `user_id` = ?;', (wedding, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
            return

    def get_wedding(self, chat_id, user_id):
        with self.connection:
            return self.cursor.execute(f'select `wedding` from `{str(chat_id)}` where `user_id` = ?;', (user_id, )).fetchone()

    def get_pair(self, chat_id):
        with self.connection:
            return self.cursor.execute(f'select `user_id`, `first_name`, `wedding`, `wedding_time` from `{str(chat_id)}`').fetchall()

    # Блок настроек
    def setting(self):
        with self.connection:
            return self.cursor.execute('select * from `setting` where `id` = ?', (1,)).fetchone()

    def set_money_game(self, money):
        with self.connection:
            return self.cursor.execute(f"update `setting` set `money_for_game` = ? where id = ?;", (money, 1))

    def get_money_game(self):
        with self.connection:
            return self.cursor.execute('select `money_for_game` from `setting`where id = ?', (1,)).fetchone()

    def set_exp_message(self, exp):
        with self.connection:
            return self.cursor.execute(f"update `setting` set `exp_for_message` = ? where id = ?;", (exp, 1))

    def get_exp_message(self):
        with self.connection:
            return self.cursor.execute('select `exp_for_message` from `setting` where id = ?;', (1,)).fetchone()

    def set_group_message(self, group):
        with self.connection:
            return self.cursor.execute('update `setting` set `id_group_log` = ? where id = ?;', (group, 1))

    def get_group_message(self):
        with self.connection:
            return self.cursor.execute('select `id_group_log` from `setting` where id = ?;', (1,)).fetchone()

    def set_gif(self, gif):
        with self.connection:
            return self.cursor.execute('update `setting` set `gif` = ? where id = ?;', (gif, 1))

    def get_gif(self):
        with self.connection:
            return self.cursor.execute('select `gif` from `setting` where id = ?;', (1, )).fetchone()


    # Блок остальной
    def show_time_create(self, params, chat_id, user_id):
        with self.connection:
            return self.cursor.execute(f'select `{params}` from `{str(chat_id)}` where user_id = ?;', (user_id,)).fetchone()[0]

    def show_info(self, chat_id, user_id):
        with self.connection:
            return self.cursor.execute(f'select * from `{str(chat_id)}` where user_id = ?;', (user_id,)).fetchone()

    def all_group(self):
        with self.connection:
            return self.cursor.execute('select `group_id`, `title` from `groups`').fetchall()

    def set_owner(self, user_id):
        with self.connection:
            return self.cursor.execute(f"insert into `main` (`owner_id`) values (?);", (user_id,))

    def get_owner(self, user_id):
        with self.connection:
            return bool(self.cursor.execute(f"select `id` from `main` where `owner_id` = ?;", (user_id,)).fetchone())

    def owners(self):
        with self.connection:
            return self.cursor.execute(f'select `owner_id` from `main`;').fetchall()

    def delete_owner(self, user_id):
        with self.connection:
            return self.cursor.execute('DELETE from `main` where `owner_id` = ?', (user_id,))

    def set_banned(self, user_id, desc='Забанен'):
        with self.connection:
            return self.cursor.execute(f"insert into `banned` (`user_id`, `desc`) values (?,?);", (user_id, desc))

    def delete_banned(self, user_id):
        with self.connection:
            return self.cursor.execute('DELETE from `banned` where `user_id` = ?', (user_id,))

    def get_banned(self, user_id):
        with self.connection:
            return bool(self.cursor.execute(f"select `id` from `banned` where `user_id` = ?;", (user_id,)).fetchone())

    def set_admin(self, chat_id, user_id, admin=0):
        with self.connection:
            return self.cursor.execute(f"update `{str(chat_id)}` set `is_admin` = ? where user_id =  ?;", (admin, user_id))

    def get_admin(self, chat_id, user_id):
        with self.connection:
            return self.cursor.execute(f"select `is_admin` from `{str(chat_id)}` where `user_id` = ?;", (user_id,)).fetchone()[0]

    def set_moder(self, chat_id, user_id, moder=0):
        with self.connection:
            return self.cursor.execute(f"update `{str(chat_id)}` set `is_moder` = ? where user_id =  ?;", (moder, user_id))

    def get_moder(self, chat_id, user_id):
        with self.connection:
            return self.cursor.execute(f"select `is_moder` from `{str(chat_id)}` where `user_id` = ?;", (user_id,)).fetchone()[0]

    def user_exists(self, chat_id, user_id):
        with self.connection:
            result = self.cursor.execute(f"select * from `{str(chat_id)}` where `user_id` = ?;", (user_id, )).fetchall()
            return bool(len(result))

    def get_user(self, chat_id, username):
        with self.connection:
            user = self.cursor.execute(f"select `user_id`, `first_name` from `{str(chat_id)}` where `username` = ?;", (username,)).fetchone()
            return user

    def get_user_id(self, chat_id, first_name):
        with self.connection:
            user = self.cursor.execute(f"select `user_id` from `{str(chat_id)}` where `first_name` = ?;", (first_name,)).fetchone()
            return user

    def add_user(self, chat_id, user_id, username, first_name, is_active):
        with self.connection:
            return self.cursor.execute(f"insert into `{str(chat_id)}` (`user_id`, `username`, `create_time`, `last_message`, `first_name`, `is_active`) values (?,?,?,?,?,?);", (user_id, username, datetime.date.today(), datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), first_name, is_active ))

    def active(self, chat_id, user_id, active):
        with self.connection:
            return self.cursor.execute(f"update `{str(chat_id)}` set `is_active` = ? where user_id = ?;",(active, user_id))

    def add_time_message(self, chat_id, user_id):
        with self.connection:
            count = self.cursor.execute(f"select `count_message` from `{str(chat_id)}` where `user_id` = ?;", (user_id,)).fetchone()[0]
            if count:
                return self.cursor.execute(f"update `{str(chat_id)}` set `last_message` = ?, `count_message` = ? where user_id = ?;", (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),count+1, user_id))
            else:
                return self.cursor.execute(f"update `{str(chat_id)}` set `first_message` = ?, `count_message` = ?, `last_message` = ? where user_id = ?;",
                                           (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), count+1, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))

    def mute(self, chat_id, user_id):
        with self.connection:
            return self.cursor.execute(f"select `mute` from `{str(chat_id)}` where `user_id` = ?;", (user_id, )).fetchone()[0]

    def add_mute(self, chat_id, user_id, mute, reason):
        with self.connection:
            return self.connection.execute(
                f"update `{str(chat_id)}` set `mute` = ?, `time_mute` = ?, `mute_reason` = ? where `user_id` = ?;",
                (mute, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), reason, user_id)
            )

    def update_mute(self, chat_id, user_id):
        with self.connection:
            mute = self.mute(chat_id, user_id) - 1
            if mute <= 0:
                mute = 0
            return self.connection.execute(
                f"update `{str(chat_id)}` set `mute` = ? where `user_id` = ?;",
                (mute, user_id)
            )

    def get_ban(self, chat_id, user_id):
        with self.connection:
            return self.cursor.execute(f"select `ban` from `{str(chat_id)}` where `user_id` = ?;", (user_id, )).fetchone()[0]

    def add_ban(self, chat_id, user_id, ban):
        with self.connection:
            if ban:
                return self.cursor.execute(f"update `{str(chat_id)}` set `ban` = ?, `time_ban` = ?, `mute` = ? where `user_id` = ?;", (int(ban),  datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0, user_id))
            else:
                return self.cursor.execute(
                    f"update `{str(chat_id)}` set `ban` = ? where `user_id` = ?;",
                    (int(ban), user_id))

    def unwarn(self, chat_id, user_id, warn):
        with self.connection:
            if not warn:
                return self.cursor.execute(f"update `{str(chat_id)}` set `mute` = ? where `user_id` = ?;", (warn, user_id))
            else:
                mute = self.cursor.execute(f"select `mute` from `{str(chat_id)}` where `user_id` = ?;",
                                           (user_id,)).fetchone()[0]
                if mute > warn:
                    mute -= warn
                else:
                    mute = 0
                return self.cursor.execute(f"update `{str(chat_id)}` set `mute` = ? where `user_id` = ?;",
                                           (mute, user_id))


    def update_user(self, chat_id, user_id, username, first_name):
        with self.connection:
            return self.cursor.execute(f"update `{str(chat_id)}` set `first_name` = ?, `username` = ? where `user_id` = ?;",
                                       (first_name, username, user_id))

    def get_first_name(self, chat_id, first_name):
        with self.connection:
            return bool(len(self.cursor.execute(f'select * from `{str(chat_id)}` where first_name = ?;',(first_name,)).fetchall()))

    def get_username(self, chat_id, user_id):
        with self.connection:
            return self.cursor.execute(f'select `first_name` from `{str(chat_id)}` where `user_id` = ?;',(user_id,)).fetchone()

    def cash_db(self, user_id):
        with self.connection:
            groups = self.all_group()
            cash = 0
            for group in groups:
                if self.user_exists(group[0], user_id):
                    cash += self.cursor.execute(f'select `cash` from `{str(group[0])}` where `user_id` = ?;', (user_id,)).fetchone()[0]
            return cash

    def cash_one(self, chat_id, user_id):
        with self.connection:
            return self.cursor.execute(f'select `cash` from `{str(chat_id)}` where `user_id` = ?;', (user_id,)).fetchone()[0]

    def add_money(self, chat_id, user_id, cash):
        with self.connection:
            cash_db = self.cash_one(chat_id, user_id)
            return self.cursor.execute(f'update `{str(chat_id)}` set `cash` = ? where `user_id` = ?;', (cash_db + cash, user_id))

    def exp(self, chat_id, user_id):
        exp_rate = {
            'Новичок': range(0, 301),
            'Обыватель': range(301, 1001),
            'Опытный': range(1001, 2001),
            'Ветеран': range(2001, 5001)
        }
        with self.connection:
            count, exp = self.cursor.execute(f"select `count_message`, `exp` from `{str(chat_id)}` where `user_id` = ?;", (user_id,)).fetchone()
            exp = int(exp.split('/')[0])
            add_exp = self.cursor.execute('select `exp_for_message` from `setting` where `id` = ?;', (1,)).fetchone()[0]
            if count:
                exp += add_exp
            if exp >= 5000:
                exps = exp
                role = 'Легендарный'
            else:
                for k, v in exp_rate.items():
                    if exp in v:
                        role = k
                        exps = f'{exp}/{max(v)}'
            return self.cursor.execute(
                f"update `{str(chat_id)}` set `role` = ?, `exp` = ? where user_id = ?;",
                (role, exps, user_id)
            )

    def select_all(self, chat_id):
        with self.connection:
            return self.cursor.execute(f'select `user_id`, `first_name` from `{chat_id}` where `is_active` = ?', (1, )).fetchall()