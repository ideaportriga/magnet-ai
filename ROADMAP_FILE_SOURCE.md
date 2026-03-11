# Roadmap: Модернизация Knowledge Source «File» (эксперимент)

> **Scope:** Только legacy-система `UrlDataSource` / `UrlDataProcessor` / `FileUrlPlugin`.  
> `FileUploadDataSource` (modern «Upload») — **не трогаем**.

## Контекст

Legacy knowledge source «File» (`UrlDataSource`) сейчас ограничен:
- Принимает **только URL-ссылки** (нет загрузки файлов из ФС)
- Обрабатывает **только PDF** (`allowed_extensions=[".pdf"]`, hardcoded в процессоре)

| Компонент | Текущее состояние | Цель |
|---|---|---|
| `UrlDataSource` | `allowed_extensions=[".pdf"]` | Все форматы kreuzberg |
| `UrlDataProcessor` | `__create_pdf_documents()` — только PDF | Format-agnostic через `extract_bytes()` |
| `FileUrlPlugin` | `"Only links to PDF files are accepted"` | Поддержка всех форматов + загрузка файлов |
| Frontend (`collections.js`) | `km-input-list-add` — только URL | URL + файловый upload |

**Цели эксперимента:**
1. Полная поддержка всех форматов kreuzberg (75+ типов) в legacy File source
2. Поддержка загрузки файлов из файловой системы (не только URL)

---

## Фаза 0 — Расширение UrlDataProcessor для всех форматов

> Снять ограничение «только PDF», чтобы legacy-система обрабатывала все поддерживаемые kreuzberg форматы.

- [x] **0.1** `UrlDataSource` — убрать `allowed_extensions=[".pdf"]`, заменить на `None` (принимать все форматы)
- [x] **0.2** `UrlDataProcessor.create_chunks_from_doc()` — заменить `if file_name.lower().endswith(".pdf")` на format-agnostic обработку:
  - Определить MIME-тип по расширению файла (через `mime_type_from_filename()`)
  - Вызвать `extract_bytes()` с правильным MIME-типом вместо hardcoded `"application/pdf"`
  - Убрать ветку `else: logger.info("Non-PDF file detected... Skipping processing.")`
- [x] **0.3** Переименовать `__create_pdf_documents()` → `__create_documents_from_bytes()` (format-agnostic)
- [x] **0.4** `FileUrlPlugin.metadata.config_schema` — обновить описание с `"Only links to PDF files are accepted"` на `"Links to supported document files (PDF, DOCX, XLSX, PPTX, HTML, images, etc.)"`
- [x] **0.5** `collections.js` — обновить описание поля `file_url` с `"Only links to PDF files are accepted"` на описание поддерживаемых форматов
- [x] **0.6** Unit-тесты для `UrlDataProcessor` с различными форматами файлов (`.pdf`, `.docx`, `.html`, `.png`)

**Файлы:**
- `api/src/data_sources/file/source.py` — `UrlDataSource.__init__`
- `api/src/data_sync/processors/file_data_processor.py` — `UrlDataProcessor`
- `api/src/plugins/builtin/knowledge_source/file/plugin.py` — `FileUrlPlugin.metadata`
- `web/apps/@ipr/magnet-admin/src/config/collections/collections.js`

---

## Фаза 1 — Добавление загрузки файлов из ФС

> Расширить legacy «File» source, чтобы помимо URL можно было загружать файлы напрямую из файловой системы браузера.

### 1.1 Backend

- [x] **1.1.1** Добавить endpoint загрузки файла для collection source:
  - `POST /api/admin/collections/{id}/upload_file` — принимает multipart файл
  - Сохраняет файл в локальное хранилище (`./files/` или настраиваемый путь)
  - Добавляет запись в `source_config.uploaded_files` — список `{filename, storage_path}`
- [x] **1.1.2** Расширить `FileUrlPlugin.config_schema` — новое поле `uploaded_files`
- [x] **1.1.3** Расширить `UrlDataSource` — принимать помимо URL ещё и пути к локальным файлам:
  - Новый параметр `local_files: list[dict]` (filename + storage_path)
  - `get_data()` возвращает как URL, так и локальные идентификаторы
- [x] **1.1.4** Расширить `UrlDataProcessor`:
  - `create_chunks_from_doc()` — если id начинается с `local://`, читать файл из хранилища вместо HTTP download
  - Общая обработка через `extract_bytes()` для обоих случаев
- [x] **1.1.5** Endpoint удаления загруженного файла:
  - `DELETE /api/admin/collections/{id}/uploaded_file/{filename}`
  - Удаляет файл из хранилища и из `source_config.uploaded_files`

### 1.2 Frontend

- [x] **1.2.1** Заменить `km-input-list-add` на комбинированный компонент с табами:
  - Tab «URL» — существующий ввод URL (как сейчас)
  - Tab «Upload» — `q-file` для выбора файлов из ФС
- [x] **1.2.2** Компонент загрузки файлов:
  - `q-file` с поддержкой множественного выбора
  - Drag & drop зона
  - Список загруженных файлов с возможностью удаления
  - Прогресс-бар загрузки
- [x] **1.2.3** Обновить `collections.js` — новая конфигурация поля для комбинированного компонента
- [x] **1.2.4** Подсказка с поддерживаемыми форматами

**Файлы:**
- `api/src/data_sources/file/source.py` — `UrlDataSource`
- `api/src/data_sync/processors/file_data_processor.py` — `UrlDataProcessor`
- `api/src/plugins/builtin/knowledge_source/file/plugin.py` — `FileUrlPlugin`
- `web/apps/@ipr/magnet-admin/src/config/collections/collections.js`
- Новый Vue-компонент для комбинированного URL/Upload ввода

---

## Фаза 2 — Валидация и безопасность

- [x] **2.1** Backend: валидация MIME-типа файла (magic bytes, не только расширение)
- [x] **2.2** Backend: лимит размера файла через env variable (`MAX_UPLOAD_FILE_SIZE_MB`)
- [x] **2.3** Frontend: `accept` filter в `<q-file>` с перечислением поддерживаемых расширений
- [x] **2.4** Frontend: валидация формата при drop (отклонять неподдерживаемые файлы с сообщением)
- [x] **2.5** Логирование всех операций загрузки для audit trail

---

## Порядок реализации

| Шаг | Фаза | Описание | Сложность |
|---|---|---|---|
| 1 | 0 | Снятие ограничения PDF-only (все форматы kreuzberg) | Средняя |
| 2 | 1 | Загрузка файлов из ФС + UI с табами | Высокая |
| 3 | 2 | Валидация и безопасность | Низкая |

---

## Текущие ограничения legacy-системы

```
UrlDataSource.__init__:   allowed_extensions=[".pdf"]     ← hardcoded
UrlDataProcessor:         if file_name.endswith(".pdf")   ← only PDF processed
                          else: "Skipping processing"     ← all other formats ignored
FileUrlPlugin:            "Only links to PDF files"       ← schema description
collections.js:           "Only links to PDF files"       ← UI label
```

## Форматы kreuzberg, которые нужно поддержать

- **Документы:** `.pdf`, `.doc`, `.docx`, `.odt`, `.rtf`, `.epub`
- **Таблицы:** `.xls`, `.xlsx`, `.ods`, `.csv`
- **Презентации:** `.ppt`, `.pptx`, `.odp`
- **Веб:** `.html`, `.htm`, `.xml`
- **Изображения (OCR):** `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.tiff`
- **Email:** `.eml`, `.msg`
- **Текст:** `.txt`, `.md`, `.json`
