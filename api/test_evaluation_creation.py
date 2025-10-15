#!/usr/bin/env python3
"""
Тестовый скрипт для создания записи evaluation
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from core.db.database import get_async_db
from services.evaluations.evaluations_service import EvaluationsService


async def test_evaluation_creation():
    """Тест создания записи evaluation"""
    print("🧪 Тестируем создание записи evaluation...")

    # Данные для создания evaluation
    evaluation_data = {
        "job_id": "test-job-123",
        "type": "agent_evaluation",
        "test_sets": [
            {
                "system_name": "MANUAL_TEST_SET",
                "id": "821e03d7-11b8-4ef4-9e7f-ec22e6d8a17d",
            }
        ],
        "started_at": datetime.now(timezone.utc),
        "status": "running",
        "errors": [],  # Правильный тип - список строк
        "tool": {"type": "test_tool", "config": {}, "system_name": "TEST_TOOL"},
        "results": None,
    }

    try:
        # Получаем соединение с базой данных
        async for db in get_async_db():
            # Создаем сервис
            evaluations_service = EvaluationsService(session=db)

            # Создаем запись
            print(f"📝 Создаем evaluation с данными: {evaluation_data}")
            evaluation = await evaluations_service.create(evaluation_data)

            print(f"✅ Успешно создана evaluation с ID: {evaluation.id}")
            print("📊 Данные evaluation:")
            print(f"   - ID: {evaluation.id}")
            print(f"   - Job ID: {evaluation.job_id}")
            print(f"   - Type: {evaluation.type}")
            print(f"   - Status: {evaluation.status}")
            print(f"   - Test Sets: {evaluation.test_sets}")
            print(f"   - Started At: {evaluation.started_at}")
            print(f"   - Errors: {evaluation.errors}")
            print(f"   - Tool: {evaluation.tool}")

            return evaluation

    except Exception as e:
        print(f"❌ Ошибка при создании evaluation: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_evaluation_creation())
