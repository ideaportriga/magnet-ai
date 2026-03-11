# ROADMAP: Миграция на Kreuzberg для извлечения контента из файлов

> Дата создания: 11 марта 2026
> Основано на аудите кодовой базы: `api/src/`

---

## Мотивация

Текущая система извлечения контента из файлов ограничена двумя типами: PDF (через `pypdf`) и plain text. HTML-контент конвертируется в текст через `html2text` с потерей структуры. Нет поддержки DOCX, PPTX, XLSX, изображений (OCR) и других форматов.

**Kreuzberg** — высокопроизводительная библиотека (Rust core) с поддержкой 75+ форматов, async API, markdown output, OCR и batch processing. MIT лицензия.

### Ключевые преимущества перехода

| Аспект | Сейчас | С Kreuzberg |
|--------|--------|-------------|
| Форматы файлов | PDF, plain text | 75+: PDF, DOCX, PPTX, XLSX, изображения, HTML, email, архивы и др. |
| Выходной формат | Plain text | Markdown (с сохранением структуры: заголовки, таблицы, списки) |
| OCR | Нет | Tesseract / EasyOCR / PaddleOCR |
| Производительность | Python (pypdf) | Rust core, 10-100 MB/s для PDF |
| Async | Нет (синхронный pypdf) | Полноценный async/await |
| Таблицы | Теряются при извлечении | Извлекаются отдельно, рендерятся в markdown |
| Метаданные | Базовые (только PDF) | Богатые метаданные для всех форматов |
| Батч-обработка | Нет | Встроенная параллельная обработка |

---

## Текущая архитектура извлечения контента

```
File Bytes
    │
    ▼
load_content_from_bytes(file_bytes, config)
    │
    ├─ ContentReaderName.PDF → DefaultPdfReader().extract_text_from_bytes()
    │                              │
    │                              └─ pypdf.PdfReader → plain text + page count
    │
    ├─ ContentReaderName.PLAIN_TEXT → bytes.decode("utf-8")
    │
    └─ _ → ValueError("Unsupported reader")
```

### Все точки извлечения контента в кодовой базе

#### 1. Knowledge Graph — основной пайплайн (приоритет: ВЫСОКИЙ)

| Файл | Что делает | Текущая реализация |
|------|------------|--------------------|
| `api/src/services/knowledge_graph/content_load_services.py` | Центральная функция `load_content_from_bytes()` — маршрутизатор по типу контента | `match reader_name` → PDF или plain text |
| `api/src/services/knowledge_graph/readers/pdf_reader.py` | `DefaultPdfReader` — извлечение текста из PDF | `pypdf.PdfReader`, extraction_mode="plain", `[Page: N]` маркеры |
| `api/src/services/knowledge_graph/models.py` | `ContentReaderName` enum, `ContentConfig` модель | Только `PDF` и `PLAIN_TEXT` |
| `api/src/services/knowledge_graph/content_config_services.py` | Дефолтные конфигурации, glob-маршрутизация | `*.pdf` → PDF reader, `*` → plain text |

**Потребители `load_content_from_bytes()`:**
- `api/src/services/knowledge_graph/sources/sync_pipeline.py` → `store_document()` (все data sources)
- `api/src/services/knowledge_graph/sources/file_upload/file_upload_sync.py` → upload pipeline
- `api/src/services/knowledge_graph/sources/sharepoint/sharepoint_sync.py` → SharePoint pipeline
- `api/src/services/knowledge_graph/sources/api_ingest/api_ingest_source.py` → `ingest_file()`

#### 2. User Utils — парсинг PDF (приоритет: СРЕДНИЙ)

| Файл | Что делает | Текущая реализация |
|------|------------|--------------------|
| `api/src/routes/user/utils.py` | Эндпоинт `POST /utils/parse-pdf` | `pypdf.PdfReader` → список текстов страниц |

#### 3. Data Sync — legacy пайплайн (приоритет: СРЕДНИЙ)

