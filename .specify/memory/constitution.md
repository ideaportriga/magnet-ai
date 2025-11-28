<!--
Sync Impact Report:
- Version change: New (1.0.0)
- Added sections: All principles (Community First, Pragmatic Modern Stack, Critical-Only Strictness, Flexible Style)
- Templates requiring updates: ✅ None (templates are generic and reference constitution dynamically)
-->

# Magnet AI Constitution

## Core Principles

### I. Community First (Open & Welcoming)
Code must be clear and welcoming to external contributors. The project must be easy to fork, run, and maintain. Development speed and joy matter more than absolute perfection.

### II. Pragmatic Modern Stack
Async code is encouraged everywhere it makes sense (Litestar, Advanced-Alchemy). Use composable Litestar plugins. Frontend must use Vue 3 Composition API + `<script setup>`, Pinia, and Vue Router. Any consistent formatting style (black/ruff/Prettier) is acceptable within the same file.

### III. Critical-Only Strictness
Fix ONLY serious issues. This includes:
1. Critical security vulnerabilities.
2. Obvious bugs and race conditions in async code.
3. Type errors that prevent the app from starting.
4. SQL injection risks or broken SQLAlchemy/Advanced-Alchemy session usage.
5. Project structure issues that break `docker-compose up` or dev mode.
6. Missing or broken essential open-source artifacts (LICENSE, CONTRIBUTING.md, README with setup instructions).

### IV. Flexible Style (Do Not Touch)
Do NOT enforce subjective preferences. This includes:
- Naming style preferences (camelCase vs snake_case on frontend is fine).
- Minor formatting, import order, object key order.
- Choice between provide/inject, Pinia, or props drilling.
- Small code duplication if it improves readability.
- Sync code in places where async brings no real benefit.

## Governance

Amendments to this constitution require a Pull Request with explicit approval from the core team. All PRs and code reviews must verify compliance with these principles. Complexity must be justified.

**Version**: 1.0.0 | **Ratified**: 2025-11-27 | **Last Amended**: 2025-11-27
