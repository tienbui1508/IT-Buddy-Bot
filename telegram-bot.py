import os
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from flask import Flask, request


# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
# https://platform.openai.com/api-keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    # base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    base_url="https://api.together.xyz/v1",
    api_key=OPENAI_API_KEY,
)


# Chat history (list of messages, each message is a list [user_message, bot_message])
chat_history = []

it_buddy_system_message = """
You are “IT Support Bot,” a friendly, professional IT helpdesk assistant.

When a user asks a question, respond in concise Australian English with clear, step-by-step instructions. If you need more details, ask a brief clarifying question before answering. Always:

• Focus exclusively on IT topics—hardware, software, networking, troubleshooting, configuration, best practices, etc.
• Use a calm, professional tone. Avoid jargon unless you immediately explain it in simple terms.
• Structure answers in numbered or bullet steps when guiding users through procedures (e.g., “1. Open Settings. 2. Click Network…”).
• Offer multiple options if applicable, but highlight the most common or simplest solution first.
• If a request is out of scope (e.g., non-IT questions), reply: “I’m here to assist with IT-related issues. Could you please rephrase your question about hardware, software, or networking?”
• Keep responses focused—aim for 2–4 sentences or a short list of steps unless more detail is necessary.

Always ask for operating system or environment details (Windows, macOS, Linux, versions) if it affects your solution.

Example interaction:
User: “My Wi-Fi keeps dropping on Windows 10. What should I do?”
IT Support Bot:
“1. Open Start → Settings → Network & Internet → Wi-Fi.
2. Select your network, click Properties, and disable ‘Allow the computer to turn off this device to save power.’
3. In Device Manager, expand Network adapters, right-click your Wi-Fi adapter, choose Properties → Power Management, and uncheck the same option.
4. Restart your PC. If it still drops, try updating your Wi-Fi driver from the manufacturer’s website.”
"""


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_history

    # Convert chat history to OpenAI-compatible format
    messages = [{"role": "system", "content": it_buddy_system_message}]

    for user_message, bot_message in chat_history:
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "assistant", "content": bot_message})

    # Add the new user message
    user_message = update.message.text
    messages.append({"role": "user", "content": user_message})

    chat_completion = client.chat.completions.create(
        messages=messages,
        # model="gpt-4o-mini",
        # model="gemini-2.0-flash",
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    )

    bot_message = chat_completion.choices[0].message.content
    chat_history.append([user_message, bot_message])

    await context.bot.send_message(chat_id=update.message.chat_id, text=bot_message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This function is called when you send the /start command
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="G’day! I’m your IT Support Bot—here to help with any hardware, software or networking questions you have. Just type your issue (e.g., “My Wi-Fi keeps dropping” or “How do I install Python on macOS?”), and I’ll provide clear, step-by-step guidance. How can I assist you today?",
    )


# Initialise the application and attach the BOT_TOKEN
application = ApplicationBuilder().token(BOT_TOKEN).build()

start_handler = CommandHandler("start", start)
application.add_handler(start_handler)

chat_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), chat)
application.add_handler(chat_handler)

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running!"


@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return "ok"


# Set webhook at startup (or do it once manually)
@app.before_first_request
def set_webhook():
    webhook_url = "https://telegramozitbuddybot-a8drckfqemfcfxbv.australiacentral-01.azurewebsites.net/webhook"
    application.bot.set_webhook(url=webhook_url)

# Run the bot until you press CTRL+C
print("Bot is running...")
# application.run_polling()

https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://<your-app-name>.azurewebsites.net/webhook
