from ivelt import phpBB
import json

with open("cfg.json", 'r', encoding='utf-8') as f:
    cfg = json.loads(f.read())

forum = phpBB()

if forum.login(cfg["username"], cfg["password"]):
    post_id, creation_time = forum.respond(cfg["topic_id"], cfg["message"], image="1.jpg")
    # post_id, creation_time = forum.postReply(cfg["topic_id"], cfg["message"], image="1.jpg", reply_to=(cfg['post_id'], cfg['time']))
    print(f"Post Id: {post_id}\nCreation Time: {creation_time}")