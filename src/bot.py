from uvicorn import Server, Config
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, Update
from dotenv import load_dotenv
import aiohttp
import random
import string
import os

load_dotenv()

secret_token_length = 20
API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_DOMAIN")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT"))
WEBHOOK_LISTEN = "0.0.0.0"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/webhook"
WEBHOOK_SECRET_TOKEN = ''.join(random.choices(string.ascii_uppercase + string.digits, k=secret_token_length))
ADMIN_CHANNEL_ID = os.getenv("ADMIN_CHANNEL_ID")

bot = AsyncTeleBot(token=API_TOKEN)

async def get_location(remote_ip: str) -> dict:
    url = f'https://ipapi.co/{remote_ip}/json/'
    response = await aiohttp.ClientSession().get(url)
    response = await response.json()
    location_data = {
        "ip": remote_ip,
        "city": response.get("city"),
        "region": response.get("region"),
        "country": response.get("country_name")
    }
    return location_data

async def access_callback(log_entry):
    req = log_entry['request']
    if req['uri'] != '/':
        return
    location_data = await get_location(req['remote_ip'])
    await bot.send_message(ADMIN_CHANNEL_ID, f"CV access from {req['remote_ip']}.\nLocation: {location_data['city']}, {location_data['region']}, {location_data['country']}")

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
    token_header_name = "X-Telegram-Bot-Api-Secret-Token"
    if request.headers.get(token_header_name) != WEBHOOK_SECRET_TOKEN:
        return PlainTextResponse("Forbidden", status_code=403)
    await bot.process_new_updates([Update.de_json(await request.json())])
    return Response()


async def startup() -> None:
    """Register webhook for telegram updates."""
    if not await bot.set_webhook(
        url=WEBHOOK_URL, secret_token=WEBHOOK_SECRET_TOKEN
    ):
        raise RuntimeError("unable to set webhook")


async def run() -> None:
    """Run the server."""

    # Create the ASGI app
    app = Starlette(
        routes=[
            Route("/webhook", telegram, methods=["POST"]),
        ],
        on_startup=[startup],
    )

    # Run the server
    config = Config(app=app, host=WEBHOOK_LISTEN, port=WEBHOOK_PORT)
    server = Server(config)
    await server.serve()
    await bot.close_session()