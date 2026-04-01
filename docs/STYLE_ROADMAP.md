# Style System Roadmap — magnet-ai

> Дата аудита: 2026-03-28
> Препроцессор: Stylus
> Фреймворк: Vue 3 + Quasar

---

## Критические находки

### Конфликт Primary Color

`quasar-variables.sass` (Quasar SCSS-тема):
```sass
$primary: #1976D2   ← СИНИЙ (Material Blue)
```

`factory.styl` (CSS variables через generateColorClasses):
```stylus
primary: #6840c2    ← ФИОЛЕТОВЫЙ (реальный бренд)
```

Quasar-компоненты (`color="primary"`) рендерятся синим, а `var(--q-primary)` — фиолетовым.

---

## Приоритизированный Roadmap

### P0 — Синхронизация Quasar Variables *(Неотложно)*

Файл: `apps/@ipr/magnet-admin/src/styles/quasar-variables.sass`

```sass
$primary:   #6840c2   // исправить с #1976D2
$secondary: #959EA4   // исправить с #26A69A
$positive:  #BDF2D5   // привести к системе
$negative:  #FF5660   // привести к системе (сейчас #dd7e89)
$warning:   #FCEC87   // привести к системе
$info:      #31CCEC   // оставить
```

---

### P1 — Создать tokens/ директорию *(Неделя 1)*

Новая файловая структура:

```
packages/themes/src/base/
├── tokens/
│   ├── _colors.styl
│   ├── _typography.styl
│   ├── _spacing.styl
│   ├── _radii.styl
│   ├── _elevation.styl
│   └── _components.styl
├── factory.styl        ← импортирует tokens/*, генерирует классы
├── typography.styl
├── fields.styl
├── quasar_overrides.styl
├── functions.styl
└── app.styl
```

---

### P2 — Typography система *(Неделя 2)*

Файл: `tokens/_typography.styl`

#### Новая иерархия

| Класс | Size | Weight | Line-height | Назначение |
|---|---|---|---|---|
| `.km-display` | 24px | 700 | 1.2 | Крупные заголовки страниц |
| `.km-h1` | 20px | 700 | 1.3 | Заголовки секций |
| `.km-h2` | 18px | 700 | 1.3 | Подзаголовки |
| `.km-h3` | 16px | 600 | 1.4 | Заголовки карточек |
| `.km-h4` | 14px | 600 | 1.4 | Метки, подписи к группам |
| `.km-h5` | 13px | 600 | 1.4 | Мелкие заголовки |
| `.km-body-lg` | 16px | 400 | 1.5 | Крупный основной текст |
| `.km-body` | 14px | 400 | 1.5 | Стандартный текст |
| `.km-body-sm` | 13px | 400 | 1.5 | Мелкий текст |
| `.km-caption` | 12px | 400 | 1.4 | Подписи, описания |
| `.km-tiny` | 11px | 400 | 1.4 | Минимальный текст |
| `.km-label` | 12px | 500 | 1 | Лейблы полей |
| `.km-btn` | 13px | 600 | 1 | Текст кнопок |
| `.km-chip` | 12px | 600 | 1 | Чипы/бейджи |

#### Алиасы (backward compatibility)

```stylus
.km-heading-6  { @extend .km-h1 }
.km-heading-7  { @extend .km-h2 }
.km-heading-4  { @extend .km-h3 }
.km-heading-5  { @extend .km-h3 }
.km-heading-2  { @extend .km-h4 }
.km-heading-3  { @extend .km-h4 }
.km-heading-1  { @extend .km-h5 }
.km-paragraph  { @extend .km-body }
.km-title      { @extend .km-h4 }
.km-description { @extend .km-caption }
.km-button-text    { @extend .km-btn }
.km-button-sm-text { @extend .km-btn }
```

---

### P3 — Color Palette *(Неделя 1–2)*

Файл: `tokens/_colors.styl`

