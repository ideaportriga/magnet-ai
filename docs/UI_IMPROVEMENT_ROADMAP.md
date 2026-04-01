# UI Improvement Roadmap — magnet-admin

> Дата составления: 2026-03-28

---

## Обзор

Анализ кодовой базы выявил четыре категории улучшений:

1. **Дедупликация мёртвого кода** — скопированные стили и утилиты, которые можно убрать
2. **Унификация паттернов** — одинаковые UI-элементы, реализованные по-разному
3. **Resizable Drawers** — возможность менять ширину правой панели перетаскиванием
4. **Рефакторинг левого меню** — collapsed-режим, collapsable секции, исправление layout
5. **Унификация правых Drawer-панелей** — единый layout-компонент, стандартные отступы/заголовки/скролл

---

## Этап 1 — Дедупликация мёртвого и скопированного кода

### 1.1 Удалить `@keyframes wobble` / `.wobble` из 19 файлов

**Проблема:** анимация `.wobble` определена в 19 компонентах через copy-paste, но нигде не используется в шаблонах — это мёртвый CSS-код.

**Затронутые файлы:**
`Configuration/details.vue`, `AIApps/settings.vue`, `AIApps/details.vue`, `AIApps/records.vue`, `Agents/details.vue`, `Agents/topicDetails.vue`, `Agents/DrawerAction.vue`, `Agents/actionDetails.vue`, `ModelConfig/details.vue`, `Retrieval/details.vue`, `EvaluationJobs/details.vue`, `EvaluationJobs/detailsCompare.vue`, `EvaluationJobs/detailsTool.vue`, `EvaluationJobs/block.vue`, `EvaluationJobs/detailsJob.vue`, `Prompts/details.vue`, `EvaluationSets/details.vue`, `Collections/details.vue`, `AssistantTools/details.vue`

**Решение:** удалить `@keyframes wobble` и `.wobble` из всех `<style>` блоков. Если анимация понадобится — добавить в `packages/themes/src/utilities.styl`.

---

### 1.2 Удалить дублированный метод `formatDate()`

**Проблема:** один и тот же метод форматирования даты скопирован в 14+ Header/SubHeader-компонентах.

```js
// копи-паст в каждом файле:
formatDate(date) {
  const dateObject = new Date(date)
  const localeDateString = dateObject.toLocaleDateString()
  const localeTimeString = dateObject.toLocaleTimeString()
  return `${localeDateString} ${localeTimeString}`
}
```

**Затронутые файлы:** `Configuration/Header.vue`, `Agents/Header.vue`, `Agents/SubHeader.vue`, `AIApps/Header.vue`, `Collections/Header.vue`, `DeepResearch/Configs/Header.vue`, `ModelConfig/Header.vue` и другие.

**Решение:** использовать существующую утилиту `formatDateTime` из `@shared/utils/dateTime` (она уже используется в `Dashboard/Drawer/Llm.vue`, значит работает). Удалить локальные определения.

---

### 1.3 Удалить мёртвые методы `deleteXxx()` из `details.vue`

**Проблема:** в ~6 файлах `details.vue` определены методы удаления через `$q.notify()`, которые никогда не вызываются из шаблона (удаление обрабатывает `Header.vue`).

**Затронутые файлы:** `Agents/details.vue`, `AssistantTools/details.vue`, `Prompts/details.vue`, `Retrieval/details.vue`, `Configuration/details.vue`, `EvaluationJobs/details.vue`

**Решение:** удалить мёртвые методы.

---

## Этап 2 — Унификация паттернов

### 2.1 Мигрировать все detail-страницы на `DetailsLayout`

**Проблема:** два конкурирующих паттерна для страниц деталей:
- **Старый (~8 файлов):** ручная flex-структура с `style=` и копи-пастом блока заголовка
- **Новый (2 файла):** `layouts-details-layout` со слотами

