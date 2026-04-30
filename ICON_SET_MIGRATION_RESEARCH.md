# Icon Set Migration Research: Phosphor vs Lucide

Date: 2026-04-28

## Goal

Check whether the current frontend icon usage can be moved to one consistent icon set, and compare two candidates:

- Phosphor Icons via `@phosphor-icons/vue`
- Lucide via `lucide-vue-next`

This research focuses on functional UI glyphs currently rendered through `KmGlyph`, `KmBtn icon`, `KmIconBtn icon`, `icon-before`, `icon-after`, FontAwesome class strings, Material icon ligatures, and `KmIcon` / `svgIcon` sprite paths.

## Methodology

- Scanned Vue/TS/JS sources under `web/apps` and `web/packages`.
- Counted static literal icon names only.
- Excluded dynamic bindings such as `:icon="item.icon"` and `:name="sample.name"` from coverage counts.
- Inspected the installed `@phosphor-icons/vue` package in the workspace.
- Inspected `lucide-vue-next@latest` from a temporary npm tarball without changing workspace dependencies.
- Validated a representative crosswalk of current icon concepts against actual component exports in both packages.

## Current Inventory

| Metric | Count |
| --- | ---: |
| Files scanned | 1113 |
| Static literal icon usages | 940 |
| Unique static literal icon names | 248 |
| FontAwesome-style usages | 320 |
| Material/canonical-name usages | 596 |
| SVG sprite usages | 19 |
| Other literal usages | 5 |

Most common static icon names:

| Current name | Usages | Notes |
| --- | ---: | --- |
| `search` | 66 | Search inputs and prompts |
| `close` | 36 | Close buttons |
| `o_info` | 29 | Outlined Material info |
| `info` | 24 | Info/action metadata |
| `open_in_new` | 24 | External-link affordance |
| `delete` | 22 | Delete action |
| `copy` | 19 | Already moved to canonical action name |
| `chevron_right` | 18 | Navigation/expand affordance |
| `fas fa-comment-dots` | 18 | Chat/message action |
| `far fa-save` | 17 | Save action |
| `fas fa-ellipsis-v` | 16 | More menu |
| `refresh` | 15 | Refresh/retry |
| `add` | 14 | Add action |
| `fas fa-paper-plane` | 14 | Send action |
| `fas fa-undo` | 14 | Undo/back action |

The current system effectively has four icon paths:

| Path | Current role | Migration note |
| --- | --- | --- |
| Material ligatures | Common simple names such as `search`, `close`, `delete` | Good target for canonical DS aliases. |
| FontAwesome classes | Many action/status/source icons such as `fas fa-comment-dots`, `far fa-save`, `fas fa-paper-plane` | Replace or map through compatibility aliases. |
| SVG sprite via `KmIcon` / `svgIcon` | Brand, theme, emoji, source-specific, and old action icons | Keep only brand/illustration assets. |
| Dynamic icon props | Menus, dashboards, source cards | Need registry-backed canonical names because static rewrite cannot see every value. |

## SVG Sprite Findings

The current sprite loader is `web/packages/themes/src/utils/loadIcons.js`. It imports:

- `web/packages/themes/src/base/assets/svg/*.svg`
- `web/packages/themes/src/themes/siebel/svg/*.svg`
- `web/packages/themes/src/themes/salesforce/svg/*.svg`

Base sprite assets currently include:

`cloud`, `copy`, `dislike`, `dislike-emoji`, `empty-collection`, `folder`, `like`, `like-emoji`, `magnet`, `magnet-msg`, `neutral-emoji`, `send`.

Theme sprite assets include functional/source icons such as:

`ai`, `arrow`, `attach`, `attach_file`, `book`, `calendar`, `copy`, `dislike`, `edit`, `email`, `exchange_h`, `file`, `like`, `pdf`, `reload`, `robot`, `settings`, `user`, `video-file`.

Conclusion for sprites:

- Functional sprite icons such as `copy`, `like`, `dislike`, `send`, `edit`, `calendar`, `pdf`, `user`, `settings`, `robot`, `attach_file`, `reload`, and `video-file` can be replaced by either Phosphor or Lucide.
- Product/illustration assets such as `magnet`, `magnet-msg`, `empty-collection`, and emoji feedback art (`like-emoji`, `neutral-emoji`, `dislike-emoji`) should remain custom SVG assets unless the product intentionally changes their visual language.
- `KmIcon` should remain only for brand/illustration assets. Common actions should go through the DS glyph path.

## Candidate Package Status