| Файл | Что делает | Текущая реализация |
|------|------------|--------------------|
| `api/src/data_sync/data_processor.py` | `DataProcessor._html_to_text()`, `create_documents_from_html()` | `BeautifulSoup` → `html2text.HTML2Text()` |
| `api/src/data_sync/utils.py` | `parse_page()` — парсинг HTML страниц | `BeautifulSoup` → `HTML2Text` → markdown-like текст |
| `api/src/data_sync/processors/file_data_processor.py` | `UrlDataProcessor` — обработка PDF по URL | `langchain PyPDFLoader` → `RecursiveCharacterTextSplitter` |
| `api/src/data_sync/splitters/pdf_splitter.py` | `PdfSplitter` — извлечение и сплит PDF | `langchain PyPDFLoader` → сегментация чанков |

#### 4. HTML → Text конвертация (приоритет: СРЕДНИЙ)

| Файл | Что делает | Текущая реализация |
|------|------------|--------------------|
| `api/src/services/knowledge_graph/sources/fluid_topics/fluid_topics_utils.py` | `_extract_text_from_html()` — Fluid Topics HTML → text | `HTML2Text` с отключением ссылок/картинок/emphasis |
| `api/src/data_sync/data_processor.py` | `_html_to_text()` | `BeautifulSoup.get_text()` → `HTML2Text` |
| `api/src/data_sync/utils.py` | `parse_page()` | `BeautifulSoup` + `HTML2Text` → markdown |

---

## Целевая архитектура

```
File Bytes + MIME Type
    │
    ▼
load_content_from_bytes(file_bytes, config)        ← unified entry point
    │
    ▼
kreuzberg.extract_bytes(data, mime_type, config)   ← async, Rust core
    │
    ├─ output_format="markdown"                     ← структурированный markdown
    ├─ pages=PageConfig(extract_pages=True)         ← per-page extraction
    ├─ ocr=OcrConfig(backend="tesseract")           ← OCR для изображений/скан. PDF
    │
    ▼
ExtractionResult
    ├─ .content          → markdown текст
    ├─ .metadata         → богатые метаданные (page_count, title, authors, ...)
    ├─ .tables           → извлечённые таблицы
    ├─ .pages            → контент по страницам
    └─ .detected_languages → обнаруженные языки
```

---

## План миграции

### Фаза 0: Подготовка (без изменения поведения)

- [x] **0.1** Добавить `kreuzberg` в `api/pyproject.toml`
- [x] **0.2** Создать `api/src/services/knowledge_graph/readers/kreuzberg_reader.py` — обёртка над kreuzberg
- [x] **0.3** Добавить MIME type detection утилиту (через `kreuzberg.detect_mime_type`)
- [x] **0.4** Написать unit-тесты для нового reader'а на тех же PDF, что и текущие тесты

### Фаза 1: Knowledge Graph — замена PDF reader (основной приоритет)

- [x] **1.1** Расширить `ContentReaderName` enum: добавить `KREUZBERG = "kreuzberg"`
- [x] **1.2** Реализовать `KreuzbergReader` класс:
  ```python
  class KreuzbergReader:
      async def extract_from_bytes(
          self, data: bytes, mime_type: str
      ) -> tuple[str, dict[str, Any]]:
          config = ExtractionConfig(
              output_format="markdown",
              pages=PageConfig(
                  extract_pages=True,
                  insert_page_markers=True,
              ),
          )
          result = await extract_bytes(data, mime_type, config=config)
          metadata = {
              "total_pages": result.get_page_count(),
              "title": result.metadata.get("title"),
              "authors": result.metadata.get("authors"),
              "tables_count": len(result.tables),
              "detected_languages": result.detected_languages,
          }
          return result.content, metadata
  ```
- [x] **1.3** Обновить `load_content_from_bytes()` — добавить `case ContentReaderName.KREUZBERG` (async)
- [x] **1.4** Обновить `content_config_services.py` — для PDF использовать kreuzberg reader по дефолту
- [x] **1.5** Обновить `store_document()` в `sync_pipeline.py` — поддержать async вызов `load_content_from_bytes`
- [x] **1.6** Сохранить `DefaultPdfReader` как fallback (feature flag `USE_KREUZBERG=true/false`)
- [ ] **1.7** Тестирование: сравнить качество извлечения на существующих PDF-документах