**Затронутые файлы (нужна миграция):**
`Agents/details.vue`, `Collections/details.vue`, `Configuration/details.vue`, `ModelConfig/details.vue`, `Retrieval/details.vue`, `AssistantTools/details.vue`, `Prompts/details.vue`, `EvaluationSets/details.vue`

**Решение:** мигрировать каждый файл на использование `layouts-details-layout` + слоты `#header`, `#content`, `#drawer`. Это автоматически убирает дубликаты блока name/description/system_name, который уже выделен в `layouts-details-header`.

---

### 2.2 Извлечь `q-tabs` в обёртку

**Проблема:** блок из 8 одинаковых пропов повторяется на каждой detail-странице:

```pug
q-tabs.bb-border.full-width(
  v-model='tab',
  narrow-indicator, dense, align='left',
  active-color='primary', indicator-color='primary',
  active-bg-color='white', no-caps,
  content-class='km-tabs'
)
```

**Решение:** создать компонент `km-tabs-nav` в `packages/ui-comp`, который принимает только `v-model` и прокидывает слот для `q-tab`-элементов. Все проп-умолчания задать внутри.

---

### 2.3 Унифицировать использование `km-inner-loading`

**Проблема:** `q-inner-loading` с спиннером используется в 30+ местах напрямую, хотя в `ui-comp` есть `km-inner-loading`.

**Решение:** заменить все прямые `q-inner-loading` на `km-inner-loading`. Убедиться, что компонент покрывает все случаи использования.

---

### 2.4 Унифицировать использование `km-empty-state`

**Проблема:** `km-empty-state` используется только в 1 месте. Пустые списки во всех остальных местах рендерят произвольный текст напрямую.

**Решение:** найти все "пустые состояния" (пустые списки, `v-if='!items.length'` с текстом) и заменить на `km-empty-state`.

---

### 2.5 Унифицировать ширину Drawer-компонентов через CSS-класс

**Проблема:** 20+ Drawer-компонентов задают ширину через inline-стили по-разному:
- `min-width: 500px; max-width: 500px`
- `max-width: 500px; min-width: 500px !important`
- `max-width: 500px; min-width: 500px`

Нет единого подхода, нет CSS-класса.

**Решение:** добавить утилитный класс в `packages/themes/src/utilities.styl`:
```stylus
.km-side-drawer
  min-width: var(--drawer-width, 500px)
  max-width: var(--drawer-width, 500px)
  width: var(--drawer-width, 500px)
```
И заменить все inline-стили на этот класс (реализуется в Этапе 4 вместе с drag-resize).

---

## Этап 3 — Resizable Drawers

### Цель

Все Drawer-компоненты (правые панели) должны поддерживать изменение ширины перетаскиванием разделительной границы (resize handle). Ширина должна сохраняться в `localStorage` отдельно для каждого Drawer.

### Дизайн решения

#### 3.1 Создать composable `useDrawerResize`

**Файл:** `packages/ui-comp/src/composables/useDrawerResize.ts`

```ts
// Принимает: имя (ключ localStorage), минимальная ширина, максимальная ширина, ширина по умолчанию
// Возвращает: ширина (ref), обработчики событий мыши для resize handle
export function useDrawerResize(options: {
  storageKey: string
  defaultWidth?: number  // default: 500
  minWidth?: number      // default: 320
  maxWidth?: number      // default: 900
}): {
  width: Ref<number>
  drawerStyle: ComputedRef<Record<string, string>>
  onResizeStart: (e: MouseEvent) => void
}
```

Логика:
1. Загрузить ширину из `localStorage` при инициализации
2. При `mousedown` на resize handle — начать отслеживание `mousemove`
3. Вычислять новую ширину как `startWidth - (e.clientX - startX)` (Drawer справа)
4. Зажать значение в `[minWidth, maxWidth]`
5. При `mouseup` — сохранить в `localStorage`
6. Очищать слушатели при `onUnmounted`

#### 3.2 Создать компонент `DrawerResizeHandle`

**Файл:** `packages/ui-comp/src/components/base/DrawerResizeHandle.vue`

