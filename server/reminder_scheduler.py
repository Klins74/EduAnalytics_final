#!/usr/bin/env python3
"""
Планировщик автоматических напоминаний
Запускается как отдельный процесс для обработки напоминаний в фоне
"""
import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_session
from app.services.reminder_service import reminder_service

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def process_reminders_job():
    """Задача обработки напоминаний"""
    logger.info("🔔 Запуск обработки напоминаний")
    
    try:
        async for db in get_async_session():
            sent_count = await reminder_service.process_pending_reminders(db)
            
            if sent_count > 0:
                logger.info(f"✅ Отправлено {sent_count} напоминаний")
            else:
                logger.info("ℹ️ Нет напоминаний для отправки")
            
            break  # Выходим из генератора
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке напоминаний: {e}")

async def reminder_scheduler():
    """Основной планировщик напоминаний"""
    logger.info("🚀 Запуск планировщика автоматических напоминаний")
    logger.info("⏰ Проверка напоминаний каждые 5 минут")
    
    while True:
        try:
            # Обрабатываем напоминания
            await process_reminders_job()
            
            # Ждем 5 минут до следующей проверки
            await asyncio.sleep(300)  # 5 минут = 300 секунд
            
        except KeyboardInterrupt:
            logger.info("🛑 Получен сигнал остановки")
            break
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в планировщике: {e}")
            # Ждем минуту перед перезапуском
            await asyncio.sleep(60)

def main():
    """Главная функция запуска планировщика"""
    try:
        asyncio.run(reminder_scheduler())
    except KeyboardInterrupt:
        logger.info("👋 Планировщик остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Фатальная ошибка: {e}")

if __name__ == "__main__":
    main()
