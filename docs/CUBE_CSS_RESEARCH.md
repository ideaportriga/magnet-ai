# CUBE CSS Research For Magnet UI

Дата: 2026-04-27

Scope: `web/packages/ds`, `web/packages/themes`, `web/packages/ui-comp`, `web/apps/@ipr/magnet-admin`, Reka UI primitives и CUBE CSS слой дизайн-системы.

Цель: зафиксировать либеральный, практичный CUBE CSS подход для Magnet UI: консистентная дизайн-система, разные темы, узнаваемый визуальный стиль, нормальная интеграция с headless-компонентами и управляемая анимация.

## Короткий Вывод

CUBE CSS полезен не как жесткая методология именования, а как способ распределить ответственность:

- CSS и токены задают системные значения и наследование.
- Composition задает макро-раскладку и ритм без знания о конкретном компоненте.
- Utilities дают маленькие одноцелевые помощники, привязанные к токенам.
- Blocks задают узнаваемую оболочку компонента или продуктового паттерна.
- Exceptions описывают состояние и варианты через `data-*`, что хорошо совпадает с Reka UI.

Для Magnet лучше применять CUBE либерально: не требовать квадратных скобок в `class`, не запрещать scoped CSS, не превращать все в utilities. Важнее, чтобы каждый стиль попадал в правильный слой и не ломал тематизацию.

## Что Такое CUBE CSS

CUBE расшифровывается как Composition, Utility, Block, Exception. Методология исходит из того, что CSS уже имеет каскад, наследование и прогрессивное улучшение. В отличие от подходов, где почти все поведение запирается внутри компонента или utility-класса, CUBE предлагает сначала использовать сильные стороны CSS, а потом добавлять локальную специфичность только там, где это действительно нужно.

Главные идеи из первоисточников:

- Простота важнее полного контроля над каждым пикселем.
- Браузеру стоит давать гибкие правила, а не микроменеджить все layout-сценарии.
- Абстракции добавляются только когда они уменьшают повторение или проясняют намерение.
- Utilities работают лучше всего, когда они генерируются или явно связаны с design tokens.
- Blocks должны быть небольшими. Если CSS блока разрастается, скорее всего там смешаны несколько ответственностей.
- Exceptions лучше выражать через `data-*`, особенно если состояние приходит из JS или headless-библиотеки.

Для composition слоя первичный практический источник — Every Layout от Andy Bell и Heydon Pickering. CUBE отвечает на вопрос "в каком CSS-слое живет правило", а Every Layout отвечает на вопрос "каким алгоритмом браузер должен сам разложить боксы". В Magnet эти идеи идут вместе: composition primitives должны быть маленькими, контекстно-устойчивыми и построенными на browser algorithms, а не на локальных magic numbers.

## Либеральная Версия Для Magnet

Для проекта не нужен догматичный CUBE. Нужен контракт, который помогает не расползтись стилям.

### 1. Слой Определяет Ответственность

Практическое правило:

```text
Tokens
  -> Composition
    -> Utilities
      -> Blocks: Ds*, Km*, product patterns
        -> Exceptions: data-state, data-variant, data-tone, data-size
          -> One-off screen CSS only when it cannot be generalized yet
```

Если стиль отвечает на вопрос "какое системное значение использовать", он должен быть token.
Если стиль отвечает на вопрос "как эти элементы располагаются рядом", он должен быть composition.
Если стиль задает одну повторяемую мелочь, он может быть utility.
Если стиль делает компонент узнаваемым, он block.
Если стиль меняет компонент по состоянию или варианту, он exception через `data-*`.

### 2. Не Запрещать Scoped CSS

Vue SFC scoped CSS нормален для block-стилей компонента. Запрещать его не нужно. Ограничение другое: scoped CSS не должен лезть во внутренности чужого DS-компонента через `:deep()` без публичного part/class/variable контракта.

Допустимо:

```css
.kg-source-card {
  display: grid;
  gap: var(--ds-space-sm);
  padding: var(--ds-space-lg);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-lg);
}

.kg-source-card[data-state='selected'] {
  border-color: var(--ds-color-primary);
  background: var(--ds-color-primary-bg);
}
```

Нежелательно:

```css
.some-page :deep(.ds-select__content > div > span:first-child) {
  margin-left: 7px;
}
```

Если такое нужно двум экранам, это уже DS part, prop, variant или CSS variable.

### 3. Class Grouping Без Ритуалов

Официальный CUBE предлагает группировать классы, например `[ card ] [ stack ] [ bg-primary ]`. В Vue-шаблонах это может ухудшать читаемость и tooling. Для Magnet достаточно стабильного порядка:

```html
<section class="kg-panel stack p-lg bg-white shadow-sm" data-gap="md" data-state="open">
  ...
</section>
```

Порядок классов:

1. Основной block или product pattern class.
2. Composition class: `stack`, `cluster`, `sidebar`, `switcher`, `flow`, `frame`, `center`.
3. Token utilities: spacing, color, typography, radius, shadow.
4. Narrow helpers: overflow, cursor, min-width fixes.

Exceptions не добавлять классами вроде `is-open`, `selected`, `primary-card`. Использовать `data-state`, `data-tone`, `data-variant`, `data-size`, `data-display`, `data-shape`.

## Tokens И Темы

В Magnet уже есть сильная база: `--ds-*` tokens, `data-theme='light|dark'`, brand themes через `@themes`, component tokens, motion tokens. Чтобы разные темы не ломали узнаваемость, токены стоит разделять по уровням.

### Уровень 1. Base Tokens

Редко используются напрямую в компонентах. Это шкалы:

- `--ds-space-*`
- `--ds-font-size-*`
- `--ds-font-weight-*`
- `--ds-radius-*`
- `--ds-shadow-*`
- `--ds-duration-*`
- `--ds-ease-*`
- raw palette values, если появится отдельный palette-файл

### Уровень 2. Semantic Tokens

Их используют почти все компоненты:

- `--ds-color-background`
- `--ds-color-surface`
- `--ds-color-text-primary`
- `--ds-color-text-muted`
- `--ds-color-border`
- `--ds-color-primary`
- `--ds-color-primary-bg`
- `--ds-color-success-*`, `warning`, `danger`, `info`

Семантические токены должны сохранять значение между темами. Например, `surface` всегда поверхность, даже если в dark mode она темная.

### Уровень 3. Component Tokens

Там, где компонент имеет устойчивую геометрию или behavior:

- `--ds-btn-height-md`
- `--ds-field-height`
- `--ds-dialog-width-md`
- `--ds-table-row-height`
- `--ds-transition-colors` после добавления motion presets

Компонентные токены должны быть ограниченным списком. Если каждый экран добавляет новый component token, это уже не дизайн-система.

### Уровень 4. Brand Signature Tokens

Это слой узнаваемости. Он не должен превращаться в произвольные цвета на местах. Лучше иметь маленький набор signature-переменных:

- `--ds-brand-accent`
- `--ds-brand-accent-soft`
- `--ds-brand-focus-ring`
- `--ds-brand-selection-bg`
- `--ds-brand-gradient` только если он действительно часть стиля
- `--ds-brand-motion-emphasis` или preset для выразительных переходов

Так можно делать `default`, `siebel`, `salesforce`, dark/light и будущие темы без переписывания компонентного CSS.

## Composition Best Practices

Composition слой должен решать layout без декоративного оформления.

Хорошие composition primitives для Magnet:

- `stack`: вертикальная последовательность, формы, body dialog, sections.
- `cluster`: toolbar, action row, chips, header controls, button groups.
- `sidebar`: aside + content, detail page with secondary panel.
- `switcher`: responsive blocks that become columns when possible and stack when narrow.
- `flow`: rich text, markdown, long-form descriptions.
- `frame`: media/aspect-ratio containers.
- `center`: constrained centered content.