```html
<!-- Вертикальная полоска 4px шириной, курсор col-resize -->
<!-- При hover — подсвечивать цветом primary -->
<!-- Позиционируется абсолютно по левому краю Drawer -->
```

#### 3.3 Добавить CSS-переменную и класс в дизайн-систему

**Файл:** `packages/themes/src/utilities.styl`

```stylus
// CSS-класс для drawer-контейнера
.km-side-drawer
  position: relative  // для абсолютного позиционирования handle
  min-width: var(--km-drawer-width, 500px)
  max-width: var(--km-drawer-width, 500px)
  width: var(--km-drawer-width, 500px)
  transition: none  // без плавности при drag
```

#### 3.4 Добавить `DrawerResizeHandle` в каждый Drawer

В каждом Drawer-компоненте:
1. Подключить `useDrawerResize({ storageKey: '<feature>-drawer' })`
2. Заменить inline `style='min-width: 500px; max-width: 500px'` на `:style='drawerStyle'` + класс `.km-side-drawer`
3. Добавить `<drawer-resize-handle @mousedown='onResizeStart' />` как первый дочерний элемент

**Затронутые компоненты (24 файла):**
`Agents/DrawerAction.vue`, `Agents/DrawerPreview.vue`, `Agents/DrawerTopic.vue`,
`ApiTools/Drawer.vue`, `AssistantTools/Drawer.vue`, `CollectionItems/Drawer.vue`,
`Collections/Drawer.vue`, `Collections/Metadata/Drawer.vue`, `Configuration/Drawer.vue`,
`Conversation/Drawer.vue`, `Conversation/MessageDrawer.vue`, `Dashboard/Drawer/Llm.vue`,
`EvaluationJobs/Drawer.vue`, `EvaluationSets/Drawer.vue`, `Jobs/Drawer.vue`,
`KnowledgeGraph/Playground/RetrievalTestDrawer.vue`, `Mcp/ToolDrawer.vue`,
`ModelProviders/Drawer.vue`, `ModelProviders/ModelDrawer.vue`, `NoteTaker/Drawer.vue`,
`Observability/Traces/Drawer.vue`, `PromptQueue/ExecuteDrawer.vue`,
`Prompts/Drawer.vue`, `Retrieval/Drawer.vue`

#### Примечания

- `KnowledgeGraph/Playground/RetrievalTestDrawer.vue` — уже 420px (chat-интерфейс), нужен особый `minWidth: 360`
- `Agents/DrawerPreview.vue` — уже имеет логику 500↔1000px (при выборе сообщения). Совместить с drag-resize: resize работает поверх, но при выборе сообщения принудительно ставить `1000px` как `defaultWidth`
- Отключить `transition` на `.km-side-drawer` на время перетаскивания (добавлять CSS-класс `.is-resizing` к body)

---

## Этап 4 — Рефакторинг левого меню и layout

### Текущее состояние

**Файлы:**
- `src/components/LayoutDefault.vue` — app shell (q-layout + q-header + q-drawer + q-page-container)
- `src/components/Toolbar.vue` — содержимое левой навигации (секции, пункты меню, Settings, Logout)
- `packages/ui-comp/src/components/base/NavBtn.vue` — пункт меню
- `packages/ui-comp/src/components/base/BtnExpandDown.vue` — раскрывающийся пункт с подпунктами

**Текущая структура header (высота 50px):**
```
┌─────────────────────────────────────────────────────────────────┐
│ [☰] Magnet AI    │   Route Label: [Context Header Buttons]     │
│ (200px, bg-white)│   (flex-grow, bg-primary #6840c2)           │
└─────────────────────────────────────────────────────────────────┘
```