### Фаза 2: Расширение поддерживаемых форматов

- [x] **2.1** Добавить конфигурации в `get_default_content_configs()`:
  ```python
  ContentConfig(name="Word", glob_pattern="*.docx", reader={"name": "kreuzberg"}),
  ContentConfig(name="PowerPoint", glob_pattern="*.pptx", reader={"name": "kreuzberg"}),
  ContentConfig(name="Excel", glob_pattern="*.xlsx", reader={"name": "kreuzberg"}),
  ContentConfig(name="Images", glob_pattern="*.png,*.jpg,*.jpeg,*.gif,*.webp,*.bmp,*.tiff",
                reader={"name": "kreuzberg", "options": {"ocr": true}}),
  ContentConfig(name="HTML", glob_pattern="*.html,*.htm",
                reader={"name": "kreuzberg"}),
  ContentConfig(name="Email", glob_pattern="*.eml,*.msg",
                reader={"name": "kreuzberg"}),
  ```
- [x] **2.2** Добавить MIME type mapping для новых форматов
- [x] **2.3** Обновить `FileUploadDataSource` — поддержать новые форматы в upload endpoint
- [ ] **2.4** Обновить SharePoint source — убрать ограничение "ingests PDFs"
- [ ] **2.5** Обновить API ingest — поддержать новые форматы файлов
- [ ] **2.6** Обновить frontend — расширить list допустимых расширений для загрузки
- [x] **2.7** Тесты для каждого нового формата

### Фаза 3: Markdown output вместо plain text

- [x] **3.1** Установить `output_format="markdown"` в `ExtractionConfig` по умолчанию
- [ ] **3.2** Адаптировать chunking стратегии для markdown:
  - Markdown-aware splitting (по заголовкам `#`, `##`, etc.)
  - Сохранение markdown-таблиц внутри чанков
  - Уважать markdown code blocks при сплите
- [ ] **3.3** Обновить LLM prompt templates — указать что контекст в markdown
- [x] **3.4** Обновить `_extract_text_from_html()` в Fluid Topics:
  - Заменить `html2text` → `kreuzberg.extract_bytes(html_bytes, "text/html", config=ExtractionConfig(output_format="markdown"))`
  - Убрать ручную нормализацию whitespace (kreuzberg делает это сам)
- [x] **3.5** Обновить `data_sync/utils.py` `parse_page()`:
  - Заменить `BeautifulSoup + HTML2Text` → `kreuzberg`
- [x] **3.6** Обновить `data_sync/data_processor.py` `_html_to_text()`:
  - Заменить `BeautifulSoup + html2text` → `kreuzberg`
- [ ] **3.7** Обновить существующие тесты, проверить markdown output

### Фаза 4: User Utils endpoint

- [x] **4.1** Обновить `POST /utils/parse-pdf` endpoint:
  ```python
  @post("/parse-pdf", status_code=HTTP_200_OK)
  async def parse_pdf(self, data: UploadFile) -> ParsePdfResponse:
      content = await data.read()
      config = ExtractionConfig(
          output_format="markdown",
          pages=PageConfig(extract_pages=True),
      )
      result = await extract_bytes(content, "application/pdf", config=config)
      pages = [p.content for p in result.pages] if result.pages else [result.content]
      return ParsePdfResponse(pages=pages)
  ```
- [x] **4.2** Расширить endpoint — поддержать все форматы (переименовать в `/utils/parse-document`)
- [x] **4.3** Вернуть дополнительные метаданные: title, page_count, tables, detected_languages

### Фаза 5: Data Sync legacy пайплайн

- [x] **5.1** Обновить `PdfSplitter` — заменить `PyPDFLoader` на kreuzberg
- [x] **5.2** Обновить `UrlDataProcessor.__create_pdf_documents()` — использовать kreuzberg
  - Убрать скачивание во временный файл, использовать `extract_bytes()` напрямую
- [ ] **5.3** Обновить `UrlDataProcessor.create_chunks_from_doc()` — поддержать не только PDF
- [ ] **5.4** Тесты для обновлённого data sync пайплайна

