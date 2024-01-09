from uvicorn import Server, Config
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, Update
from dotenv import load_dotenv
import datetime
import telebot
import aiohttp
import asyncio
import random
import string
import psutil
import os

load_dotenv()

secret_token_length = 20
status_message_id = None
API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_DOMAIN")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT"))
WEBHOOK_LISTEN = "0.0.0.0"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/webhook"
WEBHOOK_SECRET_TOKEN = "".join(
    random.choices(string.ascii_uppercase + string.digits, k=secret_token_length)
)
ADMIN_CHANNEL_ID = os.getenv("ADMIN_CHANNEL_ID")

bot = AsyncTeleBot(token=API_TOKEN)


async def get_location(remote_ip: str) -> dict:
    async with aiohttp.ClientSession() as session:
        url = f"https://ipapi.co/{remote_ip}/json/"
        async with session.get(url) as response:
            response = await response.json()
            location_data = {
                "ip": remote_ip,
                "city": response.get("city"),
                "region": response.get("region"),
                "country": response.get("country_name"),
            }
            return location_data


async def access_callback(log_entry):
    req = log_entry["request"]
    if req["uri"] != "/":
        return
    location_data = await get_location(req["remote_ip"])
    message = (
        f"CV access from {req['remote_ip']}.\n"
        f"Location: {location_data['city']}, {location_data['region']}, {location_data['country']}\n"
        "#access #cv"
    )
    await send_admin_message(message)


async def send_admin_message(message: str):
    await bot.send_message(ADMIN_CHANNEL_ID, message)


@bot.message_handler(commands=["start"])
async def handle_start(message):
    menu_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    status_button = telebot.types.KeyboardButton("VPS Status")
    menu_markup.add(status_button)

    await bot.send_message(
        message.chat.id,
        "Click 'VPS Status' to check the CPU, Memory, and Storage usage:",
        reply_markup=menu_markup,
    )


async def construct_vps_status():
    cpu_usage = psutil.cpu_percent(interval=1)  # Get CPU usage as a percentage
    memory_info = psutil.virtual_memory()
    storage_info = psutil.disk_usage("/")
    update_date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    response = (
        f"CPU Usage: {cpu_usage}%\n"
        f"Memory Usage:\n"
        f"  - Total: {memory_info.total / (1024 ** 3):.2f} GB\n"
        f"  - Used: {memory_info.used / (1024 ** 3):.2f} GB\n"
        f"Storage Usage:\n"
        f"  - Total: {storage_info.total / (1024 ** 3):.2f} GB\n"
        f"  - Used: {storage_info.used / (1024 ** 3):.2f} GB\n"
        f"Last updated: {update_date}"
    )

    return response


@bot.message_handler(func=lambda message: message.text == "VPS Status")
async def handle_vps_status(message):
    sent_message = await bot.send_message(message.chat.id, "Updating VPS status...")
    await asyncio.sleep(1)  # Delay to display the "Updating VPS status..." message

    # Remove the initial "VPS Status" message from the chat
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    response = await construct_vps_status()

    await bot.edit_message_text(
        response, chat_id=message.chat.id, message_id=sent_message.message_id
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
    if not await bot.set_webhook(url=WEBHOOK_URL, secret_token=WEBHOOK_SECRET_TOKEN):
        raise RuntimeError("unable to set webhook")


async def start_status_service():
    global status_message_id
    if status_message_id is None:
        status_message_id = await bot.send_message(
            ADMIN_CHANNEL_ID, "Starting status service..."
        )

    while True:
        status = await construct_vps_status()
        await bot.edit_message_text(
            status, chat_id=ADMIN_CHANNEL_ID, message_id=status_message_id
        )
        await asyncio.sleep(60)


async def run() -> None:
    """Run the bot."""

    # Start the status service
    asyncio.create_task(start_status_service())

    # WEBHOOK SERVER
    # Create the ASGI app for webhook
    app = Starlette(
        routes=[
            Route("/webhook", telegram, methods=["POST"]),
        ],
        on_startup=[startup],
    )

    # Run the webhook server
    config = Config(app=app, host=WEBHOOK_LISTEN, port=WEBHOOK_PORT)
    server = Server(config)

    await server.serve()
    await bot.close_session()
