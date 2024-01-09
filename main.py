from src.log_server import start_log_listener
from src.bot import run as run_bot
from src.bot import access_callback
import asyncio

async def main():

    await asyncio.gather(
        start_log_listener(callback=access_callback),
        run_bot()
    )

if __name__ == '__main__':
    asyncio.run(main())