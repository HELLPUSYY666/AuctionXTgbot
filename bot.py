import asyncio

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config_reader import get_config, BotConfig, LogConfig
from logs import get_structlog_config
from structlog.typing import FilteringBoundLogger

from dispatcher import dp


async def main():
    log_config: LogConfig = get_config(model=LogConfig, root_key="logs")
    structlog.configure(**get_structlog_config(log_config))

    bot_config: BotConfig = get_config(model=BotConfig, root_key="bot")

    bot = Bot(
        token=bot_config.token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    logger: FilteringBoundLogger = structlog.get_logger()
    await logger.ainfo("Starting the bot...")

    try:
        await dp.start_polling(bot,
                               skip_updates=False)  # Don't skip updates, if your bot will process payments or other important stuff
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