```stylus
// === BRAND ===
$color-brand-primary:       #6840c2
$color-brand-primary-light: #E5E3F2
$color-brand-primary-bg:    rgba(80, 47, 153, 0.07)
$color-brand-secondary:     #959EA4
$color-brand-secondary-bg:  rgba(149, 158, 164, 0.2)
$color-brand-accent:        #4d82a5
$color-brand-accent-bg:     #ECF4F9

// === SEMANTIC ===
$color-success:             #BDF2D5
$color-success-text:        #00A876
$color-warning:             #FCEC87
$color-warning-text:        #474641
$color-warning-bg:          #fff9d4
$color-error:               #e62222
$color-error-text:          #FF5660
$color-error-bg:            #ffecec
$color-info:                #31CCEC

// === NEUTRALS ===
$color-text-primary:        #171717
$color-text-secondary:      #424242
$color-text-weak:           #5C5C5C
$color-text-placeholder:    rgba(0, 0, 0, 0.50)
$color-border:              #EAEAF6
$color-border-strong:       #C4C7CF
$color-bg:                  #FBFBFE
$color-bg-light:            #F4F2F8
$color-bg-control:          rgb(251, 251, 251)
$color-white:               #ffffff
$color-black:               #191B23

// === STATES ===
$color-control-bg:          rgb(251, 251, 251)
$color-control-border:      #EAEAF6
$color-control-hover-bg:    whitesmoke
$color-control-hover-border: #cdcdd5
$color-control-active-bg:   var(--q-primary-bg)
$color-control-active-border: var(--q-primary)

// === STATUS LABELS ===
$color-status-ready:        #E9FCE9
$color-status-ready-text:   #00A876
$color-status-processing:   #FFF7D9
$color-status-processing-text: #FF9518

// === TABLES ===
$color-table-header:        #F7F7FC
$color-table-hover:         rgba(0, 0, 0, 0.03)
$color-table-active:        rgba(0, 0, 0, 0.06)
```

---

### P4 — Border Radius Scale *(Неделя 4)*

Файл: `tokens/_radii.styl`

```stylus
$radius-xs:   2px    // чекбоксы, скроллбар
$radius-sm:   4px    // chips, теги, btn-group
$radius-md:   6px    // кнопки, средние элементы
$radius-lg:   8px    // карточки, диалоги
$radius-xl:   12px   // большие контейнеры, секции
$radius-full: 50%    // круглые иконки/аватары
```

Генерируемые классы (оставить существующие + добавить переменные):

```stylus
// Существующие классы через переменные
.border-radius-4  { border-radius: $radius-sm }
.border-radius-6  { border-radius: $radius-md }
.border-radius-8  { border-radius: $radius-lg }
.border-radius-12 { border-radius: $radius-xl }
.round            { border-radius: $radius-full }
```

---

### P5 — Spacing Scale *(Неделя 4)*

Файл: `tokens/_spacing.styl`

```stylus
// 4px-based scale
$space-1:  4px
$space-2:  8px
$space-3:  12px
$space-4:  16px
$space-5:  20px   // заменить нестандартный 18px
$space-6:  24px
$space-7:  32px
$space-8:  40px
$space-9:  48px
$space-10: 64px
```

Обновить список в `factory.styl`:
```stylus
// Было:
$spacing-sizes = 40, 32, 24, 18, 16, 12, 6, 4, 8, 2, 1;

// Станет:
$spacing-sizes = 64, 48, 40, 32, 24, 20, 16, 12, 8, 6, 4, 2;
```

---

### P6 — Elevation Scale *(Неделя 4)*

Файл: `tokens/_elevation.styl`

```stylus
$shadow-none:    none
$shadow-sm:      0px 1px 4px rgba(0, 0, 0, 0.06)    // dropdown, tooltip
$shadow-md:      0px 2px 10px rgba(0, 0, 0, 0.08)   // карточки
$shadow-lg:      0px 4px 12px rgba(0, 0, 0, 0.10)   // модальные окна
$shadow-xl:      0px 8px 24px rgba(0, 0, 0, 0.12)   // боковые панели
$shadow-primary: 0px 2px 8px rgba(104, 64, 194, 0.25) // primary кнопки
```

Заменить в `app.styl`:
```stylus
// Было:
.shadow       { box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.08) }
.block-shadow { box-shadow: 0px 4px 12px 0px rgba(0, 0, 0, 0.10) }

// Станет:
.shadow-sm  { box-shadow: $shadow-sm }
.shadow     { box-shadow: $shadow-md }    // алиас для совместимости
.shadow-lg  { box-shadow: $shadow-lg }
.shadow-xl  { box-shadow: $shadow-xl }
.block-shadow { box-shadow: $shadow-lg }  // алиас для совместимости
```

