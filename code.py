import logging
import asyncio
from pathlib import Path
from telethon import TelegramClient, events
from telethon.tl.types import MessageService, Message
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class Config:
    API_ID: int = idreal
    API_HASH: str = 'hash'
    SESSION_NAME: str = 'session'
    LOG_FILE: str = 'self.log'
    NewMassage: bool = False
    DelAllInStart: bool = False

class MessageStore:
    def __init__(self):
        self.messages: Dict[int, str] = {}
    
    def add(self, msg_id: int, text: str):
        self.messages[msg_id] = text
    
    def get(self, msg_id: int) -> str:
        return self.messages.get(msg_id, "")

message_store = MessageStore()

def setup_logging():
    if Config.DelAllInStart:
        Path(Config.LOG_FILE).write_text('', encoding='utf-8')
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(file_formatter)

    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def get_sender_name(sender) -> str:
    """Безопасное получение имени отправителя"""
    if not sender:
        return "Unknown"
    
    if hasattr(sender, 'username') and sender.username:
        return f"@{sender.username}"
    
    if hasattr(sender, 'first_name') and sender.first_name:
        return sender.first_name
    
    if hasattr(sender, 'title') and sender.title:  # Для каналов и чатов
        return sender.title
    
    return "Unknown"

async def main():
    setup_logging()
    client = TelegramClient(Config.SESSION_NAME, Config.API_ID, Config.API_HASH)
    
    try:
        await client.start()
        logging.info("Мониторинг сообщений запущен!")

        @client.on(events.NewMessage)
        async def message_handler(event):
            if isinstance(event.message, MessageService) or not event.message.text:
                return
            
            message_store.add(event.message.id, event.message.text)
            sender = await event.get_sender()
            name = get_sender_name(sender)
            if Config.NewMassage:
                logging.info(f"НОВОЕ: {name}: {event.message.text}")

        @client.on(events.MessageDeleted)
        async def deleted_handler(event):
            for msg_id in event.deleted_ids:
                original_text = message_store.get(msg_id)
                if original_text:
                    logging.warning(f"УДАЛЕНО: Сообщение ID{msg_id}: {original_text}")
                else:
                    logging.warning(f"УДАЛЕНО: Сообщение ID{msg_id} (текст недоступен)")

        @client.on(events.MessageEdited)
        async def edited_handler(event):
            msg = event.message
            if isinstance(msg, MessageService) or not msg.text:
                return
            
            original_text = message_store.get(msg.id)
            new_text = msg.text
            
            if original_text == new_text:
                return

            sender = await msg.get_sender()
            name = get_sender_name(sender)
            logging.info(f"ИЗМЕНЕНО: {name}: {original_text} → {new_text}")
            message_store.add(msg.id, new_text)

        await client.run_until_disconnected()
        
    except Exception as e:
        logging.critical(f"Ошибка: {str(e)}")
    finally:
        logging.info("Мониторинг остановлен")

if __name__ == '__main__':
    asyncio.run(main())
