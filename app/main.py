import asyncio
import logging
import os

from dotenv import load_dotenv
from bot_controller import BotController
from web_server import start_web_server, set_bot_instance

# Load environment variables from .env file
load_dotenv()


async def main() -> None:
    # Start web server for OAuth callbacks
    web_runner = await start_web_server(host='0.0.0.0', port=8000)
    
    # Start bot controller
    bot_controller = BotController(os.getenv("TELEGRAM_API_KEY"))
    
    # Set bot instance for web server notifications
    set_bot_instance(bot_controller._bot)
    
    try:
        await bot_controller.start()
    finally:
        # Cleanup web server
        await web_runner.cleanup()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)9s | %(asctime)s | %(name)30s | %(filename)20s | %(lineno)6s | %(message)s",
        force=True,
    )
    asyncio.run(main())
