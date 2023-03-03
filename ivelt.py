#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import codecs
import mimetypes
import http.cookiejar
from io import BytesIO
from time import sleep
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlencode, urljoin
from urllib.request import build_opener, install_opener
from urllib.request import Request, HTTPCookieProcessor
from urllib.error import HTTPError


class phpBB(object):
    host = "https://www.ivelt.com/forum/"

    login_url = 'ucp.php?mode=login'

    reply_topic = 'posting.php?mode=reply&t={}'
    reply_post = 'posting.php?mode=quote&p={}'

    manual_quote_format = "[quote={} post_id={} time={} user_id={}][/quote]\n"

    login_form_id = 'login'
    reply_form_id = 'postform'

    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0'
    login_cookie_pattern = 'phpbb3_.*_u'

    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.jar))
        install_opener(self.opener)

    def _encode_multipart_formdata(self, fields, boundary=None):
        writer = codecs.lookup('utf-8')[3]
        body = BytesIO()

        if boundary is None:
            boundary = '----------b0uNd@ry_$'

        for name, value in getattr(fields, 'items')():
            body.write(bytes('--%s\r\n' % boundary, 'utf-8'))
            if isinstance(value, tuple):
                file, data = value
                writer(body).write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (name, file))
                body.write(bytes('Content-Type: %s\r\n\r\n' % (self._get_content_type(file)), 'utf-8'))
            else:
                data = value
                writer(body).write('Content-Disposition: form-data; name="%s"\r\n' % (name))
                body.write(bytes('Content-Type: text/plain\r\n\r\n', 'utf-8'))

            if isinstance(data, int):
                data = str(data)

            if isinstance(data, str):
                writer(body).write(data)
            else:
                body.write(data)

            body.write(bytes('\r\n', 'utf-8'))

        body.write(bytes('--%s--\r\n' % (boundary), 'utf-8'))

        content_type = f'multipart/form-data; boundary={boundary}'
        return body.getvalue(), content_type

    def _get_content_type(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def _get_html(self, url):
        headers = {}
        headers['User-Agent'] = self.user_agent
        request = Request(url, headers=headers)
        resp = self.opener.open(request)
        soup = BeautifulSoup(resp, "lxml")
        self.opener.close()
        return soup

    def _get_form_from_html(self, html, form_id):
        soup = BeautifulSoup(BytesIO(html))
        form = soup.find("form", id=form_id)
        return self._get_form_values(form)

    def _get_form(self, url, form_id):
        form = self._get_html(url).find("form", id=form_id)
        return self._get_form_values(form)

    def _get_form_values(self, soup):
        inputs = soup.find_all("input")
        values = {}
        for input in inputs:
            if input.get('type') == 'submit' or not input.get('name') or not input.get('value'):
                continue
            values[input['name']] = input['value']
        return {'values': values, 'action': soup['action']}

    def _send_query(self, url, query, extra_headers=None, encode=True):
        headers = {'User-Agent': self.user_agent}

        if extra_headers:
            headers.update(extra_headers)

        if encode:
            data = bytes(urlencode(query), 'utf-8')
        else:
            if not isinstance(query, bytes):
                data = bytes(query, 'utf-8')
            else:
                data = query

        request = Request(url, data, headers)
        resp = self.opener.open(request)
        html = resp.read()
        self.opener.close()
        return html
    
    def _get_post_id(posts: list[Tag]):
        for post in posts:
            post_id = post.get("id").replace("p", "")
            if post_id.isnumeric():
                return int(post_id)



    def login(self, username, password):
        form = self._get_form(urljoin(self.host, self.login_url), self.login_form_id)
        form['values']['username'] = username
        form['values']['password'] = password
        form['values']['login'] = 'Login'
        self._send_query(urljoin(self.host, self.login_url), form['values'])
        return self.isLogged()

    def isLogged(self):
        if self.jar != None:
            for cookie in self.jar:
                if re.search(self.login_cookie_pattern, cookie.name) and cookie.value:
                    return True
        return False
    


    def respond(self, topic: int, message: str, image: str = None, reply_to: tuple[int, int] = None):
        url = urljoin(self.host, self.reply_topic.format(topic))
        try:
            # if reply_to:
            #     quote = self.manual_quote_format.format('אידישליך', 4151780, 1677524972, 22552)
            #     message = quote + message

            form = self._get_form(url, self.reply_form_id)
            form['values']['message'] = message
            form['values']['post'] = 'Submit'
            form['values']['attach_sig'] = 1

            if image:
                form['values']['fileupload'] = (image, open(image, 'rb').read())
                # form['values']["attachment_data[0][real_filename]"] = image
                form['values']['message'] = message + f"\n\n[attachment=0]{image}[/attachment]"

            body, content_type = self._encode_multipart_formdata(form['values'])
            headers = {'Content-Type': content_type}

            sleep(2)
            html = self._send_query(url, body, headers, encode=False)

            soup = BeautifulSoup(BytesIO(html), 'lxml')
            posts: list[Tag] = soup.find_all('div', class_='post').reverse()

            if not posts:
                print('>>> no message')
                return
            
            post_id: int = self._get_post_id(posts)
            creation_time: int = int(form['values']['creation_time'])
            return post_id, creation_time

        except HTTPError as e:
            print(f'>>> Error {e.code}: {e.msg}')
            return


    def reply(self, post: int, message: str, image: str = None):
        url = urljoin(self.host, self.reply_post.format(post)) 