### Фаза 6: OCR для изображений и сканированных PDF

- [x] **6.1** Добавить Tesseract в Docker-образ (`Dockerfile`)
- [x] **6.2** Создать конфигурацию OCR для Knowledge Graph:
  ```python
  ExtractionConfig(
      ocr=OcrConfig(
          backend="tesseract",
          language="eng",  # configurable per graph
      ),
      force_ocr=False,  # auto-detect
  )
  ```
- [x] **6.3** Добавить content config для изображений с OCR
- [ ] **6.4** Добавить возможность настройки OCR языка в Knowledge Graph settings
- [ ] **6.5** Тесты с OCR (сканированные PDF, изображения)

### Фаза 7: Очистка и удаление legacy зависимостей

- [ ] **7.1** Удалить `DefaultPdfReader` (`readers/pdf_reader.py`) после стабилизации
- [ ] **7.2** Удалить `pypdf` из зависимостей (или оставить для специфичных edge case)
- [x] **7.3** Оценить удаление `html2text` (если все use cases покрыты kreuzberg)
- [ ] **7.4** Оценить удаление `langchain PyPDFLoader` из data_sync
- [ ] **7.5** Обновить документацию: поддерживаемые форматы, настройки OCR

---

## Текущие зависимости, затрагиваемые миграцией

| Пакет | Где используется | Заменяется kreuzberg |
|-------|-----------------|---------------------|
| `pypdf` 6.1.1 | `readers/pdf_reader.py`, `routes/user/utils.py` | Да (PDF extraction) |
| `html2text` 2020.1.16 | `fluid_topics_utils.py`, `data_sync/utils.py`, `data_processor.py` | Да (HTML → markdown) |
| `openpyxl` 3.1.5 | Косвенно (может использоваться) | Да (XLSX extraction) |
| `langchain PyPDFLoader` | `data_sync/splitters/pdf_splitter.py` | Да (PDF loading) |
| `beautifulsoup4` | `data_sync/utils.py`, `data_processor.py` | Частично (HTML parsing) |

---

## Необходимые изменения в инфраструктуре

### Docker (`Dockerfile`)
```dockerfile
# Для OCR поддержки
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-rus \
    # доп. языки по необходимости
    && rm -rf /var/lib/apt/lists/*
```

### `pyproject.toml`
```toml
[tool.poetry.dependencies]
kreuzberg = "^4.4"
# Опционально для EasyOCR:
# kreuzberg = {version = "^4.4", extras = ["easyocr"]}
```

### Environment Variables
```env
# Feature flag для постепенного rollout
USE_KREUZBERG=true

# OCR настройки
KREUZBERG_OCR_BACKEND=tesseract
KREUZBERG_OCR_LANGUAGE=eng
```

---

## Риски и митигация

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| Различия в качестве PDF extraction между pypdf и kreuzberg | Средняя | Feature flag, A/B тестирование, сравнительные тесты |
| Увеличение размера Docker-образа (Tesseract OCR) | Высокая | OCR — опциональная функция, отдельный Docker layer |
| Breaking changes в kreuzberg API (v4 → v5) | Низкая | Обёртка `KreuzbergReader` изолирует API |
| Markdown output ломает существующие chunking стратегии | Средняя | Фазированный rollout, markdown-aware splitters |
| Совместимость kreuzberg native binaries в Docker | Низкая | Precompiled binaries есть для linux/amd64 и arm64 |
| Больше метаданных → изменения в DB schema | Низкая | Метаданные хранятся в JSON-полях, schema не меняется |

---

## Метрики успеха

- [ ] Поддержка ≥10 форматов файлов (сейчас: 2)
- [ ] Markdown output для всех источников контента
- [ ] OCR поддержка для изображений и сканированных документов
- [ ] Без регрессий в качестве извлечения PDF
- [ ] Уменьшение количества зависимостей для text extraction (pypdf, html2text, langchain)
- [ ] Время извлечения PDF не увеличивается (kreuzberg Rust core быстрее pypdf)
