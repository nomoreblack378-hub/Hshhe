import time
import json
import os
import requests
import random
from datetime import datetime
import pytz
from instagrapi import Client

# --- Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SESSION_ID = os.getenv("SESSION_ID")
TARGET_GROUP_IDS = ["746424351272036"] 
BOT_USERNAME = "mo.chi.351"
IST = pytz.timezone('Asia/Kolkata')

def is_sleeping_time():
    now = datetime.now(IST)
    return now.hour >= 0 and now.hour < 7

def get_ai_reply(user_message, username):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    system_prompt = (
        f"You are @{BOT_USERNAME}, a witty, flirty, and savage Indian girl. "
        "Reply in Hinglish. Keep it short (max 2 lines). If someone replies to you, "
        "be more engaging or savage based on their tone."
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
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def run_bot():
    if is_sleeping_time():
        print("😴 Indian Night Time: Bot is sleeping.")
        return

    cl = Client()
    cl.set_user_agent()

    try:
        cl.login_by_sessionid(SESSION_ID)
        my_id = cl.user_id
        print(f"✅ Logged in as {BOT_USERNAME} (ID: {my_id})")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        return

    processed_ids = set()
    if os.path.exists('processed.json'):
        with open('processed.json', 'r') as f:
            try: processed_ids = set(json.load(f))
            except: pass

    start_run = time.time()
    # 22 minutes loop
    while (time.time() - start_run) < 1320:
        for group_id in TARGET_GROUP_IDS:
            try:
                print(f"🔍 Checking group: {group_id}...")
                thread = cl.direct_thread(group_id, amount=10)
                messages = thread.messages 
                
                for msg in reversed(messages):
                    if msg.id in processed_ids:
                        continue
                    
                    # Apne messages ko skip karein
                    if str(msg.user_id) == str(my_id):
                        processed_ids.add(msg.id)
                        continue

                    text = (msg.text or "").lower()
                    
                    # Check 1: Mention (@username)
                    is_mentioned = f"@{BOT_USERNAME}".lower() in text
                    
                    # Check 2: Reply to bot's message
                    is_reply_to_me = False
                    if msg.reply_to_message:
                        if str(msg.reply_to_message.user_id) == str(my_id):
                            is_reply_to_me = True
                            print(f"💬 Found a reply to my message from user {msg.user_id}")

                    if is_mentioned or is_reply_to_me:
                        print(f"🎯 Responding to: {text}")
                        
                        # Simulating Human Speed
                        time.sleep(random.uniform(5, 10))
                        
                        sender = "User"
                        try:
                            # User info fetch karne mein delay daalein safety ke liye
                            sender = cl.user_info_v1(msg.user_id).username
                        except: pass
                        
                        reply_text = get_ai_reply(text, sender)
                        
                        if reply_text:
                            # Typing simulation
                            time.sleep(random.uniform(3, 7))
                            cl.direct_send(reply_text, thread_ids=[group_id], reply_to_message_id=msg.id)
                            print(f"✅ Reply sent to {sender}")
                    
                    processed_ids.add(msg.id)

            except Exception as e:
                print(f"⚠️ Loop Error: {e}")
                if "429" in str(e):
                    print("🚨 Rate limited. Stopping.")
                    return

        # Save progress
        with open('processed.json', 'w') as f:
            json.dump(list(processed_ids)[-100:], f)
            
        wait_time = random.randint(45, 90)
        print(f"😴 Waiting {wait_time}s for next check...")
        time.sleep(wait_time)

if __name__ == "__main__":
    run_bot()
    
