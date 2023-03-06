from ivelt import phpBB
from time import sleep
import json

with open("cfg.json", 'r', encoding='utf-8') as f:
    cfg = json.loads(f.read())

forum = phpBB()

print("logging in")
login = forum.login(cfg["username"], cfg["password"])

if not login:
    print("login failed!")
    exit()

print("posting")
sleep(3)
post_id = forum.respond(cfg["topic_id"], cfg["message"])
print(f"Post ID: {post_id}")
    
    # post_id, creation_time = forum.postReply(cfg["topic_id"], cfg["message"], image="1.jpg", reply_to=(cfg['post_id'], cfg['time']))
    # print(f"Post ID: {post_id}\nCreation Time: {creation_time}")