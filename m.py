import time
import json
import os
import requests
import random
from datetime import datetime
import pytz # Timezone handle karne ke liye
from instagrapi import Client

# --- Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SESSION_ID = os.getenv("SESSION_ID")
TARGET_GROUP_IDS = ["746424351272036"] 
BOT_USERNAME = "mo.chi.351"
TRACKING_FILE_IDS = 'last_message_ids.json'
TIMEZONE = pytz.timezone('Asia/Kolkata') # India Timezone

def is_sleeping_time():
    """Check karega ki kya abhi sone ka waqt hai (12 AM to 7 AM)"""
    now = datetime.now(TIMEZONE)
    current_hour = now.hour
    # Raat 12 se subah 7 baje tak bot band rahega
    if current_hour >= 0 and current_hour < 7:
        return True
    return False

def get_ai_reply(user_message, username):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    # Female Persona Logic
    system_prompt = (
        f"You are @{BOT_USERNAME}, a witty Indian girl. Your vibe is savage, funny, and flirty. "
        "Use Hinglish naturally. Keep replies short like a DM, not like an essay."
    )
    
    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User @{username}: {user_message}"}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        return response.json()['choices'][0]['message']['content'].strip()
    except:
        return None

def run_bot():
    cl = Client()
    cl.set_user_agent() # Randomize device

    try:
        cl.login_by_sessionid(SESSION_ID)
        print("✅ Safe Mode Activated.")
    except Exception as e:
        print(f"❌ Login Error: {e}")
        return

    processed_ids = set()
    if os.path.exists(TRACKING_FILE_IDS):
        with open(TRACKING_FILE_IDS, 'r') as f:
            try: processed_ids = set(json.load(f))
            except: processed_ids = set()

    while True:
        # --- 1. SLEEP LOGIC ---
        if is_sleeping_time():
            print(f"😴 It's sleeping time (12AM-7AM). Bot is resting...")
            time.sleep(1800) # 30 min baad phir check karega
            continue

        # --- 2. HUMAN BREAK LOGIC ---
        if random.random() < 0.05: 
            nap = random.randint(300, 900)
            print(f"☕ Taking a small human break for {nap} seconds...")
            time.sleep(nap)

        for group_id in TARGET_GROUP_IDS:
            try:
                messages = cl.direct_thread(group_id, amount=3).messages 
                for msg in reversed(messages):
                    if msg.id not in processed_ids and str(msg.user_id) != str(cl.user_id):
                        text = (msg.text or "").lower()
                        if f"@{BOT_USERNAME}".lower() in text:
                            
                            # Reading Delay (3-7 sec)
                            time.sleep(random.uniform(3, 7))
                            
                            sender = "Friend"
                            try: sender = cl.user_info_v1(msg.user_id).username
                            except: pass
                                
                            reply = get_ai_reply(text, sender)
                            
                            if reply:
                                # Typing Delay (Insaan ki tarah slow typing)
                                typing_time = len(reply) * 0.15 + random.uniform(2, 5)
                                print(f"⌨️ Typing for {typing_time:.1f}s...")
                                time.sleep(min(typing_time, 12))
                                
                                cl.direct_send(reply, thread_ids=[group_id])
                        processed_ids.add(msg.id)
            except Exception as e:
                if "429" in str(e):
                    print("🚨 Rate limit hit! Sleeping for 20 mins.")
                    time.sleep(1200)

        # Loop delay - Fixed intervals are bad, so we randomize
        time.sleep(random.randint(45, 120))

if __name__ == "__main__":
    run_bot()
