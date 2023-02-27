from ivelt import phpBB
import json

# with open("cfg.json", 'r', encoding='utf-8') as f:
#     cfg = json.loads(f.read())

# forum = phpBB()

# if forum.login(cfg["username"], cfg["password"]):
#     forum.postReply(cfg["topic_id"], cfg["message"])

with open("ivelt_response.txt", "r", encoding="utf-8") as f:
    content = f.read()

with open("ivelt_response.html", "w") as i:
    i.write(content)