**Текущая структура sidebar (q-drawer):**
```
┌──────────────┐
│ VISUALIZE    │
│   AI Apps    │
│              │
│ CONFIGURE    │
│   Agents     │
│   Prompts... │
│   RAG Tools  │
│   Retrieval  │
│              │
│ CONNECT      │
│   API Tools  │
│   MCP Tools  │
│   Knowledge  │
│   Models     │
│   API Keys   │
│              │
│ Experimental │
│   KG         │
│   Deep Res.  │
│   DR Runs    │
│   Note Taker │
│   Prompt Q.  │
│              │
│ TEST&MONITOR │
│   Evaluations│
│   Usage      │
│   Traces     │
│   Jobs       │
│              │
│ RESOURCES    │
│   Help       │
│              │
│ ─────────── │
│ Settings     │
│ Log out      │
└──────────────┘
```

### Проблемы

#### 4.P1 — «Ступенька» между header и drawer

Header содержит `.col-auto(style='width: 200px')` (строка 6 LayoutDefault.vue) — это белый блок с логотипом и hamburger, который **всегда** рендерится. `q-drawer` ниже тоже `:width='200'`. Но:
- Drawer имеет `bg-primary` (пурпурный фон), а header-секция `bg-white` — визуально разные
- При `show-if-above` и breakpoint 1350px, drawer автоматически скрывается на узком экране, но 200px белый блок в header остаётся → появляется «ступенька» (200px белого пространства без sidebar под ним)

#### 4.P2 — При закрытии sidebar остаётся кнопка на белом фоне

Когда `drawerLeft = false`, `q-drawer` скрывается, но header-секция с hamburger и логотипом (200px, `bg-white`) остаётся видимой. Визуально: кнопка-гамбургер на белом фоне без контекста, а под ней ничего.

#### 4.P3 — Слишком длинное меню, нет collapse секций

20+ пунктов в 6 секциях. Весь список прокручивается с тонким скроллбаром. Секции ("VISUALIZE", "CONFIGURE", "CONNECT", "Experimental", "TEST & MONITOR", "RESOURCES") — статические лейблы, их нельзя свернуть.

#### 4.P4 — Нет icon-only (collapsed) режима

Sidebar либо полностью открыт (200px), либо полностью скрыт. Нет промежуточного состояния «только иконки» (~56px), как в VS Code, GitLab, Grafana и т.д.

#### 4.P5 — Состояние не сохраняется

`drawerLeft: ref(true)` — при каждом обновлении страницы sidebar всегда открывается. Нет persistence.

#### 4.P6 — Hardcoded header routing (lines 29–68)

Массивная цепочка `template(v-if='route.name === "..."')` для каждого Header-компонента. При добавлении новой страницы нужно ручное добавление нового `v-if`. Не масштабируется.

#### 4.P7 — `overflow: scroll` вместо `auto`

В Toolbar.vue `.km-toolbar { overflow: scroll }` — скроллбар виден даже когда контент помещается. Нужно `overflow-y: auto`.

#### 4.P8 — Непоследовательные отступы между секциями

Секции используют разные margins: `q-mt-12`, `q-mt-24`, `q-mt-md` — визуально неоднородно.

---

### Дизайн решения

#### 4.1 Collapsed (icon-only) режим sidebar

**Идея:** вместо полного скрытия, sidebar переключается между двумя состояниями:
- **Expanded:** 220px (чуть шире текущих 200px для лучшего дыхания) — показывает иконку + текст
- **Collapsed:** 56px — показывает только иконку с tooltip на hover

**Composable:** `src/composables/useSidebarState.ts`
```ts
export function useSidebarState() {
  // Инициализация из localStorage, default: 'expanded'
  const mode = ref<'expanded' | 'collapsed'>(
    localStorage.getItem('sidebar-mode') as any || 'expanded'
  )

  function toggle() {
    mode.value = mode.value === 'expanded' ? 'collapsed' : 'expanded'
    localStorage.setItem('sidebar-mode', mode.value)
  }

  const sidebarWidth = computed(() => mode.value === 'expanded' ? 220 : 56)
  const isCollapsed = computed(() => mode.value === 'collapsed')

  return { mode, toggle, sidebarWidth, isCollapsed }
}
```

