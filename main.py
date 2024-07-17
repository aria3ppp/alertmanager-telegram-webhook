import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from telegram import Bot
from telegram.constants import ParseMode
import asyncio

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
auth = HTTPBasicAuth()

# Get sensitive information from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 5000))
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', '127.0.0.1')
WEBHOOK_USERNAME = os.getenv('WEBHOOK_USERNAME')
WEBHOOK_PASSWORD = os.getenv('WEBHOOK_PASSWORD')

# Ensure required environment variables are set
if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WEBHOOK_USERNAME, WEBHOOK_PASSWORD]):
    raise ValueError("TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WEBHOOK_USERNAME, and WEBHOOK_PASSWORD must be set in .env file")

users = {
    WEBHOOK_USERNAME: generate_password_hash(WEBHOOK_PASSWORD)
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_telegram_message(message):
    async with bot:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode=ParseMode.MARKDOWN)

@app.route('/webhook', methods=['POST'])
@auth.login_required
def webhook():
    data = request.json
    
    # Process the alert data
    alerts = data['alerts']
    for alert in alerts:
        status = alert['status']
        labels = alert['labels']
        annotations = alert['annotations']
        
        # Construct the message
        message = f"*Alert: {status.upper()}*\n"
        message += f"*Summary:* {annotations.get('summary', 'N/A')}\n"
        message += f"*Description:* {annotations.get('description', 'N/A')}\n"
        message += "\n*Labels:*\n"
        for key, value in labels.items():
            message += f"- {key}: {value}\n"
        
        # Send the message to Telegram
        asyncio.run(send_telegram_message(message))
    
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host=WEBHOOK_HOST, port=WEBHOOK_PORT)
