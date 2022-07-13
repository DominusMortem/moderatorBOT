from telethon import TelegramClient, sync, events

api_id = 15820816
api_hash = '3a9cf35550d971b31234d1c395a51b15'

client = TelegramClient('session_name', api_id, api_hash)


@client.on(events.NewMessage(chats=('Тестовая комната')))
async def normal_handler(event):
    print(event.message.to_dict()['message'])