**Изменения в `LayoutDefault.vue`:**
- `q-drawer(:width='sidebarWidth')` — динамическая ширина
- Header left section: `:style='{ width: sidebarWidth + "px" }'` — синхронизировать с drawer
- Убрать `show-if-above` — drawer всегда видим, просто collapsed/expanded
- При breakpoint < 1350px: автоматически переключать в `collapsed`

**Изменения в `NavBtn.vue`:**
- Добавить проп `collapsed: Boolean`
- Когда `collapsed=true`: скрыть label, увеличить иконку до 18px, добавить `q-tooltip` с label

**Изменения в `BtnExpandDown.vue`:**
- Когда `collapsed=true`: показать только иконку родительского элемента; при клике — показать popup-меню (q-menu) с подпунктами
- Когда `expanded=true`: текущее поведение

#### 4.2 Синхронизация header и sidebar

**Проблема:** header left section (логотип) и drawer — два отдельных элемента с жёсткой шириной.

**Решение:**
- Ширина header left section привязана к `sidebarWidth` через `:style`
- В collapsed-режиме: header left section = 56px, показать только иконку Magnet (без текста "Magnet AI")
- Hamburger-кнопку переместить ниже, в начало sidebar (первый элемент Toolbar) — так header всегда визуально чистый
- Или: заменить hamburger на toggle-кнопку в нижней части sidebar (как в VS Code)

**Header в collapsed-режиме:**
```
┌────────────────────────────────────────────────┐
│ [M]│   Route Label: [Context Header Buttons]   │
│56px│   (flex-grow, bg-primary)                  │
└────────────────────────────────────────────────┘
```

**Header в expanded-режиме:**
```
┌────────────────────────────────────────────────────────┐
│ [M] Magnet AI  [«]│   Route Label: [Context Buttons]  │
│      220px        │   (flex-grow, bg-primary)          │
└────────────────────────────────────────────────────────┘
```

Toggle-кнопка `[«]` / `[»]` — collapse/expand.

#### 4.3 Collapsable секции меню

**Идея:** каждая секция ("VISUALIZE", "CONFIGURE", "CONNECT", etc.) — сворачиваемая группа.

**Компонент:** `KmNavSection` (новый, в ui-comp)
```vue
<!-- Props: label, collapsed (v-model), icon? -->
<!-- Шаблон: -->
<div class="row items-center cursor-pointer" @click="collapsed = !collapsed">
  <span class="km-button-xs-text text-secondary text-uppercase">{{ label }}</span>
  <q-space />
  <q-icon :name="collapsed ? 'expand_more' : 'expand_less'" size="14px" />
</div>
<km-separator />
<slot v-if="!collapsed" />
```

**Persistence:** состояние свёрнутости каждой секции сохраняется в localStorage как JSON:
```ts
const sectionState = useLocalStorage('sidebar-sections', {
  visualize: false,
  configure: false,
  connect: false,
  experimental: false,
  testMonitor: false,
  resources: true, // свёрнуто по умолчанию
})
```

#### 4.4 Рефакторинг header routing

**Проблема:** 20 строк `template(v-if='route.name === "..."')` в LayoutDefault.vue (строки 29–68).

**Решение:** использовать динамический компонент через `meta.headerComponent` в роутере:

```js
// router.js — при определении маршрута:
{
  path: '/agents/:id',
  name: 'AgentDetail',
  component: AgentDetails,
  meta: { pageLabel: 'Agents', headerComponent: 'agents-header' }
}
```

```pug
// LayoutDefault.vue — вместо 20 v-if:
component(v-if='route.meta?.headerComponent', :is='route.meta.headerComponent')
```

Это заменяет всю цепочку if/else одной строкой. При добавлении нового header достаточно указать `meta.headerComponent` в роутере.

#### 4.5 Мелкие UX-улучшения

