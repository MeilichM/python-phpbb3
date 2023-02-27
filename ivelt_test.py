from ivelt import phpBB
import json

with open("cfg.json", 'r', encoding='utf-8') as f:
    cfg = json.loads(f.read())

forum = phpBB()

if forum.login(cfg["username"], cfg["password"]):
    post_id = forum.postReply(cfg["topic_id"], cfg["message"], image="1.jpg")
    print(post_id)