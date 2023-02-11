import re

from requests import RequestException
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import os
import json
import time
from random import choice


class ThemeReply:
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.session.headers.update({'user-agent': self.ua.random})
        self.themes = None
        self.themes = None
        self.message = None
        self.delay = None
        self.xftoken = None
        self.username = None
        self.cookie_load()

    def data_load(self):
        self.themes = input('Ссылка(и) на тему:')
        self.themes = re.sub(r'page-\d+#post-\d+', '', self.themes)
        self.themes = re.sub(r'page-\d+', '', self.themes)
        self.themes = self.themes.replace(' ', '').split(',')
        self.message = input('Сообщение(я):')
        self.message = self.message.replace(' ', '').split(',')

        self.delay = input('Задержка в секундах:')

    def cookie_load(self):
        if not os.path.isfile('cookie.txt'):
            os.mkdir('cookie.txt')
            print('Edit cookie.txt')
            input()
            exit()
        with open('cookie.txt') as f:
            cookies_lines = json.load(f)
            for line in cookies_lines:
                if 'name' in line:
                    self.session.cookies[line['name']] = line['value']

    def is_login(self):
        response = self.session.get(f'https://mistaua.com/')
        req_bs = BeautifulSoup(response.text, 'lxml')
        if not req_bs.select_one('img[class="navTab--visitorAvatar"]'):
            return False
        return True

    def get_xftoken(self):
        try:
            response = self.session.get(self.themes[0])
            token_bs = BeautifulSoup(response.content, 'lxml')
            token = token_bs.find('input', {'name': '_xfToken'})['value']
            self.xftoken = token
        except RequestException as e:
            raise e
        else:
            return token

    @staticmethod
    def get_last_date(soup_content):
        try:
            last_date = soup_content.select_one('input[name="last_date"]').get('value')
            return last_date
        except Exception as e:
            raise e

    @staticmethod
    def get_last_known_date(soup_content):
        try:
            last_known_date = soup_content.select_one('input[name="last_known_date"]').get('value')
            return last_known_date
        except Exception as e:
            print(e)
            return False

    def get_username(self):
        try:
            response = self.session.get('https://mistaua.com')
            soup = BeautifulSoup(response.content, 'lxml')
            try:
                self.username = soup.select_one('b[id="NavigationAccountUsername"]').text
            except Exception as e:
                raise e
        except RequestException as e:
            raise e

    def reply_theme(self):
        try:
            self.data_load()
            self.get_username()
            self.get_xftoken()
            data = {
                'message_html': '',
                'last_date': '',
                'last_known_date': '',
                '_xfToken': self.xftoken,
                '_xfRequestUri': '',
                '_xfNoRedirect': 1,
                '_xfResponseType': 'json'
            }
            while True:
                for link in self.themes:
                    print(link)
                    response = self.session.get(link)
                    soup = BeautifulSoup(response.content, 'lxml')
                    last_page = self.get_last_theme_page(soup)
                    if not last_page:
                        last_page = 1
                    response = self.session.get(f'{link}page-{last_page}')
                    soup = BeautifulSoup(response.content, 'lxml')
                    if self.check_last_reply(soup):
                        last_known_date = self.get_last_known_date(soup)
                        if not last_known_date:
                            self.themes.remove(link)
                            continue
                        last_date = self.get_last_date(soup)
                        data['last_date'] = last_date
                        data['last_known_date'] = last_known_date
                        _xf_request_uri = response.url.replace('https://mistaua.com/', '')
                        data['_xfRequestUri'] = _xf_request_uri
                        data['message_html'] = f'<p>{choice(self.message)}</p>'
                        response = self.session.post(f'{link}add-reply', data=data)
                        print(response.text)
                    time.sleep(10)
                time.sleep(int(self.delay))
        except RequestException as e:
            raise e

    def check_last_reply(self, soup_content):
        try:
            last_reply = soup_content.select('li[class="message"]')
            last_reply_name = last_reply[-1].get('data-author')
            if self.username in last_reply_name:
                return False
            else:
                return True
        except Exception as e:
            raise e

    @staticmethod
    def get_last_theme_page(soup_content):
        try:
            last_theme_data = soup_content.select_one('div[class="PageNav"]').get('data-last')
            return last_theme_data
        except Exception as e:
            print(e)
            return False


def main():
    print('Ссылки\\Сообщения вводить через запятую.')
    reply = ThemeReply()
    if reply.is_login():
        print('Login successful')
        reply.reply_theme()
    else:
        print('Login fail')


if __name__ == '__main__':
    main()
