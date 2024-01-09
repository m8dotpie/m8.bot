from src.log_server import start_log_listener
from src.bot import run as run_bot
import asyncio

async def simple_callback(log_entry):
    req = log_entry['request']
    if req['uri'] == '/':
        print(f"Access from {req['remote_ip']}")

async def main():

    await asyncio.gather(
        start_log_listener(callback=simple_callback),
        run_bot()
    )

if __name__ == '__main__':
    asyncio.run(main())