| Candidate | Package | Current status | Observed exports |
| --- | --- | --- | ---: |
| Phosphor | `@phosphor-icons/vue` | Installed in `web/package.json` | 1530 `Ph*` Vue components |
| Lucide | `lucide-vue-next` | Not installed; inspected from temporary npm tarball | 3896 base component export names, including aliases/deprecated names |

Lucide's export count includes many aliases, but practical UI coverage is still broad.

## Coverage Summary

### Phosphor

Verdict: Phosphor can replace all functional UI icons found in the inventory.

Phosphor has direct or close equivalents for the current Material and FontAwesome concepts. The only cases that should not be forced into Phosphor are product/illustration sprites.

Strong matches:

- Actions: copy, edit, delete, save, upload, download, send, undo, refresh, add, close
- Navigation: chevrons/carets, first/last page, external link, expand/collapse
- Feedback/status: info, warning, error, check, thumbs up/down
- Data/source: file, file text, file PDF, video, folder, database, tag, key, lock
- AI/chat: robot, brain, chat/message, magic wand, sparkles
- Misc UI: menu dots, filter/tune/settings, visibility, calendar, clock, paperclip, list/table

Known notes:

- `fas fa-server` has no exact `PhServer`; use `PhDatabase`, `PhStack`, or `PhNetwork` depending on context.
- `timeline` has no exact `PhTimeline`; use `PhChartLine`, `PhTreeStructure`, or `PhGitBranch` depending on context.
- Phosphor offers weights (`thin`, `light`, `regular`, `bold`, `fill`, `duotone`), which is useful for active/selected states without switching icon families.

Recommended Phosphor migration shape:

1. Keep `KmGlyph` as the single DS glyph renderer.
2. Grow a canonical DS alias map in `phosphorIcons.ts`.
3. Rewrite feature code from legacy names to canonical names, for example `fas fa-paper-plane` -> `send`, `open_in_new` -> `external-link`, `o_info` -> `info`.
4. Keep FontAwesome and Material names as fallback aliases during migration, but block new usages with an audit once the rewrite is mostly complete.

### Lucide

Verdict: Lucide can also replace the functional UI icon inventory.

Lucide has direct or very close equivalents for the same functional set. It is especially strong for application UI actions, navigation, status, file/source icons, and common dashboard controls.

Strong matches:

- Actions: `Copy`, `Pencil`, `Trash2`, `Save`, `Upload`, `Download`, `Send`, `Undo2`, `RefreshCw`, `Plus`, `X`
- Navigation: `ChevronRight`, `ChevronLeft`, `ChevronDown`, `ChevronsLeft`, `ChevronsRight`, `ExternalLink`
- Feedback/status: `Info`, `TriangleAlert`, `CircleAlert`, `CircleCheck`, `ThumbsUp`, `ThumbsDown`
- Data/source: `File`, `FileText`, `Video`, `Folder`, `FolderOpen`, `Database`, `Tag`, `Key`, `Lock`
- AI/chat: `Bot`, `Brain`, `MessageCircleMore`, `WandSparkles`, `Sparkles`
- Misc UI: `EllipsisVertical`, `ListFilter`, `SlidersHorizontal`, `Eye`, `Calendar`, `Clock`, `Paperclip`, `Columns3`

Known notes:

- Lucide has a stricter 24px outline look. That is good for consistency, but less flexible than Phosphor if the UI needs filled/duotone/active states from the same package.
- Lucide does not solve brand/illustration sprites either. `magnet`, `magnet-msg`, `empty-collection`, and emoji art still need custom SVGs.
- Moving to Lucide now would require adding `lucide-vue-next` and replacing the newly introduced Phosphor registry with a Lucide registry.

## Validated Crosswalk

The following high-frequency concepts were checked against real package exports.