- **`overflow: scroll` → `overflow-y: auto`** — скроллбар виден только при необходимости
- **Единые отступы** — все секции используют `q-mt-16` (вместо `12`/`24`/`md`)
- **Transition при collapse/expand** — плавная анимация ширины sidebar: `transition: width 0.2s ease`
- **Active route indicator** — тонкая 3px полоска `bg-primary` слева от активного пункта (вместо бледного bg-primary-bg по всему элементу)
- **Persist collapsed sections** — при перезагрузке секции сохраняют своё состояние
- **Keyboard shortcut** — `Ctrl+B` для toggle sidebar (как в VS Code)

---

### Затронутые файлы

| Файл | Изменения |
|---|---|
| `src/components/LayoutDefault.vue` | Динамическая ширина header/drawer, динамический headerComponent, убрать hardcoded routing |
| `src/components/Toolbar.vue` | Collapsable секции через `KmNavSection`, поддержка collapsed-режима, toggle-кнопка |
| `src/composables/useSidebarState.ts` | **Новый** — composable для состояния sidebar |
| `packages/ui-comp/src/components/base/NavBtn.vue` | Проп `collapsed`, tooltip, icon-only режим |
| `packages/ui-comp/src/components/base/BtnExpandDown.vue` | Collapsed-режим: popup-меню вместо expand |
| `packages/ui-comp/src/components/base/NavSection.vue` | **Новый** — collapsable секция меню |
| `src/router.js` | Добавить `meta.headerComponent` к каждому route |
| `packages/themes/src/base/app.styl` | Стили sidebar transition, active indicator |

---

## Этап 5 — Унификация правых Drawer-панелей

### Текущее состояние

Анализ 23 Drawer-компонентов выявил 4 разных паттерна контейнера и множество несогласованностей.

### Проблемы

#### 5.P1 — Hardcoded фиксированная ширина (сломан resize)

Два drawer'а до сих пор содержат `style='min-width: 500px; max-width: 500px'` **без** `km-side-drawer` / `drawerStyle`:
- `Conversation/Drawer.vue`
- `ModelProviders/ModelDrawer.vue`

При drag-resize их ширина не меняется.

#### 5.P2 — Несогласованные отступы (padding)

| Паттерн | Файлы |
|---|---|
| `q-pa-16` на root | AssistantTools, CollectionItems, Collections, Collections/Metadata, Configuration, EvaluationJobs, EvaluationSets, Jobs, Prompts, Retrieval, PromptQueue |
| `q-pt-16` + `q-px-16` фрагментарно | ApiTools, Conversation/Drawer, Conversation/MessageDrawer, Dashboard/Llm, Mcp/ToolDrawer |
| `q-py-16` + `q-pl-16.q-pr-8` | Agents/DrawerPreview |
| `q-py-16.q-pl-16.q-pr-xs` (ассиметричный) | Observability/Traces |
| Без стандартных q-отступов (CSS) | KnowledgeGraph/RetrievalTestDrawer |

#### 5.P3 — Несогласованные заголовки

| Паттерн | Файлы |
|---|---|
| `.km-heading-7` + `q-separator` | AssistantTools, Collections, Configuration, EvaluationJobs, EvaluationSets, Jobs, Prompts, Retrieval, PromptQueue |
| `.km-heading-4` + back-button | CollectionItems, Collections/Metadata, Agents/DrawerTopic |
| Tabs вместо заголовка | ApiTools, Conversation, Dashboard/Llm, Mcp/ToolDrawer, ModelProviders/ModelDrawer |
| Кастомный layout | Agents/DrawerPreview, Observability/Traces, KnowledgeGraph |

#### 5.P4 — Несогласованная прокрутка

| Подход | Файлы |
|---|---|
| `q-scroll-area.fit` | ApiTools, CollectionItems, Configuration, Collections, Dashboard/Llm, EvaluationJobs, Jobs, Mcp, Retrieval |
| `q-scroll-area.full-height.col` | Collections, Retrieval |
| Inline `overflow-y: auto; max-height: calc(100vh - Xpx)` | AssistantTools, Agents/DrawerAction, Agents/DrawerPreview |
| Custom CSS scrolling | KnowledgeGraph/RetrievalTestDrawer |
| Нет прокрутки | EvaluationSets, Collections/Metadata, ModelProviders/Drawer |

