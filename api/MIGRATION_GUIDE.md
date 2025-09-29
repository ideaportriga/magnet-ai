# Утилита миграции данных MongoDB в SQLAlchemy

Эта утилита предназначена для миграции данных из MongoDB в PostgreSQL с использованием SQLAlchemy ORM.

## Возможности

- **Настраиваемый маппинг**: Конфигурируемое соответствие между коллекциями MongoDB и таблицами SQLAlchemy
- **Пакетная обработка**: Обработка больших объемов данных батчами для оптимизации производительности
- **Режим тестирования**: Dry-run режим для проверки миграции без внесения изменений
- **Обработка ошибок**: Надежная обработка ошибок с rollback транзакций
- **Подробное логирование**: Детальные логи процесса миграции
- **Пропуск существующих записей**: Возможность пропускать уже существующие записи

## Предварительные требования

### Установка зависимостей

```bash
# Основные зависимости для миграции
pip install motor pymongo sqlalchemy

# Если используется PostgreSQL
pip install asyncpg

# Для полной работы с проектом
cd api
poetry install
```

### Настройка переменных окружения

Убедитесь, что в файле `.env` настроены следующие переменные:

```bash
# MongoDB (Cosmos DB)
COSMOS_DB_CONNECTION_STRING=mongodb+srv://username:password@cluster.cosmos.azure.com/
COSMOS_DB_DB_NAME=magnet-test

# PostgreSQL (SQLAlchemy)
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
PGVECTOR_CONNECTION_STRING=postgresql+asyncpg://user:password@host:port/database
```

## Использование

### Базовое использование

```bash
# Запуск из директории api
cd api
python mongo_to_sqlalchemy_migration.py

# Или с указанием пути к Python окружению
poetry run python mongo_to_sqlalchemy_migration.py
```

### Параметры командной строки

```bash
# Тестовый запуск без внесения изменений
python mongo_to_sqlalchemy_migration.py --dry-run

# Миграция конкретной коллекции
python mongo_to_sqlalchemy_migration.py --collection agents

# Настройка размера батча
python mongo_to_sqlalchemy_migration.py --batch-size 500

# Отключение пропуска существующих записей
python mongo_to_sqlalchemy_migration.py --no-skip-existing

# Комбинирование параметров
python mongo_to_sqlalchemy_migration.py --dry-run --collection collections --batch-size 100
```

## Маппинг коллекций

Утилита поддерживает следующие коллекции MongoDB и их соответствие таблицам SQLAlchemy:

| MongoDB коллекция | SQLAlchemy модель | Описание |
|------------------|-------------------|----------|
| `agents` | `Agent` | AI агенты |
| `ai_apps` | `AIApp` | AI приложения |
| `collections` | `Collection` | Коллекции документов |
| `jobs` | `Job` | Задачи и джобы |
| `api_keys` | `APIKey` | API ключи |
| `api_servers` | `APIServer` | API серверы |
| `api_tools` | `APITool` | API инструменты |
| `mcp_servers` | `MCPServer` | MCP серверы |
| `rag_tools` | `RAGTool` | RAG инструменты |
| `retrieval_tools` | `RetrievalTool` | Инструменты поиска |
| `evaluations` | `Evaluation` | Оценки |
| `evaluation_sets` | `EvaluationSet` | Наборы оценок |
| `metrics` | `Metric` | Метрики |
| `traces` | `Trace` | Трейсы |
| `prompts` | `Prompt` | Промпты |

## Примеры использования

### 1. Тестовый запуск перед миграцией

```bash
python mongo_to_sqlalchemy_migration.py --dry-run
```

Этот режим покажет:
- Какие коллекции будут обработаны
- Количество документов в каждой коллекции
- Ожидаемые результаты миграции
- Потенциальные проблемы

### 2. Миграция конкретной коллекции

```bash
python mongo_to_sqlalchemy_migration.py --collection agents --dry-run
```

Полезно для:
- Тестирования миграции на небольшом наборе данных
- Отладки проблем с конкретной коллекцией
- Поэтапной миграции

### 3. Полная миграция

```bash
python mongo_to_sqlalchemy_migration.py
```

### 4. Миграция с настройкой производительности

```bash
python mongo_to_sqlalchemy_migration.py --batch-size 2000
```

## Структура процесса миграции

1. **Подключение к базам данных**: Устанавливается соединение с MongoDB и PostgreSQL
2. **Получение списка коллекций**: Сканируются доступные коллекции в MongoDB
3. **Фильтрация коллекций**: Обрабатываются только коллекции с настроенным маппингом
4. **Пакетная обработка**: Документы обрабатываются батчами для оптимизации памяти
5. **Трансформация данных**: Документы MongoDB преобразуются в объекты SQLAlchemy
6. **Сохранение в PostgreSQL**: Данные сохраняются с обработкой ошибок