---

### P7 — Component Tokens *(Недели 5–6)*

Файл: `tokens/_components.styl`

```stylus
:root
  // Buttons
  --btn-height-xs:    22px
  --btn-height-sm:    28px
  --btn-height-md:    34px
  --btn-height-lg:    40px
  --btn-radius:       var(--radius-md)   // 6px

  // Inputs / Fields
  --field-height:     34px
  --field-radius:     var(--radius-md)   // 6px

  // Cards
  --card-radius:      var(--radius-xl)   // 12px
  --card-padding:     16px

  // Dialogs
  --dialog-radius:    var(--radius-lg)   // 8px
  --dialog-padding:   24px
  --dialog-width-sm:  400px
  --dialog-width-md:  500px
  --dialog-width-lg:  676px

  // Chips
  --chip-height:      20px
  --chip-radius:      var(--radius-sm)   // 4px

  // Tables
  --table-header-bg:  var(--q-table-header)
  --table-row-height: 48px
```

Компоненты для обновления (приоритет):

| Компонент | Файл | Задача |
|---|---|---|
| `Btn.vue` | `packages/ui-comp/src/components/base/Btn.vue` | Использовать `--btn-height-*`, `--btn-radius` |
| `Input.vue` | `packages/ui-comp/.../Input.vue` | Использовать `--field-height`, `--field-radius` |
| `Dialog.vue` | `packages/ui-comp/.../Dialog.vue` | Использовать `--dialog-*` переменные |
| `PopupConfirm.vue` | `packages/ui-comp/.../PopupConfirm.vue` | Убрать inline `width: 676px` |
| `ErrorDialog.vue` | `packages/ui-comp/.../ErrorDialog.vue` | Убрать inline `border-radius: 0px 0px 8px 8px` |

---

## План миграции

### Порядок и сроки

```
Неделя 1
├── P0: Исправить quasar-variables.sass (primary, secondary, positive, negative)
├── P1: Создать tokens/ директорию, перенести $colors из factory.styl
└── P3: Убрать дублирующиеся определения цветов, мёртвый закомментированный код

Неделя 2
├── P2: Создать новые km-h1..5, km-body*, km-caption классы
├── P2: Добавить алиасы для старых km-heading-* (backward compat)
└── P2: Добавить line-height во все типографические классы

Неделя 3
└── P3: Заменить хардкодные hex-значения токенами (factory.styl, app.styl, компоненты)

Неделя 4
├── P4: Переменные для border-radius, обновить app.styl
├── P5: Стандартизировать spacing-sizes (убрать 18, добавить 20, 48, 64)
└── P6: Создать elevation scale, заменить .shadow / .block-shadow

Недели 5–6
├── P7: Обновить Btn.vue, Input.vue, Dialog.vue через component tokens
└── P7: Устранить inline styles в magnet-admin компонентах
```

### Правила минимизации регрессий

1. **Алиасы вместо удаления** — старые классы (`km-heading-*`, `.shadow`, `.block-shadow`) остаются как `@extend` на новые
2. **Начинать с `packages/ui-comp`** — изменение базовых компонентов распространяется на все 464 .vue файла
3. **Inline styles** — выносить в component CSS vars или утилитарные классы, не удалять без замены
4. **`em` и `pt`** — аудировать происхождение перед заменой (могут быть единицы иконочных шрифтов)
5. **Тестировать на всех 3 темах** (default, salesforce, siebel) после каждого изменения в `factory.styl`

---

## Известные проблемы (дополнительно)

| Проблема | Файл | Строки |
|---|---|---|
| `user-input-bg` определён дважды | `factory.styl` | 133, 136 |
| Закомментированные старые цвета | `factory.styl` | 40–47, 60–73 |
| `font-family` закомментирован | `typography.styl` | 82 |
| TODO-комментарий с вопросом | `app.styl` | 50 |
| Конфликт `quasar-variables.sass` vs `factory.styl` | оба файла | весь файл |
