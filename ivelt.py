#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import codecs
import mimetypes
import http.cookiejar
from io import BytesIO
from time import sleep
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse, urlencode, urljoin
from urllib.request import build_opener, install_opener
from urllib.request import Request, HTTPCookieProcessor
from urllib.error import HTTPError


class phpBB(object):
    host = "https://www.ivelt.com/forum/"

    login_url = 'ucp.php?mode=login'
    post_url = 'viewtopic.php?f=%s&t=%i&p=%i#p%i'
    reply_url = 'posting.php?mode=reply&t={}'
    userpost_url = 'search.php?st=0&sk=t&sd=d&sr=posts&author_id=%i&start=%i'
    profile_url = 'memberlist.php?mode=viewprofile&u=%i'
    search_url = 'search.php?st=0&sk=t&sd=d&sr=posts&search_id=%s&start=%i'
    member_url = 'memberlist.php?sk=c&sd=d&start=%i'
    details_url = 'mcp.php?i=main&mode=post_details&f=%i&p=%i'

    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0'

    login_cookie_pattern = 'phpbb3_.*_u'

    login_form_id = 'login'
    delete_form_id = 'confirm'
    reply_form_id = 'postform'
    ucp_form_id = 'ucp'

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
    

    def postReply(self, topic, message, image = None):
        url = urljoin(self.host, self.reply_url.format(topic))
        try:
            form = self._get_form(url, self.reply_form_id)
            form['values']['message'] = message
            form['values']['post'] = 'Submit'

            if image:
                form['values']['uploadfile'] = (image, open(image, 'rb').read())

            body, content_type = self._encode_multipart_formdata(form['values'])
            headers = {'Content-Type': content_type}

            # wait at least 2 seconds so phpBB lets us post
            sleep(2)

            html = self._send_query(url, body, headers, encode=False)
            soup = BeautifulSoup(BytesIO(html), 'lxml')
            resp: Tag = soup.find_all('div', class_='post')[-1]
            
            if resp:
                return resp.get("id").replace("p", "")
            else:
                print('>>> no message')
                return

        except HTTPError as e:
            print(f'>>> Error {e.code}: {e.msg}')
            return


    def changeAvatar(self, imagefile):
        url = urljoin(self.host, self.profile_url % 'avatar')
        form = self._get_form(url, self.ucp_form_id)
        form['values']['uploadfile'] = (imagefile, open(imagefile, 'rb').read())
        form['values']['submit'] = 'Submit'
        body, content_type = self._encode_multipart_formdata(form['values'])
        headers = {'Content-Type': content_type, 'Content-length': str(len(body)), 'Referer': url}

        """ wait at least 2 seconds so phpBB let us post """
        sleep(2)

        html = self._send_query(url, body, headers, encode=False)
        soup = BeautifulSoup(BytesIO(html))
        error_msg = soup.find("div", id=self.ucp_form_id).find("p", "error").text
        if error_msg:
            print('Error: %s' % error_msg)
        resp = soup.find("div", id="message")
        if resp:
            print('>>> %s' % resp.p.text)
        else:
            print('>>> no message')