#!/usr/bin/env python
"""
Asynchronous Telegram Echo Bot example.

This is a simple bot that echoes each message that is received onto the chat.
It uses the Starlette ASGI framework to receive updates via webhook requests.
"""

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, Update
from dotenv import load_dotenv
import random
import string
import os

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")

WEBHOOK_HOST = os.getenv("WEBHOOK_DOMAIN")  # Domain name or IP address
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT"))  # Local port
WEBHOOK_LISTEN = "0.0.0.0"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/webhook"
secret_token_length = 20
WEBHOOK_SECRET_TOKEN = ''.join(random.choices(string.ascii_uppercase + string.digits, k=secret_token_length))

bot = AsyncTeleBot(token=API_TOKEN)

# BOT HANDLERS
@bot.message_handler(commands=["help", "start"])
async def send_welcome(message: Message):
    """
    Handle '/start' and '/help'
    """
    await bot.reply_to(
        message,
        ("Hi there, I am EchoBot.\n" "I am here to echo your kind words back to you."),
    )


@bot.message_handler(func=lambda _: True, content_types=["text"])
async def echo_message(message: Message):
    """
    Handle all other messages
    """
    await bot.reply_to(message, message.text)


# WEBSERVER HANDLERS
async def telegram(request: Request) -> Response:
    """Handle incoming Telegram updates."""
    print('Telegram update received')
    token_header_name = "X-Telegram-Bot-Api-Secret-Token"
    if request.headers.get(token_header_name) != WEBHOOK_SECRET_TOKEN:
        print('Rejected update, wrong secret token')
        return PlainTextResponse("Forbidden", status_code=403)
    print('Processing update')
    await bot.process_new_updates([Update.de_json(await request.json())])
    return Response()


async def startup() -> None:
    """Register webhook for telegram updates."""
    
    print(
        f"updating webhook:\nnew url: {WEBHOOK_URL}\nnew token: {WEBHOOK_SECRET_TOKEN}"
    )
    if not await bot.set_webhook(
        url=WEBHOOK_URL, secret_token=WEBHOOK_SECRET_TOKEN
    ):
        raise RuntimeError("unable to set webhook")


async def run() -> None:
    print('Starting starlette app')
    app = Starlette(
        routes=[
            Route("/webhook", telegram, methods=["POST"]),
        ],
        on_startup=[startup],
    )

    print('Starting uvicorn server')
    uvicorn.run(
        app,
        host=WEBHOOK_LISTEN,
        port=WEBHOOK_PORT
    )