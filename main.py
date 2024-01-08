from src.log_server import start_log_listener
from src.bot import bot
from dotenv import load_dotenv
import asyncio
import os

import multiprocessing

async def simple_callback(log_entry):
    req = log_entry['request']
    if req['uri'] == '/':
        print(f"Access from {req['remote_ip']}")

async def main():

    load_dotenv()

    # Define the host and port where Caddy will send logs
    LOG_HOST = os.getenv('LOG_HOST')
    LOG_PORT = os.getenv('LOG_PORT')

    WEBHOOK_SSL_CERT = os.getenv('WEBHOOK_CERT')  # Path to the ssl certificate
    WEBHOOK_SSL_PRIV = os.getenv('WEBHOOK_PKEY')  # Path to the ssl private key
    WEBHOOK_DOMAIN = os.getenv('WEBHOOK_DOMAIN') # either domain, or ip address of vps

    await asyncio.gather(
        start_log_listener(LOG_HOST, LOG_PORT, callback=simple_callback),
        bot.run_webhooks(
            listen="0.0.0.0",
            port=5000,
            url_path='/',
            webhook_url=WEBHOOK_DOMAIN,
            # certificate=WEBHOOK_SSL_CERT,
            # certificate_key=WEBHOOK_SSL_PRIV
        ), return_exceptions=True
    )

if __name__ == '__main__':
    asyncio.run(main())