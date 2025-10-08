# External Plugins Strategy Guide

## Стратегии работы с client-specific плагинами

Есть три основных подхода к управлению external плагинами, которые не должны попадать в публичный репозиторий:

---

## ✅ Рекомендуемый подход: Отдельные Private Репозитории

### Структура

```
your-org/
├── magnet-ai/                          # Публичный основной репозиторий
│   └── api/
│       └── src/
│           └── plugins/
│               ├── builtin/            # Публичные плагины
│               └── external/           # Пустая папка (только __init__.py)
│
├── magnet-plugins-client-a/           # Приватный репозиторий для клиента A
│   └── magnet_plugins_client_a/
│       └── custom_source.py
│
└── magnet-plugins-client-b/           # Приватный репозиторий для клиента B
    └── magnet_plugins_client_b/
        └── legacy_system.py
```

### Преимущества

✅ **Полная изоляция** - client-specific код не попадает в основной репозиторий  
✅ **Отдельный доступ** - можно дать доступ только нужным людям  
✅ **Независимые версии** - каждый клиент может использовать свою версию плагина  
✅ **Простая установка** - через pip install git+https://...  
✅ **CI/CD ready** - легко интегрируется в pipeline  

### Недостатки

⚠️ Требуется создать отдельные репозитории  
⚠️ Нужно управлять версиями плагинов отдельно  

### Как использовать

#### 1. Создайте private репозиторий для каждого client-specific плагина

```bash
# Для клиента A
mkdir magnet-plugins-client-a
cd magnet-plugins-client-a

mkdir -p magnet_plugins_client_a
touch magnet_plugins_client_a/__init__.py
```

#### 2. Скопируйте код плагина

```bash
cp ../magnet-ai/api/src/plugins/external/knowledge_source/file.py \
   magnet_plugins_client_a/custom_source.py
```

#### 3. Создайте setup.py

```python
from setuptools import setup, find_packages

setup(
    name="magnet-plugins-client-a",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        # Dependencies from main magnet-ai
    ],
)
```

#### 4. Установка при деплое

```dockerfile
# Dockerfile
FROM python:3.12

# Install main application
COPY api/ /app/api/
RUN pip install -e /app/api

# Install client-specific plugin from private repo
ARG GITHUB_TOKEN
RUN pip install git+https://${GITHUB_TOKEN}@github.com/your-org/magnet-plugins-client-a.git@v1.0.0

ENV MAGNET_PLUGINS=magnet_plugins_client_a.custom_source
```

```yaml
# docker-compose.yml
services:
  api:
    build:
      context: .
      args:
        GITHUB_TOKEN: ${GITHUB_TOKEN}
    environment:
      - MAGNET_PLUGINS=magnet_plugins_client_a.custom_source
```

#### 5. CI/CD Pipeline

```yaml
# .github/workflows/deploy-client-a.yml
name: Deploy for Client A

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        env:
          GH_TOKEN: ${{ secrets.GH_TOKEN }}
        run: |
          pip install -e ./api
          pip install git+https://${GH_TOKEN}@github.com/your-org/magnet-plugins-client-a.git@v1.0.0
      
      - name: Deploy
        env:
          MAGNET_PLUGINS: magnet_plugins_client_a.custom_source
        run: |
          # Your deployment script
```

---

## 🔄 Альтернатива 1: Git Submodules (средняя сложность)

### Структура

```
magnet-ai/
├── api/
│   └── src/
│       └── plugins/
│           ├── builtin/
│           └── external/
│               └── client_a/         # Git submodule -> private repo
│                   └── knowledge_source/
│                       └── custom.py
```

### Как использовать

```bash
# Добавьте submodule в external/
cd api/src/plugins/external
git submodule add https://github.com/your-org/magnet-plugins-client-a.git client_a

# В .gitignore основного репозитория
echo "src/plugins/external/client_a/" >> .gitignore

# При клонировании для клиента A
git clone https://github.com/your-org/magnet-ai.git
cd magnet-ai
git submodule init
git submodule update --init --recursive api/src/plugins/external/client_a
```

### Преимущества

✅ Все в одном месте при разработке  
✅ Автоматическая загрузка плагинов (без MAGNET_PLUGINS)  
✅ Легко переключаться между версиями  

