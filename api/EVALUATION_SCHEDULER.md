# Evaluation через Scheduler

Этот документ описывает, как запускать evaluation через новую систему scheduler вместо устаревшего метода через `run_job`.

## Обзор изменений

1. **Добавлен новый тип задач**: `RunConfigurationType.EVALUATION`
2. **Создан executor**: `execute_evaluation` в `scheduler/executors.py`
3. **Обновлена функция evaluate**: Убраны Thread'ы, теперь полностью асинхронная
4. **Создан новый endpoint**: `/evaluation-scheduler/create-evaluation-job`

## Как использовать

### 1. Создание немедленной evaluation задачи

```bash
POST /evaluation-scheduler/create-evaluation-job
Content-Type: application/json

{
    "name": "RAG Tool Evaluation",
    "evaluation_type": "rag_eval",
    "iteration_count": 3,
    "config": [
        {
            "system_name": "my_rag_tool",
            "test_set_system_names": ["test_set_1", "test_set_2"],
            "variants": ["default", "optimized"]
        }
    ],
    "result_entity": "evaluations",
    "job_type": "one_time_immediate"
}
```

### 2. Создание регулярной evaluation задачи

```bash
POST /evaluation-scheduler/create-scheduled-evaluation
Content-Type: application/json

{
    "name": "Daily RAG Evaluation",
    "evaluation_type": "rag_eval", 
    "iteration_count": 1,
    "config": [
        {
            "system_name": "production_rag_tool",
            "test_set_system_names": ["production_test_set"],
            "variants": ["current"]
        }
    ],
    "result_entity": "evaluations"
}
```

### 3. Использование через общий scheduler endpoint

Альтернативно, можно использовать общий endpoint `/scheduler/create-job`:

```bash
POST /scheduler/create-job
Content-Type: application/json

{
    "name": "Custom Evaluation Job",
    "job_type": "one_time_immediate",
    "run_configuration": {
        "type": "evaluation",
        "params": {
            "type": "rag_eval",
            "iteration_count": 1,
            "config": [
                {
                    "system_name": "MAGNET_AI_MANUAL",
                    "test_set_system_names": ["MANUAL_TEST_SET"],
                    "variants": ["variant_1"]
                }
            ],
            "result_entity": "evaluations"
        }
    }
}
```

## Параметры

### EvaluationJobRequest

- `name` (string): Название задачи
- `evaluation_type` (string): Тип evaluation - `"rag_eval"` или `"prompt_eval"`
- `iteration_count` (int): Количество итераций (по умолчанию 1)
- `config` (array): Массив конфигураций для evaluation
- `result_entity` (string): Сущность для сохранения результатов (по умолчанию "evaluations")
- `job_type` (JobType): Тип задачи - `"one_time_immediate"`, `"one_time_scheduled"`, или `"recurring"`

### EvaluationConfig

- `system_name` (string): Системное имя инструмента для evaluation
- `test_set_system_names` (array): Массив системных имен тестовых наборов
- `variants` (array): Массив вариантов для тестирования

## Типы задач

1. **`one_time_immediate`**: Запуск сразу после создания
2. **`one_time_scheduled`**: Запуск в указанное время
3. **`recurring`**: Повторяющийся запуск по расписанию (cron)

## Мониторинг

Для проверки статуса задач используйте:

```bash
GET /scheduler/pool-status
```

Для отмены задачи:

```bash
POST /scheduler/cancel-job
Content-Type: application/json

{
    "job_id": "your-job-id"
}
```

## Преимущества новой системы

1. **Централизованное управление**: Все задачи в одном месте
2. **Расписания**: Возможность создавать recurring задачи
3. **Мониторинг**: Единый интерфейс для отслеживания статуса
4. **Масштабируемость**: Лучшая производительность и управление ресурсами
5. **Логирование**: Стандартизированное логирование через observability

## Миграция с run_job

Для миграции с старого метода `run_job`:

1. Замените вызов `run_job(data)` на создание задачи через scheduler
2. Адаптируйте структуру параметров под новый формат
3. Используйте новые endpoints для мониторинга вместо прямого обращения к коллекции jobs

### Пример миграции

**Было (run_job):**
```python
data = {
    "type": "rag_eval",
    "iteration_count": 3,
    "config": [...],
    "result_entity": "evaluations"
}
result = await run_job(data)
```

**Стало (scheduler):**
```python
job_definition = JobDefinition(
    name="My Evaluation",
    job_type=JobType.ONE_TIME_IMMEDIATE,
    run_configuration=RunConfiguration(
        type=RunConfigurationType.EVALUATION,
        params={
            "type": "rag_eval",
            "iteration_count": 3,
            "config": [...],
            "result_entity": "evaluations"
        }
    )
)
result = await create_job(scheduler, job_definition, db_session)
```
