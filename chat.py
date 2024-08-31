import random
import re


class Chat:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.mess = []
        self.is_on = True
        self.now_mes = 0

    def get_mess(self):
        return self.mess 

    def add_mess(self, message):
        words = re.findall(r'\b\w+\b', message)
        self.mess = list(self.mess + words)



