from bs4 import BeautifulSoup, Tag
from io import BytesIO
import pickle

with open('tests\iv_respns.html', 'rb') as f:
    html = f.read()

# raw_pickle = pickle.load(open('tests\html_response', 'rb'))
# readable = BytesIO(raw_pickle)
readable = BytesIO(html)
# readable = html.decode()
soup = BeautifulSoup(readable, 'lxml')
post: Tag = soup.find('div', class_='post')

post_id = post.get("id").replace("p", "")
if post_id.isnumeric():
    print(int(post_id))

print('hi')

# posts: list[Tag] = soup.find_all('div', class_='post').reverse()

# for post in posts:
#     post_id = post.get("id").replace("p", "")
#     if post_id.isnumeric():
#         print(int(post_id))
