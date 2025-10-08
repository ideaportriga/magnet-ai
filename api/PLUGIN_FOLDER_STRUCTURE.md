# Структура Knowledge Source плагинов

## Обзор

Начиная с этой версии, **все Knowledge Source плагины организованы в отдельные папки**, где каждый плагин инкапсулирует свою логику, включая специфические Data Processors.

## Структура

Каждый плагин находится в своей папке со следующей структурой:

```
plugins/builtin/knowledge_source/
├── __init__.py                    # Импортирует все плагины для авто-регистрации
├── salesforce/
│   ├── __init__.py               # Авто-регистрация плагина
│   ├── plugin.py                 # Определение плагина (SalesforcePlugin)
│   └── processor.py              # Data Processor + вспомогательные классы
├── confluence/
│   ├── __init__.py
│   ├── plugin.py
│   └── processor.py
├── hubspot/
│   ├── __init__.py
│   ├── plugin.py
│   └── processor.py
├── rightnow/
│   ├── __init__.py
│   ├── plugin.py
│   └── processor.py
├── oracle_knowledge/
│   ├── __init__.py
│   ├── plugin.py
│   └── processor.py
├── sharepoint/
│   ├── __init__.py
│   ├── plugin.py
│   ├── abstract_processor.py     # Базовый класс для SharePoint процессоров
│   └── documents_processor.py    # Процессор для документов
└── sharepoint_pages/
    ├── __init__.py
    ├── plugin.py
    └── pages_processor.py         # Процессор для страниц (использует abstract_processor)
```

## ✅ Мигрированные плагины

Все следующие плагины теперь следуют новой структуре:

- ✅ **Salesforce** - CLIENT-SPECIFIC
- ✅ **Confluence** 
- ✅ **HubSpot** - CLIENT-SPECIFIC
- ✅ **RightNow** - CLIENT-SPECIFIC
- ✅ **Oracle Knowledge** - CLIENT-SPECIFIC
- ✅ **SharePoint Documents**
- ✅ **SharePoint Pages**

**Старые файлы удалены:**
- ❌ `salesforce.py`, `confluence.py`, `hubspot.py`, `rightnow.py`, `oracle_knowledge.py` из корня
- ❌ Все соответствующие процессоры из `data_sync/processors/`

## Преимущества новой структуры

### 1. Инкапсуляция
- Каждый плагин содержит всю свою логику в одной папке
- Data Processors являются частью плагина, а не глобальной кодовой базы
- Легче перенести плагин в отдельный пакет для клиентов

### 2. Чистота кода
- Отдельные файлы для плагина и процессора
- Нет необходимости держать весь код в одном большом файле
- Легче читать и поддерживать

### 3. Переносимость
- Вся папка плагина может быть легко скопирована в отдельный репозиторий
- Минимальные зависимости от остальной кодовой базы
- Готова к публикации как отдельный pip-пакет

### 4. Масштабируемость
- Легко добавлять новые файлы в папку плагина (utils, types, constants и т.д.)
- Нет загромождения корневой папки плагинов
- Каждый плагин может иметь свою внутреннюю структуру

## Создание нового плагина

### Шаг 1: Создайте папку плагина

```bash
mkdir plugins/builtin/knowledge_source/my_source
```

### Шаг 2: Создайте структуру файлов

**`__init__.py`** - Авто-регистрация плагина:
```python
"""My Source Knowledge Source Plugin Package"""

from core.plugins.registry import PluginRegistry
from .plugin import MySourcePlugin

PluginRegistry.register(MySourcePlugin())

__all__ = ["MySourcePlugin"]
```

**`plugin.py`** - Определение плагина:
```python
"""My Source Knowledge Source Plugin"""

from typing import Any, Dict
from litestar.exceptions import ClientException

from core.plugins.base import PluginMetadata
from core.plugins.interfaces import KnowledgeSourcePlugin
from core.plugins.plugin_types import PluginType
from data_sync.data_processor import DataProcessor

from .processor import MySourceDataProcessor


class MySourcePlugin(KnowledgeSourcePlugin):
    """Plugin for syncing My Source"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="My Source",
            version="1.0.0",
            author="Your Team",
            description="Synchronizes data from My Source",
            plugin_type=PluginType.KNOWLEDGE_SOURCE,
            dependencies=[],
            config_schema={
                "type": "object",
                "properties": {
                    "api_url": {
                        "type": "string",
                        "description": "My Source API URL",
                    },
                },
                "required": ["api_url"],
            },
        )

    @property
    def source_type(self) -> str:
        return "MySource"

    async def create_processor(
        self,
        source_config: Dict[str, Any],
        collection_config: Dict[str, Any],
        store: Any,
    ) -> DataProcessor:
        """Create My Source processor"""
        # Your implementation here
        return MySourceDataProcessor(...)
```

**`processor.py`** - Data Processor:
```python
"""My Source Data Processor"""

from data_sources.my_source.source import MySourceDataSource
from data_sources.types.basic_metadata import SourceBasicMetadata
from data_sync.data_processor import DataProcessor
from models import DocumentData


class MySourceDataProcessor(DataProcessor):
    """Data processor for My Source"""

    def __init__(self, data_source: MySourceDataSource) -> None:
        self.__data_source = data_source

    @property
    def data_source(self) -> MySourceDataSource:
        return self.__data_source

    async def load_data(self) -> None:
        # Your implementation
        pass

    def get_all_records_basic_metadata(self) -> list[SourceBasicMetadata]:
        # Your implementation
        pass

    async def create_chunks_from_doc(self, id: str) -> list[DocumentData]:
        # Your implementation
        pass
```

### Шаг 3: Добавьте импорт в главный __init__.py

В `plugins/builtin/knowledge_source/__init__.py`:
```python
from . import my_source  # добавьте эту строку

__all__ = [..., "my_source"]  # добавьте в список
```

## Рекомендации

1. **Один файл для плагина, один для процессора** - Не смешивайте логику плагина и процессора в одном файле
2. **Используйте вспомогательные файлы** - Создавайте дополнительные файлы в папке плагина для utils, types, constants
3. **Минимизируйте зависимости** - Старайтесь не зависеть от других плагинов (кроме shared базовых классов)
4. **Документируйте** - Добавляйте docstrings ко всем классам и методам
5. **Тестируйте изолированно** - Каждый плагин должен иметь свои тесты

## Миграция старых плагинов

Если у вас есть старый плагин в одном .py файле:

1. Создайте папку с именем плагина
2. Создайте `__init__.py`, `plugin.py`, `processor.py`
3. Разделите код:
   - Класс плагина → `plugin.py`
   - Data Processor → `processor.py`
   - Вспомогательные классы → `processor.py` или отдельные файлы
4. Обновите импорты
5. Добавьте импорт в главный `__init__.py`
6. Удалите старый .py файл
7. Удалите процессор из `data_sync/processors/` (если он там был)

## Пример: Salesforce плагин

```
salesforce/
├── __init__.py              # Авто-регистрация
├── plugin.py                # SalesforcePlugin
└── processor.py             # SalesforceDataProcessor + SalesforceOutputConfig
```

Все три файла работают вместе, но логика четко разделена.
