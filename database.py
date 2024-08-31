import mysql.connector
import asyncio
from multiprocessing import Process
from aiogram import Bot
from dotenv import load_dotenv
import os

load_dotenv()

bd = mysql.connector.connect(
    host= os.getenv('HOST'),
    port= os.getenv("PORT"),
    user= os.getenv('USER'),
    passwd= os.getenv('PASSWORD'),
    database= os.getenv('DATABASE')
)

cursor = bd.cursor(buffered=True)

cursor.execute("""CREATE TABLE IF NOT EXISTS ownerbots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner VARCHAR(50),
    bot_to VARCHAR(255),
    max_mes VARCHAR(50),
    min_mes VARCHAR(50),
    couldown VARCHAR(50),
    bot_name VARCHAR(50)
)""")


class DataBase:
    def set_max_mes(self, token, value):
        cursor.execute("UPDATE ownerbots SET max_mes = %s WHERE bot_to = %s", (value, token))
        bd.commit()

    def set_min_mes(self, token, value):
        cursor.execute("UPDATE ownerbots SET min_mes = %s WHERE bot_to = %s", (value, token))
        bd.commit()

    def set_couldown(self, token, value):
        cursor.execute("UPDATE ownerbots SET couldown = %s WHERE bot_to = %s", (value, token))
        bd.commit()

    def get_max_mes(self, token):
        cursor.execute("SELECT max_mes FROM ownerbots WHERE bot_to = %s", (token,))
        return int(cursor.fetchone()[0])

    def get_min_mes(self, token):
        cursor.execute("SELECT min_mes FROM ownerbots WHERE bot_to = %s", (token,))
        return int(cursor.fetchone()[0])

    def get_couldown(self, token):
        cursor.execute("SELECT couldown FROM ownerbots WHERE bot_to = %s", (token,))
        return int(cursor.fetchone()[0])

    def get_owners_bots(self, owner_id):
        cursor.execute("SELECT bot_name, bot_to FROM ownerbots WHERE owner = %s", (owner_id,))
        rows = cursor.fetchall()
        return rows

    def get_bot_name(self, token):
        cursor.execute("SELECT bot_name FROM ownerbots WHERE bot_to = %s", (token,))
        return cursor.fetchone()[0]

    def get_bot(self, token):
        cursor.execute("SELECT * FROM ownerbots WHERE bot_to = %s", (token,))
        row = cursor.fetchone()
        return row

    def del_bot(self, token):
        cursor.execute("DELETE FROM ownerbots WHERE bot_to = %s", (token,))
        bd.commit()

    async def add_bot(self, owner_id, bot_to):
        cursor.execute("INSERT INTO ownerbots (owner, bot_to, max_mes, min_mes, couldown) VALUES (%s, %s, %s, %s, %s)",
                       (owner_id, bot_to, 4, 2, 3))
        bd.commit()
        bot = Bot(bot_to)
        me = await bot.get_me()
        cursor.execute("UPDATE ownerbots SET bot_name = %s WHERE bot_to = %s", (me.username, bot_to))
        bd.commit()

    async def get_tokens(self):
        cursor.execute("SELECT bot_to FROM ownerbots")
        return [token[0] for token in cursor.fetchall()]