## Трансформация данных

### Особенности преобразования:

- **ID поля**: `_id` из MongoDB игнорируется, используется автогенерируемый `id` в PostgreSQL
- **Даты**: Строковые представления дат автоматически преобразуются в datetime объекты
- **JSON поля**: Сложные объекты и массивы сохраняются в JSONB полях PostgreSQL
- **Неизвестные поля**: Поля без соответствия в SQLAlchemy модели логируются как предупреждения

### Примеры трансформации:

```python
# MongoDB документ
{
    "_id": "507f1f77bcf86cd799439011",
    "name": "Test Agent",
    "system_name": "test_agent",
    "created_at": "2023-01-15T10:30:00Z",
    "variants": [{"name": "v1", "config": {}}]
}

# SQLAlchemy объект
Agent(
    name="Test Agent",
    system_name="test_agent", 
    created_at=datetime(2023, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
    variants=[{"name": "v1", "config": {}}]
)
```

## Мониторинг и логирование

Утилита предоставляет подробную информацию о процессе:

```
2023-01-15 10:30:00 - INFO - Starting migration of all collections
2023-01-15 10:30:01 - INFO - Found collections in MongoDB: count=15, names=['agents', 'collections', ...]
2023-01-15 10:30:01 - INFO - Collections to migrate: total_collections=12, supported_collections=8
2023-01-15 10:30:02 - INFO - Starting migration for collection: agents
2023-01-15 10:30:02 - INFO - Collection statistics: total_documents=150
2023-01-15 10:30:03 - INFO - Batch processed: processed=100, total=150, progress_percent=66.67
2023-01-15 10:30:04 - INFO - Collection migration completed: status=completed, processed=150, errors=0
```

## Обработка ошибок

### Типы ошибок:

1. **Ошибки соединения**: Проблемы подключения к MongoDB или PostgreSQL
2. **Ошибки трансформации**: Проблемы преобразования данных
3. **Ошибки вставки**: Проблемы сохранения в PostgreSQL
4. **Ошибки валидации**: Несоответствие данных схеме SQLAlchemy

### Стратегия восстановления:

- **Rollback транзакций**: При ошибке в батче происходит откат всей транзакции
- **Продолжение обработки**: Ошибка в одном батче не останавливает обработку других
- **Детальная отчетность**: Все ошибки логируются с контекстной информацией

## Производительность

### Рекомендации по настройке:

- **Размер батча**: 1000-5000 документов (по умолчанию 1000)
- **Подключения**: Используются пулы соединений SQLAlchemy
- **Память**: Батчная обработка минимизирует потребление памяти

### Ожидаемая производительность:

- **Простые документы**: ~1000-2000 документов/сек
- **Сложные документы с JSON**: ~500-1000 документов/сек
- **Большие коллекции**: Линейное масштабирование

## Безопасность

- **Транзакции**: Все изменения в рамках транзакций с возможностью rollback
- **Dry-run режим**: Безопасное тестирование без изменения данных
- **Пропуск существующих**: Избежание дублирования данных
- **Логирование**: Не логируются чувствительные данные

## Расширение

### Добавление новых моделей:

1. Добавьте импорт модели в начало файла
2. Добавьте маппинг в `collection_model_mapping`
3. При необходимости настройте специальную трансформацию в `DocumentTransformer`

### Кастомная трансформация:

```python
def transform_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
    transformed = super().transform_document(document)
    
    # Кастомная логика для конкретной модели
    if self.model_class.__name__ == 'Agent':
        # Специальная обработка для агентов
        pass
    
    return transformed
```

## Устранение неполадок

### Частые проблемы:

1. **ImportError**: Убедитесь что все зависимости установлены
2. **Connection timeout**: Проверьте строки подключения к базам данных
3. **Schema mismatch**: Убедитесь что SQLAlchemy модели синхронизированы с MongoDB структурой
4. **Memory issues**: Уменьшите размер батча

### Отладка:

```bash
# Включение детального логирования
export LOG_LEVEL=DEBUG
python mongo_to_sqlalchemy_migration.py --dry-run

# Тестирование на малой выборке
python mongo_to_sqlalchemy_migration.py --collection agents --batch-size 10 --dry-run
```

## Поддержка

При возникновении проблем:

1. Проверьте логи выполнения
2. Запустите в режиме `--dry-run` для диагностики
3. Убедитесь в правильности настроек подключения
4. Проверьте совместимость версий зависимостей