# Frontend Architecture

The Magnet AI frontend is built using **Vue 3**, **TypeScript**, and **Nx** monorepo tools, providing a modern, modular, and maintainable user interface.

## Project Structure

```
web/
├── apps/
│   ├── magnet-admin/          # Admin Console (Configuration)
│   ├── magnet-panel/          # User Panel (Chat & Interaction)
│   └── magnet-docs/           # Documentation (VitePress)
├── packages/
│   ├── shared/                # Shared logic (composables, types, utils)
│   ├── themes/                # Theme configurations & assets
│   └── ui-comp/               # Shared UI Component Library
├── scripts/                   # Build and deployment scripts
├── nx.json                    # Nx configuration
├── package.json               # Dependencies
└── tsconfig.base.json         # TypeScript configuration
```

## Technology Stack

### Core Technologies

- **Vue 3**: Progressive JavaScript Framework (Composition API).
- **TypeScript**: Type-safe development.
- **Nx**: Monorepo management, build optimization, and task orchestration.
- **Vite**: Fast build tool and dev server.

### UI Components

- **PrimeVue**: Comprehensive UI component library.
- **Tailwind CSS**: Utility-first CSS framework (if used, or custom CSS).
- **Custom Components**: Located in `packages/ui-comp`.

### State Management

- **Pinia**: The intuitive store for Vue.js.
- **Composables**: Encapsulated stateful logic using Vue Composition API.

## Key Features

### 1. Agent Configuration UI (Admin)

Components for creating and managing agents:

- Agent builder interface
- Topic and action configuration
- Tool selection and setup
- Testing and validation

### 2. Chat Interface (Panel)

Interactive chat interface for end-users:

- Real-time streaming responses
- Markdown rendering
- History management
- Feedback mechanisms

### 3. Knowledge Source Integration

UI for connecting data sources:

- Source type selection
- Configuration forms
- Connection testing
- Status monitoring

### 4. Usage Dashboards

Analytics and monitoring:

- Conversation history
- LLM usage metrics
- RAG query analytics
- Cost tracking

## Component Architecture

### Monorepo Strategy

We use Nx to share code between the Admin and Panel applications.

- **Apps**: Thin layers that assemble pages and route configurations.
- **Packages**:
  - `ui-comp`: Dumb UI components (Buttons, Inputs, Cards).
  - `shared`: Business logic, API clients, types, and helper functions.
  - `themes`: Styling and branding assets.

### Component Patterns

#### 1. Composition API & Composables

Logic is extracted into reusable composables:

```typescript
// packages/shared/src/composables/useAgent.ts
export function useAgent(agentId: Ref<string>) {
  const agent = ref(null)
  const loading = ref(true)

  async function fetchAgent() {
    loading.value = true
    agent.value = await api.get(`/agents/${agentId.value}`)
    loading.value = false
  }

  watchEffect(() => {
    if (agentId.value) fetchAgent()
  })

  return { agent, loading }
}
```

#### 2. Smart vs. Dumb Components

- **Smart (Container)**: Handle data fetching, state, and pass data down. Usually Pages or complex widgets.
- **Dumb (Presentational)**: Receive props and emit events. Located in `ui-comp`.

## Routing

**Vue Router** is used for navigation.

- **Admin Routes**:
  - `/agents` - Agent management
  - `/knowledge` - Knowledge sources
  - `/settings` - System configuration
- **Panel Routes**:
  - `/chat/:id` - Active conversation
  - `/history` - Past conversations

## API Integration

### API Client

Centralized API client (likely using Axios or Fetch wrapper) in `packages/shared`.

```typescript
// packages/shared/src/api/client.ts
import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})
```

## Build and Development

### Nx Workspace

Benefits:

- **Computation Caching**: Never rebuild the same code twice.
- **Project Graph**: Visualize dependencies (`nx graph`).
- **Affected Commands**: Run tests only on changed projects.

### Development Server

```bash
# Run Panel
yarn nx dev magnet-panel

# Run Admin
yarn nx dev magnet-admin
```

### Production Build

```bash
yarn nx build magnet-panel
yarn nx build magnet-admin
```

## Testing Strategy

### Unit Tests

- **Vitest**: Fast unit test runner (Jest compatible).
- **Vue Test Utils**: Testing Vue components.

### E2E Tests

- **Cypress** or **Playwright**: For end-to-end integration testing.

## Internationalization

Support for multiple languages (i18n) is built-in, supporting English (en) and other locales.

## Documentation

VitePress-based documentation (this site) is also part of the monorepo in `apps/magnet-docs`.

## Next Steps

- [System Architecture](/docs/en/developers/architecture/system-architecture) - Overall architecture
- [Database Schema](/docs/en/developers/architecture/database) - Data models
- [Getting Started](/docs/en/developers/setup/getting-started) - Development setup
