import time
import json
import os
import requests
import random
from datetime import datetime
import pytz
from instagrapi import Client

# Configuration from Secrets
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SESSION_ID = os.getenv("SESSION_ID")
TARGET_GROUP_IDS = ["746424351272036"]
BOT_USERNAME = "mo.chi.351"
IST = pytz.timezone('Asia/Kolkata')

def is_sleeping_time():
    now = datetime.now(IST)
    # Raat 12 se subah 7 tak band (Indian Time)
    if now.hour >= 0 and now.hour < 7:
        return True
    return False

def get_ai_reply(user_message, username):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    system_prompt = f"You are @{BOT_USERNAME}, a savage and flirty Indian girl. Use Hinglish. Keep it short."
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User {username} says: {user_message}"}
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return None

def run_bot():
    # --- SAFE START ---
    if is_sleeping_time():
        print("😴 Night time in India. Bot is sleeping to avoid ban.")
        return # Script yahan ruk jayega

    cl = Client()
    cl.set_user_agent() # Mobile fingerprint

    try:
        cl.login_by_sessionid(SESSION_ID)
        print("✅ Login Successful")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return

    processed_ids = set()
    # Tracking message IDs to avoid double replies
    if os.path.exists('processed.json'):
        with open('processed.json', 'r') as f:
            try: processed_ids = set(json.load(f))
            except: pass

    # GitHub Actions runtime limit (20 mins safe run)
    start_time = time.time()
    while (time.time() - start_time) < 1200: # 20 minutes loop
        for group_id in TARGET_GROUP_IDS:
            try:
                messages = cl.direct_thread(group_id, amount=3).messages
                for msg in reversed(messages):
                    if msg.id not in processed_ids and str(msg.user_id) != str(cl.user_id):
                        if f"@{BOT_USERNAME}".lower() in (msg.text or "").lower():
                            
                            # Natural delay
                            time.sleep(random.uniform(5, 10))
                            
                            reply = get_ai_reply(msg.text, "User")
                            if reply:
                                # Typing delay
                                time.sleep(random.uniform(3, 7))
                                cl.direct_send(reply, thread_ids=[group_id])
                                print("✉️ Sent Savage/Flirty Reply")
                        
                        processed_ids.add(msg.id)
            except Exception as e:
                print(f"⚠️ Error: {e}")
                if "429" in str(e): return # Rate limit par exit karo
        
        # Save progress
        with open('processed.json', 'w') as f:
            json.dump(list(processed_ids)[-100:], f)
        
        # Random interval between checks
        time.sleep(random.randint(60, 120))

if __name__ == "__main__":
    run_bot()
    