| Current concept/name family | Phosphor candidate | Lucide candidate | Result |
| --- | --- | --- | --- |
| `search`, `fas fa-search` | `PhMagnifyingGlass` | `Search` | Both available |
| `close`, `fas fa-times`, `fa fa-xmark` | `PhX` | `X` | Both available |
| `info`, `o_info`, `fas fa-circle-info` | `PhInfo` | `Info` | Both available |
| `open_in_new`, external link classes | `PhArrowSquareOut` | `ExternalLink` | Both available |
| `delete`, `o_delete`, `delete_outline`, trash classes | `PhTrash` | `Trash2` | Both available |
| `copy`, `content_copy`, copy classes | `PhCopy` | `Copy` | Both available |
| `chevron_right`, angle/chevron classes | `PhCaretRight` | `ChevronRight` | Both available |
| `fas fa-comment-dots`, chat names | `PhChatCircleDots` | `MessageCircleMore` | Both available |
| `far fa-save`, `save_alt` | `PhFloppyDisk` | `Save` | Both available |
| `fas fa-ellipsis-v`, `more_vert` | `PhDotsThreeVertical` | `EllipsisVertical` | Both available |
| `refresh`, `sync`, `reload`, rotate classes | `PhArrowClockwise` | `RefreshCw` | Both available |
| `add`, `plus`, `o_add` | `PhPlus` | `Plus` | Both available |
| `fas fa-paper-plane`, `send` | `PhPaperPlaneRight` | `Send` | Both available |
| `fas fa-undo` | `PhArrowCounterClockwise` | `Undo2` | Both available |
| `fas fa-thumbtack`, `pin` | `PhPushPinSimple` | `Pin` | Both available |
| `check`, `check_circle`, circle-check classes | `PhCheckCircle` | `CircleCheck` | Both available |
| `edit`, `pen`, pencil classes | `PhPencilSimple` | `Pencil` | Both available |
| `expand_more`, `arrow_drop_down` | `PhCaretDown` | `ChevronDown` | Both available |
| `description`, `article`, `file` | `PhFileText` | `FileText` | Both available |
| `attach_file`, paperclip classes | `PhPaperclip` | `Paperclip` | Both available |
| `warning`, `error`, triangle/circle alert classes | `PhWarningCircle` | `TriangleAlert` | Both available |
| `auto_awesome`, magic/wand classes | `PhMagicWand` | `WandSparkles` | Both available |
| `play_arrow` | `PhPlay` | `Play` | Both available |
| `book` | `PhBookOpen` | `BookOpen` | Both available |
| `first_page`, `last_page` | `PhCaretLineLeft` / `PhCaretLineRight` | `ChevronsLeft` / `ChevronsRight` | Both available |
| `pdf`, `fas fa-file-pdf` | `PhFilePdf` | `FileText` | Phosphor has a PDF-specific icon; Lucide should use generic file/text |
| `smart_toy`, `robot`, `ai` | `PhRobot` / `PhBrain` | `Bot` / `Brain` | Both available |
| `tune`, `settings`, gear classes | `PhSliders` / `PhGearSix` | `SlidersHorizontal` / `Settings` | Both available |
| `hub`, `account_tree`, network concepts | `PhGraph` / `PhTreeStructure` | `Network` | Both available |
| `timeline` | `PhChartLine` / `PhTreeStructure` | `ChartNoAxesGantt` | Both possible; Lucide has a closer named metaphor |
| `fas fa-server` | `PhDatabase` / `PhStack` / `PhNetwork` | `Server` | Both possible; Lucide has a direct server icon |

## What Cannot Be Replaced One-to-One

These should remain custom assets or be intentionally redesigned:

| Current asset | Recommended treatment |
| --- | --- |
| `magnet` | Keep custom brand SVG |
| `magnet-msg` | Keep custom brand/mark SVG |
| `empty-collection` | Keep custom illustration, or redesign as a DS empty-state illustration |
| `like-emoji`, `neutral-emoji`, `dislike-emoji` | Keep custom emoji/feedback art, or replace with a deliberate non-emoji feedback visual |
| Theme-specific source illustrations | Replace only if they are action glyphs; keep if they carry theme/product identity |

## Recommendation

Use Phosphor as the main DS icon set.

Reasons:

- It is already installed and wired into `KmGlyph`.
- It covers the functional inventory well.
- Its weights allow one family to represent default, active, selected, filled, and emphasis states.
- The current DS direction already separates glyphs (`KmGlyph`) from brand/illustration sprites (`KmIcon`).
- Migration can continue incrementally by expanding `phosphorIcons.ts` and rewriting call sites to canonical DS names.

Lucide is also viable, but adopting it now would be more churn because it is not installed and would duplicate or replace the Phosphor work already started. Lucide is a good fallback choice if the desired visual style is stricter, thinner, and more uniformly outline-only.

## Proposed Next Steps

1. Expand the canonical DS icon registry to cover all top 100 current icon names.
2. Add an audit metric for new FontAwesome class strings and raw Material ligatures in feature templates.
3. Rewrite high-frequency names first: `search`, `close`, `o_info`, `open_in_new`, `delete`, `fas fa-comment-dots`, `far fa-save`, `fas fa-ellipsis-v`, `refresh`, `fas fa-paper-plane`, `fas fa-undo`.
4. Keep `KmIcon` only for `magnet`, `magnet-msg`, `empty-collection`, emoji feedback art, and other product illustrations.
5. After registry coverage is complete, remove unused action SVGs from the theme sprite folders (`copy`, `like`, `dislike`, possibly `send`) if no theme still depends on them.