Composition не должен задавать цвет, border, shadow, font weight. Если это нужно, добавлять block или utility.

### Every Layout Правила Для Composition

Every Layout формулирует layout как arrangement of boxes. Практические правила для Magnet:

- Стиль задается контексту, а не отдельному элементу. Вертикальный ритм делает общий родитель (`stack > * + *`), а не `margin-bottom` у каждого ребенка.
- Spacing между соседями принадлежит relationship, поэтому для последовательностей использовать `stack`/`flow`, для горизонтальных групп `cluster`/`gap`, для divider rhythm — margin utilities на самом divider, а не пустые spacer nodes.
- Размеры должны быть suggestions, not dictates: предпочитать `flex-basis`, `min-inline-size`, `max-inline-size`, `aspect-ratio`, `gap`, `ch`, logical properties. Жесткие `width/height`, viewport breakpoints and magic pixels — только если формат действительно fixed.
- Браузер должен принимать решения по available space. Для responsive layouts сначала пробовать `sidebar` или `switcher` вместо viewport media queries.
- Вложенные ритмы делаются nested primitives with smaller `data-gap`, а не локальными block-классами вроде `some-component__section-gap`.
- `stack` использовать для semantically distinct blocks. `flow` использовать для rich text, markdown, paragraph/list rhythm.
- `cluster` использовать для элементов, которые ведут себя как строка слов: wrapping by available space is allowed. Для toolbar, который не должен переноситься, явно ставить `data-wrap="no"`.
- `sidebar` использовать для two-part layouts, где одна часть имеет intrinsic/fixed target width, а main забирает остальное и wraps when content space is insufficient.
- `switcher` использовать для равноправных siblings, которые должны переключаться сразу между one-row и one-column, без случайных промежуточных строк.
- Exceptions внутри layout выражать через `data-*` или существующие token utilities. Если нужно больше двух-трех однотипных exceptions, это признак недостающего product pattern или DS primitive option.

Анти-паттерны:

- Пустые `<div class="mt-md" />` как layout API.
- Одновременное использование `stack data-gap`, `mt-*`, default component margins and `py-*` без явного расчета итогового rhythm.
- Локальные scoped CSS classes, единственная цель которых — повторить `.mt-sm`, `.pt-md`, `gap`, `flex` или `min-h-0`.
- Viewport breakpoint только потому, что компоненту тесно в конкретном скриншоте. Сначала проверить container/intrinsic layout primitive.

Пример:

```html
<form class="km-form stack" data-gap="lg">
  <div class="cluster" data-gap="sm" data-align="center" data-justify="between">
    <h2 class="km-heading-7">Settings</h2>
    <KmBtn variant="secondary" icon="save" />
  </div>
  <KmInput display="text-field" />
</form>
```

## Utility Best Practices

Utilities должны быть маленькими, предсказуемыми и token-driven.

Подходящие utilities:

- spacing: `.p-md`, `.mt-lg`, `.gap-sm`
- color: `.text-primary`, `.bg-white`, если они семантически стабильны
- typography: `.km-body`, `.km-caption`, `.font-medium`, если naming согласован
- radius/shadow: `.radius-md`, `.shadow-sm`
- technical helpers: `.min-w-0`, `.overflow-hidden`, `.cursor-pointer`

Неподходящие utilities:

- `.pretty-card-blue-large`
- `.primary-status-chip`
- utilities, которые задают цвет, размер, padding, border и shadow сразу
- `!important` как обычный способ выиграть specificity

Если utility регулярно используется как компонент, ему нужен block или domain component.

## Blocks Для DS, Domain И Product Patterns

Block в Magnet может быть трех типов:

- Primitive block: `.ds-button`, `.ds-select`, `.ds-dialog__content`.
- Domain block: `.km-data-table`, `.km-chip`, `.km-filter-bar`.
- Product pattern block: `.kg-field-row`, `.workspace-tab-bar`, `.collection-container`.

Block не обязан быть BEM-строгим, но должен иметь ясную границу. Внутри block можно использовать BEM-like part classes, если это помогает публичному styling contract.