#### 5.P5 — Кнопка закрытия

Только 4 из 23 drawer'ов имеют кнопку закрытия, и они все разные:
- `Dashboard/Llm.vue` — в tab bar справа
- `PromptQueue/ExecuteDrawer.vue` — рядом с заголовком
- `KnowledgeGraph/RetrievalTestDrawer.vue` — рядом с заголовком (HTML)
- `Agents/DrawerPreview.vue` — в header area

#### 5.P6 — KnowledgeGraph/RetrievalTestDrawer.vue

Полностью выбивается из системы: написан в HTML (не Pug), свои CSS классы (`message-bubble`, `user-bubble`, `assistant-bubble`), кастомный скроллбар, нет `bl-border`, нет `bg-white`.

---

### Дизайн решения

#### 5.1 Создать компонент `KmDrawerLayout`

**Файл:** `packages/ui-comp/src/components/base/DrawerLayout.vue`

Обёртка-контейнер, стандартизирующая структуру всех drawer'ов:

```pug
//- Стандартная структура:
.km-drawer-layout.column.no-wrap.bg-white.bl-border.full-height.km-side-drawer(:style='drawerStyle')
  km-drawer-resize-handle(@mousedown='onResizeStart')
  //- Header slot (title, back button, close button)
  .km-drawer-header.q-px-16.q-pt-16(v-if='$slots.header')
    slot(name='header')
    q-separator.q-mt-12
  //- Tabs slot (alternative to header)
  .km-drawer-tabs(v-if='$slots.tabs')
    slot(name='tabs')
  //- Content slot (scrollable)
  q-scroll-area.col.q-px-16.q-py-16
    slot
```

**Props:**
- `storageKey: string` — ключ для useDrawerResize
- `defaultWidth?: number` (default: 500)
- `minWidth?: number` (default: 320)
- `maxWidth?: number` (default: 900)
- `noScroll?: boolean` — отключить q-scroll-area для маленьких форм

Composable `useDrawerResize` вызывается внутри компонента, drawer'ам не нужно его импортировать.

#### 5.2 Подключить `KmDrawerLayout` к Drawer'ам

Для каждого drawer'а: обернуть содержимое в `km-drawer-layout` с нужными слотами.

**Пример миграции (до):**
```pug
.column.no-wrap.q-pa-16.bg-white.fit.bl-border.height-100.km-side-drawer(:style='drawerStyle')
  km-drawer-resize-handle(@mousedown='onResizeStart')
  .km-heading-7.q-mb-xs Record details
  q-separator.q-mb-md
  q-scroll-area.fit
    //- content
```

**После:**
```pug
km-drawer-layout(storageKey='drawer-evaluation-jobs')
  template(#header)
    .km-heading-7 Record details
  //- content (уже внутри q-scroll-area)
```

**Группы drawer'ов по типу миграции:**

**Группа A — Простые drawer'ы с заголовком (11 файлов):**
AssistantTools, CollectionItems, Collections, Collections/Metadata, Configuration, EvaluationJobs, EvaluationSets, Jobs, Prompts, Retrieval, PromptQueue/ExecuteDrawer

**Группа B — Drawer'ы с tabs вместо заголовка (5 файлов):**
ApiTools, Conversation/Drawer, Dashboard/Llm, Mcp/ToolDrawer, ModelProviders/ModelDrawer

**Группа C — Сложные drawer'ы (остальные 7 файлов):**
Agents/DrawerAction, Agents/DrawerPreview, Agents/DrawerTopic, Conversation/MessageDrawer, ModelProviders/Drawer, Observability/Traces, KnowledgeGraph/RetrievalTestDrawer
— требуют индивидуальной адаптации, но root-контейнер всё равно стандартизируется через `km-drawer-layout`

#### 5.3 Исправить сломанные drawer'ы