### Недостатки

⚠️ Сложнее в управлении для команды  
⚠️ Можно случайно закоммитить submodule reference  
⚠️ Требует аккуратности при работе с git  

---

## 📁 Альтернатива 2: Local External Directory (только для разработки)

### Структура

```
magnet-ai/
└── api/
    └── src/
        └── plugins/
            ├── builtin/              # В git
            └── external/             # В .gitignore (кроме __init__.py)
                └── knowledge_source/
                    ├── __init__.py   # В git
                    ├── file.py       # НЕ в git
                    └── fluidtopics.py # НЕ в git
```

### Как использовать

#### 1. Настройте .gitignore

```bash
# .gitignore
# Exclude all external plugins except __init__.py files
src/plugins/external/*/
!src/plugins/external/*/__init__.py
!src/plugins/external/__init__.py
```

#### 2. Для деплоя - используйте volume mounting

```yaml
# docker-compose.yml
services:
  api:
    build:
      context: .
    volumes:
      # Mount client-specific plugins from secure location
      - /secure/client-a-plugins:/app/api/src/plugins/external/knowledge_source
    environment:
      - MAGNET_PLUGINS=  # Empty - use auto-loaded from directory
```

#### 3. Или скопируйте при сборке

```dockerfile
# Dockerfile
FROM python:3.12

COPY api/ /app/api/

# Copy client-specific plugins from build context
ARG CLIENT_NAME
COPY ${CLIENT_NAME}-plugins/* /app/api/src/plugins/external/knowledge_source/

RUN pip install -e /app/api
```

```bash
# Build for different clients
docker build --build-arg CLIENT_NAME=client-a -t magnet-client-a .
docker build --build-arg CLIENT_NAME=client-b -t magnet-client-b .
```

### Преимущества

✅ Простота - нет дополнительных репозиториев  
✅ Автоматическая загрузка плагинов  
✅ Не нужны переменные окружения  

### Недостатки

⚠️ Риск случайного коммита в основной репозиторий  
⚠️ Сложнее управление версиями плагинов  
⚠️ Нужны внешние механизмы для доставки плагинов  
⚠️ Не подходит для публичного GitHub репозитория  

---

## 🎯 Рекомендации по выбору стратегии

### Используйте **Отдельные Репозитории** если:

✅ Публикуете основной код на GitHub  
✅ Работаете с несколькими клиентами  
✅ Нужен строгий контроль доступа  
✅ Важна изоляция client-specific кода  
✅ Используете CI/CD  

### Используйте **Git Submodules** если:

✅ Команда опытна с git  
✅ Нужна тесная интеграция при разработке  
✅ Хотите версионировать связь main repo ↔ plugin  

### Используйте **Local Directory** только если:

✅ Это temporary решение  
✅ Только для development  
✅ НЕ публикуете на GitHub  

---

## 📋 Checklist для публикации на GitHub

Перед публикацией основного репозитория:

### 1. Проверьте .gitignore

```bash
# Убедитесь что external плагины исключены
cat .gitignore | grep external

# Должно быть:
src/plugins/external/*/
!src/plugins/external/*/__init__.py
!src/plugins/external/__init__.py
```

### 2. Проверьте что будет закоммичено

```bash
git status
git ls-files src/plugins/external/
# Должны быть только __init__.py файлы
```

### 3. Удалите чувствительные данные

```bash
# Проверьте историю
git log --all --full-history -- src/plugins/external/

# Если нужно, очистите историю
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch src/plugins/external/knowledge_source/file.py' \
  --prune-empty --tag-name-filter cat -- --all
```

### 4. Создайте README для external/

```bash
cat > api/src/plugins/external/README.md << 'EOF'
# External Plugins

This directory is for client-specific plugins that are not part of the public repository.

## For Development

Place your external plugins here. They will be auto-loaded.

## For Production

Use one of these methods:
1. Install from private repository: `pip install git+https://...`
2. Mount as volume in Docker
3. Copy during build process

See EXTERNAL_PLUGINS_STRATEGY.md for details.
EOF
```

### 5. Обновите документацию

```bash
# Добавьте в README.md
echo "## External Plugins

