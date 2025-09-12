"""
Примеры вызова существующего endpoint /scheduler/create-job для запуска evaluation
"""

import asyncio
import json
from datetime import datetime, timedelta

import aiohttp


class SchedulerClient:
    """Клиент для работы с scheduler API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def create_evaluation_job(self, job_data: dict) -> dict:
        """Создать evaluation job через scheduler"""
        url = f"{self.base_url}/scheduler/create-job"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=job_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")

    async def get_pool_status(self) -> dict:
        """Получить статус scheduler pool"""
        url = f"{self.base_url}/scheduler/pool-status"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

    async def cancel_job(self, job_id: str) -> dict:
        """Отменить задачу"""
        url = f"{self.base_url}/scheduler/cancel-job"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"job_id": job_id}) as response:
                return await response.json()


async def example_1_immediate_rag_evaluation():
    """Пример 1: Немедленная RAG evaluation"""
    client = SchedulerClient()

    job_data = {
        "name": "RAG Tool Performance Test",
        "job_type": "one_time_immediate",
        "run_configuration": {
            "type": "evaluation",
            "params": {
                "type": "rag_eval",
                "iteration_count": 3,
                "config": [
                    {
                        "system_name": "customer_support_rag",
                        "test_set_system_names": [
                            "support_questions_v1",
                            "support_questions_v2",
                        ],
                        "variants": ["default", "optimized"],
                    }
                ],
                "result_entity": "evaluations",
            },
        },
        # Все остальные поля None (будут установлены по умолчанию)
        "job_id": None,
        "interval": None,
        "notification_email": None,
        "cron": None,
        "scheduled_start_time": None,
        "status": None,
        "timezone": None,
    }

    print("🚀 Создание немедленной RAG evaluation...")
    result = await client.create_evaluation_job(job_data)
    print(f"✅ Результат: {json.dumps(result, indent=2)}")

    return result.get("job_id")


async def example_2_prompt_evaluation():
    """Пример 2: Evaluation для Prompt Template"""
    client = SchedulerClient()

    job_data = {
        "name": "Prompt Template A/B Test",
        "job_type": "one_time_immediate",
        "run_configuration": {
            "type": "evaluation",
            "params": {
                "type": "prompt_eval",
                "iteration_count": 2,
                "config": [
                    {
                        "system_name": "customer_response_template",
                        "test_set_system_names": ["customer_interactions"],
                        "variants": ["formal", "friendly", "concise"],
                    },
                    {
                        "system_name": "product_description_template",
                        "test_set_system_names": ["product_descriptions"],
                        "variants": ["technical", "marketing"],
                    },
                ],
                "result_entity": "evaluations",
            },
        },
        "job_id": None,
        "interval": None,
        "notification_email": None,
        "cron": None,
        "scheduled_start_time": None,
        "status": None,
        "timezone": None,
    }

    print("🧪 Создание Prompt Template evaluation...")
    result = await client.create_evaluation_job(job_data)
    print(f"✅ Результат: {json.dumps(result, indent=2)}")

    return result.get("job_id")


async def example_3_scheduled_evaluation():
    """Пример 3: Запланированная evaluation на завтра в 14:00"""
    client = SchedulerClient()

    # Запланировать на завтра в 14:00
    tomorrow_2pm = (datetime.now() + timedelta(days=1)).replace(
        hour=14, minute=0, second=0, microsecond=0
    )

    job_data = {
        "name": "Scheduled RAG Evaluation",
        "job_type": "one_time_scheduled",
        "scheduled_start_time": tomorrow_2pm.isoformat(),
        "run_configuration": {
            "type": "evaluation",
            "params": {
                "type": "rag_eval",
                "iteration_count": 1,
                "config": [
                    {
                        "system_name": "production_rag_tool",
                        "test_set_system_names": ["production_test_set"],
                        "variants": ["current"],
                    }
                ],
                "result_entity": "evaluations",
            },
        },
        "job_id": None,
        "interval": None,
        "notification_email": None,
        "cron": None,
        "status": None,
        "timezone": None,
    }

    print(f"📅 Создание запланированной evaluation на {tomorrow_2pm}...")
    result = await client.create_evaluation_job(job_data)
    print(f"✅ Результат: {json.dumps(result, indent=2)}")

    return result.get("job_id")


async def example_4_recurring_evaluation():
    """Пример 4: Повторяющаяся evaluation каждый день в 2:00 ночи"""
    client = SchedulerClient()

    job_data = {
        "name": "Daily Production RAG Evaluation",
        "job_type": "recurring",
        "cron": {
            "hour": 2,  # 2:00 AM
            "minute": 0,
            "second": 0,
            # Остальные поля None (каждый день)
            "year": None,
            "month": None,
            "day": None,
            "week": None,
            "day_of_week": None,
            "start_date": None,
            "end_date": None,
            "jitter": None,
        },
        "scheduled_start_time": datetime.now().isoformat(),
        "run_configuration": {
            "type": "evaluation",
            "params": {
                "type": "rag_eval",
                "iteration_count": 1,
                "config": [
                    {
                        "system_name": "production_rag_tool",
                        "test_set_system_names": ["daily_test_set"],
                        "variants": ["production"],
                    }
                ],
                "result_entity": "evaluations",
            },
        },
        "job_id": None,
        "interval": None,
        "notification_email": None,
        "status": None,
        "timezone": "UTC",
    }

    print("🔄 Создание повторяющейся evaluation (каждый день в 2:00)...")
    result = await client.create_evaluation_job(job_data)
    print(f"✅ Результат: {json.dumps(result, indent=2)}")

    return result.get("job_id")


async def example_5_weekly_evaluation():
    """Пример 5: Еженедельная evaluation по понедельникам в 9:00"""
    client = SchedulerClient()

    job_data = {
        "name": "Weekly RAG Performance Report",
        "job_type": "recurring",
        "cron": {
            "day_of_week": "monday",  # Понедельник
            "hour": 9,  # 9:00 AM
            "minute": 0,
            "second": 0,
            "year": None,
            "month": None,
            "day": None,
            "week": None,
            "start_date": None,
            "end_date": None,
            "jitter": None,
        },
        "scheduled_start_time": datetime.now().isoformat(),
        "run_configuration": {
            "type": "evaluation",
            "params": {
                "type": "rag_eval",
                "iteration_count": 5,
                "config": [
                    {
                        "system_name": "main_rag_tool",
                        "test_set_system_names": ["comprehensive_test_set"],
                        "variants": ["production", "staging"],
                    }
                ],
                "result_entity": "evaluations",
            },
        },
        "job_id": None,
        "interval": None,
        "notification_email": "admin@company.com",
        "status": None,
        "timezone": "UTC",
    }

    print("📊 Создание еженедельной evaluation (понедельники в 9:00)...")
    result = await client.create_evaluation_job(job_data)
    print(f"✅ Результат: {json.dumps(result, indent=2)}")

    return result.get("job_id")


async def main():
    """Главная функция для демонстрации всех примеров"""
    print("=== Примеры использования Scheduler для Evaluation ===\n")

    job_ids = []

    try:
        # Пример 1: Немедленная RAG evaluation
        job_id_1 = await example_1_immediate_rag_evaluation()
        if job_id_1:
            job_ids.append(job_id_1)

        print("\n" + "-" * 60 + "\n")

        # Пример 2: Prompt evaluation
        job_id_2 = await example_2_prompt_evaluation()
        if job_id_2:
            job_ids.append(job_id_2)

        print("\n" + "-" * 60 + "\n")

        # Пример 3: Запланированная evaluation
        job_id_3 = await example_3_scheduled_evaluation()
        if job_id_3:
            job_ids.append(job_id_3)

        print("\n" + "-" * 60 + "\n")

        # Пример 4: Повторяющаяся evaluation
        job_id_4 = await example_4_recurring_evaluation()
        if job_id_4:
            job_ids.append(job_id_4)

        print("\n" + "-" * 60 + "\n")

        # Пример 5: Еженедельная evaluation
        job_id_5 = await example_5_weekly_evaluation()
        if job_id_5:
            job_ids.append(job_id_5)

        print("\n" + "=" * 60 + "\n")

        # Проверка статуса scheduler
        client = SchedulerClient()
        print("📊 Проверка статуса scheduler...")
        status = await client.get_pool_status()
        print(f"✅ Статус: {json.dumps(status, indent=2)}")

        print(f"\n🎉 Создано задач: {len(job_ids)}")
        print("Job IDs:", job_ids)

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    # Запуск примеров
    asyncio.run(main())
