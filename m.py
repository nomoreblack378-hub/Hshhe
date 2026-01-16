import time
import json
import os
import requests
import random
from datetime import datetime
import pytz
from instagrapi import Client

# --- Setup ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SESSION_ID = os.getenv("SESSION_ID")
TARGET_GROUP_IDS = ["746424351272036"] 
BOT_USERNAME = "mo.chi.351"
IST = pytz.timezone('Asia/Kolkata')

def is_sleeping_time():
    """Returns True if current time in India is between 12 AM and 7 AM"""
    now = datetime.now(IST)
    return now.hour >= 0 and now.hour < 7

def get_ai_reply(user_message, username):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    # Updated Female Persona
    system_prompt = (
        f"You are @{BOT_USERNAME}, a cute but savage Indian girl. "
        "Your replies are flirty, witty, and in Hinglish. "
        "Keep them very short (1-2 lines maximum) like a real person chatting."
    )
    
    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User {username} said: {user_message}"}
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        return r.json()['choices'][0]['message']['content'].strip()
    except: return None

def run_bot():
    # --- STEP 1: NIGHT CHECK ---
    if is_sleeping_time():
        print("😴 Raat ho gayi hai India mein. Bot is sleeping to stay safe.")
        return

    cl = Client()
    cl.set_user_agent() # Mobile app ki tarah behave karega

    try:
        cl.login_by_sessionid(SESSION_ID)
        print(f"✅ Logged in as {BOT_USERNAME}")
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return

    processed_ids = set()
    if os.path.exists('processed.json'):
        with open('processed.json', 'r') as f:
            try: processed_ids = set(json.load(f))
            except: pass

    # --- STEP 2: ACTIVITY LOOP ---
    start_run = time.time()
    # 20 minutes tak chalega phir band ho jayega (next cycle tak)
    while (time.time() - start_run) < 1200:
        for group_id in TARGET_GROUP_IDS:
            try:
                # Sirf 3 latest messages check karega
                messages = cl.direct_thread(group_id, amount=3).messages 
                for msg in reversed(messages):
                    if msg.id not in processed_ids and str(msg.user_id) != str(cl.user_id):
                        text = (msg.text or "").lower()
                        
                        if f"@{BOT_USERNAME}".lower() in text:
                            # STEP 3: Reading Simulation (3-8 seconds)
                            time.sleep(random.uniform(3, 8))
                            
                            sender = "Friend"
                            try: sender = cl.user_info_v1(msg.user_id).username
                            except: pass
                            
                            reply = get_ai_reply(text, sender)
                            
                            if reply:
                                # STEP 4: Typing Simulation (Wait time based on length)
                                typing_speed = len(reply) * 0.12 + random.uniform(2, 5)
                                print(f"⌨️ Typing for {typing_speed:.1f}s...")
                                time.sleep(min(typing_speed, 12))
                                
                                cl.direct_send(reply, thread_ids=[group_id])
                        
                        processed_ids.add(msg.id)
            except Exception as e:
                print(f"⚠️ Error: {e}")
                if "429" in str(e): # Rate limit hit
                    print("🚨 Rate limit! Ending this cycle.")
                    return 

        # Progress save karein
        with open('processed.json', 'w') as f:
            json.dump(list(processed_ids)[-100:], f)
            
        # STEP 5: Variable Sleep (Don't use 30s fixed)
        wait = random.randint(60, 150)
        time.sleep(wait)

if __name__ == "__main__":
    run_bot()
    