- `Conversation/Drawer.vue` — заменить hardcoded ширину на `km-side-drawer` + `drawerStyle`
- `ModelProviders/ModelDrawer.vue` — то же

#### 5.4 Стандартизировать мелочи

- **Все padding:** `q-px-16.q-py-16` на content area (через `km-drawer-layout`)
- **Все заголовки:** `.km-heading-7` + `q-separator.q-mt-12` (через slot `#header`)
- **Все scroll:** `q-scroll-area.col` (через `km-drawer-layout`)
- **Border:** `bl-border` на root (через `km-drawer-layout`)
- **Background:** `bg-white` на root (через `km-drawer-layout`)

---

### Затронутые файлы

| Файл | Изменения |
|---|---|
| `packages/ui-comp/src/components/base/DrawerLayout.vue` | **Новый** — layout-обёртка для drawer |
| 23 Drawer-компонента | Миграция на `km-drawer-layout`, удаление дублирующихся классов/стилей |
| `Conversation/Drawer.vue` | Дополнительно: исправить hardcoded ширину |
| `ModelProviders/ModelDrawer.vue` | Дополнительно: исправить hardcoded ширину |

---

## Порядок выполнения

| # | Этап | Задача | Сложность | Приоритет |
|---|---|---|---|---|
| 1 | 1 | ~~Удалить мёртвый wobble CSS (19 файлов)~~ | Низкая | ✅ Готово |
| 2 | 1 | ~~Удалить дублированный `formatDate()`~~ | Низкая | ✅ Готово |
| 3 | 1 | ~~Удалить мёртвые методы delete из details.vue~~ | Низкая | ✅ Готово |
| 4 | 3 | ~~Создать `useDrawerResize` composable~~ | Средняя | ✅ Готово |
| 5 | 3 | ~~Создать `DrawerResizeHandle` компонент~~ | Низкая | ✅ Готово |
| 6 | 3 | ~~Подключить resize во все 23 Drawer~~ | Средняя | ✅ Готово |
| 7 | 3 | ~~Унифицировать ширину Drawer через `.km-side-drawer`~~ | Низкая | ✅ Готово |
| 8 | 2 | ~~Мигрировать detail-страницы на `DetailsLayout`~~ | Высокая | ✅ Готово |
| 9 | 2 | ~~Извлечь `q-tabs` в `km-tabs`~~ | Средняя | ✅ Готово |
| 10 | 2 | ~~Унифицировать `km-inner-loading`~~ | Средняя | ✅ Готово |
| 11 | 2 | Унифицировать `km-empty-state` | Средняя | Пропущено |
| 12 | 4 | ~~Создать `useSidebarState` composable~~ | Средняя | ✅ Готово |
| 13 | 4 | ~~Collapsed (icon-only) режим sidebar~~ | Высокая | ✅ Готово |
| 14 | 4 | ~~Синхронизация ширины header ↔ sidebar~~ | Средняя | ✅ Готово |
| 15 | 4 | ~~Collapsable секции меню (`KmNavSection`)~~ | Средняя | ✅ Готово |
| 16 | 4 | ~~Рефакторинг header routing → `meta.headerComponent`~~ | Средняя | ✅ Готово |
| 17 | 4 | ~~UX мелочи: overflow-y auto, единые отступы, toggle в header~~ | Низкая | ✅ Готово |
| 18 | 5 | Создать `KmDrawerLayout` компонент | Средняя | Высокий |
| 19 | 5 | Исправить hardcoded ширину (Conversation, ModelProviders/Model) | Низкая | Высокий |
| 20 | 5 | Мигрировать Группу A (11 простых drawer) на `KmDrawerLayout` | Средняя | Высокий |
| 21 | 5 | Мигрировать Группу B (5 drawer с tabs) на `KmDrawerLayout` | Средняя | Средний |
| 22 | 5 | Мигрировать Группу C (7 сложных drawer) на `KmDrawerLayout` | Высокая | Средний |
