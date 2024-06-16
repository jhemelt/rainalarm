import asyncio
import telegram


async def main():
    bot = telegram.Bot(TOKEN)
    async with bot:
        await bot.send_message(text='Hi John!', chat_id=7028736026, )


TOKEN="7057387405:AAHUcn25UJ0wRPRRgczTE-UThGjG5gmfgFw"
if __name__ == '__main__':
    asyncio.run(main())