Хороший block:

```css
.ds-menu-item {
  display: flex;
  align-items: center;
  gap: var(--ds-space-sm);
  min-block-size: var(--ds-menu-item-height, 32px);
  color: var(--ds-color-text-primary);
}

.ds-menu-item[data-highlighted] {
  background: var(--ds-color-accent-bg);
  color: var(--ds-color-accent);
}
```

Плохой block:

```css
.some-page .ds-menu-item span:first-child svg path {
  fill: purple;
}
```

## Exceptions И `data-*`

CUBE exceptions идеально совпадают с Reka UI, потому что Reka уже отдает состояния через attributes:

- `data-state='open|closed|checked|unchecked|active|inactive'`
- `data-disabled`
- `data-highlighted`
- `data-side`, `data-align` для overlay позиционирования

Magnet DS уже использует похожий подход:

- `data-variant`
- `data-size`
- `data-tone`
- `data-display`
- `data-shape`

Рекомендация: сделать `data-*` официальным языком состояния и вариантов. Новые визуальные API должны мапиться в закрытые `data-*`, а не в произвольные классы и цвета.

## Интеграция С Reka UI

Reka UI дает поведение, доступность и state attributes, но стили полностью принадлежат проекту. Это хорошо для CUBE: Reka закрывает сложную интерактивность, CUBE закрывает визуальный контракт.

### Functional Styles Обязательны

Headless-компоненты не гарантируют layout overlay. Например, Dialog Overlay сам по себе не обязан покрывать viewport. DS wrapper должен задавать functional styles:

- overlay fixed inset
- z-index через `--ds-z-*`
- popover/menu width constraints
- focus ring
- scroll locking expectations
- collision-safe max sizes

Это должно жить в DS primitive, а не в каждом экране.

### Portal Styling

Reka portal часто рендерит content в `body`. Поэтому DS overlay/menu/popover styles лучше держать в самих primitive components или в глобальном DS style module. Не полагаться на scoped parent selectors.

Правило: portaled part получает стабильный class:

```html
<PopoverContent class="ds-popover__content">
```

А styling идет по этому class и `data-state`, `data-side`, `data-align`.

### `asChild` Для Триггеров

Reka `asChild` полезен, когда trigger должен быть вашим `DsButton` или `KmBtn`. Это лучше, чем вкладывать button в button.

```html
<DsDropdownMenuTrigger as-child>
  <DsButton variant="ghost" size="icon" aria-label="Open actions">
    <KmGlyph name="more_vert" />
  </DsButton>
</DsDropdownMenuTrigger>
```

Если меняется underlying element, нужно сохранять доступность: focusable element, keyboard events, correct role.

## Animation И Motion

Анимация должна быть частью дизайн-системы, а не локальным набором `0.15s ease`.

### Базовый Контракт

- Не использовать `transition: all` в новом коде.
- Использовать только tokenized duration/ease.
- Для hover/focus чаще всего `--ds-duration-fast` + `--ds-ease-out`.
- Для layout/resize `--ds-duration-base` или `--ds-duration-slow`.
- Для overlay enter `--ds-ease-out`, для exit `--ds-ease-in`.
- Всегда уважать `prefers-reduced-motion`.

Полезные presets:

```css
:root {
  --ds-transition-colors:
    color var(--ds-duration-fast) var(--ds-ease-out),
    background-color var(--ds-duration-fast) var(--ds-ease-out),
    border-color var(--ds-duration-fast) var(--ds-ease-out);
  --ds-transition-opacity: opacity var(--ds-duration-fast) var(--ds-ease-out);
  --ds-transition-transform: transform var(--ds-duration-base) var(--ds-ease-out);
  --ds-transition-shadow: box-shadow var(--ds-duration-fast) var(--ds-ease-out);
}
```

### Reka Enter/Exit

Reka может задерживать unmount на CSS animation, если content получает `data-state='closed'`. Для overlay primitives это самый простой путь:

```css
.ds-dialog__overlay[data-state='open'] {
  animation: ds-fade-in var(--ds-duration-base) var(--ds-ease-out);
}

.ds-dialog__overlay[data-state='closed'] {
  animation: ds-fade-out var(--ds-duration-fast) var(--ds-ease-in);
}
```

Для JS animation libraries использовать `forceMount` только там, где CSS не хватает: drag, spring, complex presence, chart motion.

### Keyframes

Повторяемые keyframes должны жить в DS/theme motion module, а не копироваться по экранам. Локальные keyframes допустимы только для узкого продуктового эффекта, который не повторяется.

## Cascade Layers

В проекте пока нет `@layer`. Это не критичная проблема, но для CUBE layers они могут быть полезны как следующий шаг:

```css
@layer ds.reset, ds.tokens, ds.composition, ds.utilities, ds.components, ds.patterns, app;
```

Потенциальная польза:

- utilities не обязаны повышать specificity;
- app-level exceptions могут быть явно выше DS base;
- легче объяснить порядок каскада новым разработчикам;
- проще убрать legacy utilities без неожиданного выигрыша specificity.

Осторожность: Vue scoped styles и Vite CSS order нужно проверить в отдельном spike. Не стоит внедрять `@layer` массово без snapshot/visual check.

## Узнаваемый Стиль Без Хаоса

Узнаваемость должна приходить не из произвольных локальных цветов, а из системных решений:

- стабильная плотность интерфейса;
- фирменный focus/selection/highlight;
- согласованная форма controls;
- узнаваемые menu/overlay transitions;
- один language для chips/badges/status;
- аккуратная typographic scale;
- локальные fonts/icons под контролем темы;
- цветовые темы, которые переопределяют semantic tokens, а не component CSS.

## Checklist Для Нового UI

Перед добавлением нового component/screen CSS:

- Можно ли решить layout через `stack`, `cluster`, `sidebar`, `switcher`, `flow`, `frame`?
- Следует ли spacing из relationship between siblings (`stack`, `flow`, `cluster gap`), а не из margin на отдельных child components?
- Есть ли hardcoded width/height/breakpoint, который можно заменить на suggestion: `flex-basis`, `min/max-inline-size`, `aspect-ratio`, `ch`, or tokenized gap?
- Есть ли уже `Ds*` или стабильный `Km*` component?
- Используются ли только `--ds-*` tokens?
- Вариант выражен через `variant`, `display`, `tone`, `shape`, `size`, а не через arbitrary color props?
- Состояния выражены через `data-*`?
- Portaled Reka parts имеют стабильные classes?
- Нет `transition: all`, hardcoded `0.15s ease`, локально скопированных keyframes?
- Нет `:deep()` в чужие internals?
- Есть ли пример в UI gallery или другой visual reference?

## Источники

- CUBE CSS overview: https://cube.fyi/
- CUBE CSS principles: https://cube.fyi/principles.html
- CUBE CSS CSS layer: https://cube.fyi/css.html
- CUBE CSS composition: https://cube.fyi/composition.html
- CUBE CSS utility: https://cube.fyi/utility.html
- CUBE CSS block: https://cube.fyi/block.html
- CUBE CSS exception: https://cube.fyi/exception.html
- CUBE CSS grouping: https://cube.fyi/grouping.html
- Every Layout overview: https://every-layout.dev/
- Every Layout boxes: https://every-layout.dev/rudiments/boxes/
- Every Layout axioms: https://every-layout.dev/rudiments/axioms/
- Every Layout stack: https://every-layout.dev/layouts/stack/
- Every Layout sidebar: https://every-layout.dev/layouts/sidebar/
- Every Layout switcher: https://every-layout.dev/layouts/switcher/
- Reka UI styling guide: https://reka-ui.com/docs/guides/styling
- Reka UI animation guide: https://reka-ui.com/docs/guides/animation
- Reka UI composition guide: https://reka-ui.com/docs/guides/composition
