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
from http.client import HTTPResponse

class phpBB(object):
    host = "https://www.ivelt.com/forum/"
    login_url = urljoin(host, 'ucp.php?mode=login')
    reply_topic = 'posting.php?mode=reply&t={}'
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0'

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
            body.write(bytes(f'--{boundary}\r\n', 'utf-8'))
            
            if isinstance(value, tuple):
                file, data = value
                writer(body).write(f'Content-Disposition: form-data; name="{name}"; filename="{file}"\r\n')
                body.write(bytes(f'Content-Type: {self._get_content_type(file)}\r\n\r\n', 'utf-8'))
            else:
                data = value
                writer(body).write(f'Content-Disposition: form-data; name="{name}"\r\n')
                body.write(bytes('Content-Type: text/plain\r\n\r\n', 'utf-8'))

            if isinstance(data, int):
                data = str(data)

            if isinstance(data, str):
                writer(body).write(data)
            else:
                body.write(data)

            body.write(bytes('\r\n', 'utf-8'))

        body.write(bytes(f'--{boundary}--\r\n', 'utf-8'))

        content_type = f'multipart/form-data; boundary={boundary}'
        return body.getvalue(), content_type

    def _get_content_type(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


    def _get_form(self, url, form_id):
        request = Request(url, headers={'User-Agent': self.user_agent})
        resp: HTTPResponse
        with self.opener.open(request) as resp:
            html = BeautifulSoup(resp, "lxml")
            form = html.find("form", id=form_id)

        if not form:
            with open('current.html', 'wb') as f:
                f.write(resp.read())
                print("dumped")
                return

        return self._get_form_values(form)
    
    def _get_form_values(self, soup: Tag):
        values = {}
        inputs: list[Tag] = soup.find_all("input")
        
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
        
        with self.opener.open(request) as resp:
            return resp.read()


    def _get_post_id(self, posts: list[Tag]):
        for post in posts[::-1]:
            post_id = post.get("id").replace("p", "")
            if post_id.isnumeric():
                return int(post_id)
            

    # def _stage_media(self, url, creation_time, form_token, img_path):
    def _stage_media(self):
        img_path = '1.jpg'
        topic = 60827
        url = urljoin(self.host, self.reply_topic.format(topic))
        
        form = self._get_form(url, 'postform')
        creation_time = form['values'][creation_time]
        form_token = form['values'][form_token]

        values = {
            "name": "random.jpg",
            "chunk": 0,
            "chunks": 1,
            "add_file": "אטעטש פייל",
            "creation_time": creation_time,
            "form_token": form_token,
            "realfilename": img_path,
            "fileupload": open(img_path, 'rb').read(),
        }
        
        body, content_type = self._encode_multipart_formdata(values)
        headers = {'Content-Type': content_type}
        return self._send_query(url, body, headers, encode=False)



    def login(self, username, password):
        form = self._get_form(self.login_url, 'login')
        form['values']['username'] = username
        form['values']['password'] = password
        form['values']['login'] = 'Login'
        self._send_query(self.login_url, form['values'])
        return self.isLogged()

    def isLogged(self):
        if self.jar:
            for cookie in self.jar:
                if re.search('phpbb3_.*_u', cookie.name) and cookie.value:
                    return True
        return False
    


    def respond(self, topic: int, message: str, images: list[str] = None):
        print('setup reply')
        url = urljoin(self.host, self.reply_topic.format(topic))
        try:
            
            form = self._get_form(url, 'postform')
            form['values']['message'] = message
            form['values']['post'] = 'Submit'
            form['values']['attach_sig'] = 1

            if images:

                creation_time = form['values'][creation_time]
                form_token = form['values'][form_token]

                for image_id, image_path in enumerate(images):
                    form['values']['fileupload'] = (image_path, open(image_path, 'rb').read())
                    form['values']['message'] = message + f"\n\n[attachment={image_id}]{image_path}[/attachment]"
                    
                    form['values'][f"attachment_data[{image_id}][attach_id]"] = "489171"
                    form['values'][f"attachment_data[{image_id}][is_orphan]"] = "1"
                    form['values'][f"attachment_data[{image_id}][real_filename]"] = "1.jpg"
                    form['values'][f"attachment_data[{image_id}][attach_comment]"] = ""
                    form['values'][f"attachment_data[{image_id}][filesize]"] = "105517"

            body, content_type = self._encode_multipart_formdata(form['values'])
            headers = {'Content-Type': content_type}

            print('send reply')
            sleep(2)
            html = self._send_query(url, body, headers, encode=False)

            soup = BeautifulSoup(BytesIO(html), 'lxml')
            posts: list[Tag] = soup.find_all('div', class_='post')

            if not posts:
                print('>>> no message')
                return
            
            post_id: int = self._get_post_id(posts)
            return post_id
        
        except HTTPError as e:
            print(f'>>> Error {e.code}: {e.msg}')
            return



if __name__ == '__main__':

    eshkol_id = '00000'
    msg = "דאס איז א טעסט"
    img_path = "1.jpg"
    nik = "דיין נאמען"
    password = "password123"

    forum = phpBB()
    login = forum.login(nik, password)

    if not login:
        print("login failed!")
        exit()

    print("posting")
    sleep(4)

    # post_id = forum.respond(eshkol_id, msg, image=img_path)
    # print(f"Post ID: {post_id}")
    data = forum._stage_media()
    print(data)