Client-specific plugins should be installed separately.
See [EXTERNAL_PLUGINS_STRATEGY.md](./EXTERNAL_PLUGINS_STRATEGY.md) for details.
" >> README.md
```

---

## 🔒 Security Best Practices

### 1. GitHub Tokens

```bash
# Используйте read-only токены с ограниченным scope
# Только для private repos
gh auth login --scopes "repo"

# В CI/CD используйте secrets
# GitHub Actions: ${{ secrets.GH_TOKEN }}
# GitLab CI: $CI_JOB_TOKEN
```

### 2. Credentials в плагинах

```python
# ❌ НЕ ДЕЛАЙТЕ ТАК
class FilePlugin(KnowledgeSourcePlugin):
    def __init__(self):
        self.api_key = "hardcoded-key"  # NEVER!

# ✅ ДЕЛАЙТЕ ТАК
class FilePlugin(KnowledgeSourcePlugin):
    def __init__(self):
        self.api_key = os.environ.get("CLIENT_A_API_KEY")
```

### 3. Разные .env для клиентов

```bash
# .env.client-a (не в git)
MAGNET_PLUGINS=magnet_plugins_client_a.custom_source
CLIENT_A_API_KEY=secret123
CLIENT_A_ENDPOINT=https://client-a.example.com

# .env.client-b (не в git)
MAGNET_PLUGINS=magnet_plugins_client_b.legacy_system
CLIENT_B_TOKEN=token456
CLIENT_B_DATABASE_URL=postgresql://...
```

---

## 📊 Сравнительная таблица

| Критерий | Separate Repos | Git Submodules | Local Directory |
|----------|---------------|----------------|-----------------|
| Изоляция кода | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Простота setup | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Контроль доступа | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| CI/CD integration | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Version management | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Development UX | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Риск утечки кода | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |

---

## 🚀 Quick Start для рекомендуемого подхода

### Шаг 1: Подготовьте основной репозиторий

```bash
cd magnet-ai/api

# Обновите .gitignore
cat >> .gitignore << 'EOF'
# External plugins (client-specific)
src/plugins/external/*/
!src/plugins/external/*/__init__.py
!src/plugins/external/__init__.py
EOF

# Удалите external плагины из git (если уже закоммичены)
git rm --cached src/plugins/external/knowledge_source/file.py
git rm --cached src/plugins/external/knowledge_source/fluidtopics.py
git commit -m "Remove client-specific plugins from main repo"
```

### Шаг 2: Создайте репозиторий для плагина

```bash
cd /path/to/projects
mkdir magnet-plugins-file
cd magnet-plugins-file

# Инициализируйте git
git init
gh repo create magnet-plugins-file --private

# Создайте структуру
mkdir -p magnet_plugins/file
touch magnet_plugins/__init__.py

# Скопируйте код
cp /path/to/magnet-ai/api/src/plugins/external/knowledge_source/file.py \
   magnet_plugins/file/plugin.py

# Создайте setup.py
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="magnet-plugins-file",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.12",
)
EOF

# Коммит и тег
git add .
git commit -m "Initial version"
git tag v1.0.0
git push origin main --tags
```

### Шаг 3: Установите при деплое

```bash
# В вашем deployment скрипте
pip install git+https://${GITHUB_TOKEN}@github.com/your-org/magnet-plugins-file.git@v1.0.0

# Установите переменную окружения
export MAGNET_PLUGINS=magnet_plugins.file.plugin
```

---

## 💡 Итоговая рекомендация

Для публикации на GitHub рекомендую:

1. ✅ **Основной репозиторий (публичный):**
   - Содержит builtin плагины
   - External plugins папка пустая (только __init__.py)
   - Документация по установке external плагинов

2. ✅ **Client-specific плагины (приватные репозитории):**
   - Каждый плагин в отдельном private repo
   - Установка через `pip install git+https://...`
   - Загрузка через `MAGNET_PLUGINS` env var

3. ✅ **Для development:**
   - Можно держать плагины локально в `external/`
   - `.gitignore` предотвратит случайный коммит
   - Автоматическая загрузка без env vars

Это дает максимальную гибкость и безопасность! 🎯
