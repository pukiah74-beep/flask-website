import threading
import time
import requests
import json
import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# --- CONFIG ---
DB_FILE = "database_key.json"
BOT_STATE = {"running": False, "token": None, "logs": []}

# --- DATABASE HANDLER ---
def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f: json.dump({"keys": {}}, f, indent=4)
    else:
        try:
            with open(DB_FILE, "r") as f:
                if not f.read().strip(): raise ValueError
        except:
            with open(DB_FILE, "w") as f: json.dump({"keys": {}}, f, indent=4)

def load_keys():
    init_db()
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {"keys": {}}

def save_keys(data):
    try:
        with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)
    except: pass

# --- LOGGER ---
def add_log(msg, color="default"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")
    BOT_STATE["logs"].append({"time": timestamp, "msg": msg, "color": color})
    if len(BOT_STATE["logs"]) > 60: BOT_STATE["logs"].pop(0)

# --- CORE ---
def send_message(token, channel_id, content):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    try:
        res = requests.post(url, headers=headers, json={"content": content}, timeout=10)
        return res.status_code
    except: return 500

def worker(interval, groups):
    add_log("🚀 Engine Started...", "success")
    while BOT_STATE["running"]:
        total_sent = 0
        # Loop Dinamis (Bisa A, B, C, D...)
        for grp_name, data in groups.items():
            targets = data.get('channels', [])
            msg = data.get('msg', "")
            
            if not targets: continue
            
            add_log(f"Processing Group {grp_name} ({len(targets)} Targets)...", "warning")
            for channel in targets:
                if not BOT_STATE["running"]: break
                
                cid, cname = channel['id'], channel['name']
                code = send_message(BOT_STATE["token"], cid, msg)
                
                if code == 200:
                    add_log(f"✅ Sent to #{cname}", "success")
                    total_sent += 1
                elif code == 429:
                    add_log("⚠️ Rate Limit! Sleeping 5s...", "danger")
                    time.sleep(5)
                else:
                    add_log(f"❌ Failed #{cname} ({code})", "danger")
                
                time.sleep(2) # Jeda aman per pesan
        
        if total_sent == 0:
            add_log("Waiting for tasks...", "default")

        if BOT_STATE["running"]:
            add_log(f"⏳ Cooldown {interval}s...", "default")
            time.sleep(int(interval))
            
    add_log("🛑 Engine Stopped.", "danger")

# --- ROUTES ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/verify_key', methods=['POST'])
def verify():
    k = request.json.get('key')
    db = load_keys()
    if k in db["keys"] and db["keys"][k]["status"] == "active":
        db["keys"][k]["status"] = "redeemed"
        db["keys"][k]["used_at"] = str(datetime.now())
        save_keys(db)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "msg": "Key Invalid or Used"})

@app.route('/api/login', methods=['POST'])
def login():
    t = request.json.get('token')
    if not t: return jsonify({"status": "error", "msg": "Token Empty"})
    try:
        res = requests.get("https://discord.com/api/v9/users/@me/guilds", headers={"Authorization": t}, timeout=10)
        if res.status_code == 200:
            BOT_STATE["token"] = t
            srvs = [{"id": s["id"], "name": s["name"]} for s in res.json()]
            return jsonify({"status": "success", "servers": srvs})
    except: pass
    return jsonify({"status": "error", "msg": "Token Invalid / Connection Error"})

@app.route('/api/get_channels', methods=['POST'])
def get_channels():
    if not BOT_STATE["token"]: return jsonify({"channels": []})
    gid = request.json.get('guild_id')
    try:
        res = requests.get(f"https://discord.com/api/v9/guilds/{gid}/channels", headers={"Authorization": BOT_STATE["token"]}, timeout=10)
        if res.status_code == 200:
            chans = [{"id": c["id"], "name": c["name"]} for c in res.json() if c['type'] == 0]
            return jsonify({"channels": chans})
    except: pass
    return jsonify({"channels": []})

@app.route('/api/start', methods=['POST'])
def start():
    if BOT_STATE["running"]: return jsonify({"status": "error"})
    BOT_STATE["running"] = True
    t = threading.Thread(target=worker, args=(request.json['interval'], request.json['groups']))
    t.daemon = True
    t.start()
    return jsonify({"status": "success"})

@app.route('/api/stop', methods=['POST'])
def stop():
    BOT_STATE["running"] = False
    return jsonify({"status": "success"})

@app.route('/api/logs')
def logs(): return jsonify(BOT_STATE["logs"])

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)