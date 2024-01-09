from src.log_server import start_log_listener
from src.bot import run as run_bot

import multiprocessing

async def simple_callback(log_entry):
    req = log_entry['request']
    if req['uri'] == '/':
        print(f"Access from {req['remote_ip']}")

async def main():

    await asyncio.gather(
        start_log_listener(LOG_HOST, LOG_PORT, callback=simple_callback),
        run_bot(), return_exceptions=False
    )

if __name__ == '__main__':
    asyncio.run(main())