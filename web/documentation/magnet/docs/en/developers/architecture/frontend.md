# Frontend Architecture

The Magnet AI frontend is built using React, TypeScript, and Nx monorepo tools, providing a modern and maintainable user interface.

## Project Structure

```
web/
├── apps/
│   └── knowledge-magnet/      # Main application
├── packages/                  # Shared packages
├── documentation/
│   └── magnet/               # VitePress documentation
├── scripts/                   # Build and deployment scripts
├── nx.json                   # Nx configuration
├── package.json              # Dependencies
└── tsconfig.base.json        # TypeScript configuration
```

## Technology Stack

### Core Technologies
- **React 18**: Component-based UI framework
- **TypeScript**: Type-safe development
- **Nx**: Monorepo management and build optimization
- **Vite**: Fast build tool and dev server

### UI Components
- Custom React components
- Responsive design
- Accessibility (a11y) considerations

### State Management
- React Context API
- React Hooks (useState, useEffect, useReducer)
- Custom hooks for data fetching

## Key Features

### 1. Agent Configuration UI
Components for creating and managing agents:
- Agent builder interface
- Topic and action configuration
- Tool selection and setup
- Testing and validation

### 2. Prompt Template Management
Interface for prompt templates:
- Template editor
- Variable management
- Version control (if applicable)
- Preview functionality

### 3. Knowledge Source Integration
UI for connecting data sources:
- Source type selection
- Configuration forms
- Connection testing
- Status monitoring

### 4. RAG Tools Configuration
Interface for RAG tool setup:
- Knowledge source selection
- Retrieval parameters
- Model configuration
- Testing interface

### 5. Usage Dashboards
Analytics and monitoring:
- Conversation history
- LLM usage metrics
- RAG query analytics
- Cost tracking

## Component Architecture

### Component Hierarchy
```
App
├── Layout
│   ├── Header
│   ├── Sidebar
│   └── Content
├── Pages
│   ├── Agents
│   │   ├── AgentList
│   │   └── AgentEditor
│   ├── PromptTemplates
│   ├── KnowledgeSources
│   └── Dashboards
└── Shared Components
    ├── Forms
    ├── Tables
    └── Modals
```

### Component Patterns

#### 1. Container/Presentational Pattern
- **Container**: Handle data fetching and state
- **Presentational**: Render UI based on props

#### 2. Custom Hooks
```typescript
// Example custom hook
function useAgent(agentId: string) {
  const [agent, setAgent] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchAgent(agentId).then(setAgent);
  }, [agentId]);
  
  return { agent, loading };
}
```

#### 3. Composition
- Composable components
- Reusable UI elements
- Prop drilling minimization

## Routing

React Router for navigation:
- `/agents` - Agent management
- `/prompt-templates` - Template editor
- `/knowledge-sources` - Data source config
- `/rag-tools` - RAG configuration
- `/dashboards` - Analytics views

## API Integration

### API Client
Centralized API communication:
```typescript
// Example API service
class ApiService {
  async getAgents() {
    return fetch('/api/agents').then(r => r.json());
  }
  
  async createAgent(data) {
    return fetch('/api/agents', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
}
```

### Data Fetching Strategies
- Fetch on mount
- Lazy loading
- Caching strategies
- Error handling

## Styling

### CSS Architecture
- Modular CSS
- CSS Modules (if used)
- Responsive design
- Theme support (if applicable)

### Design System
- Consistent color palette
- Typography system
- Spacing scale
- Component variants

## Build and Development

### Nx Workspace
Benefits:
- Code sharing across apps
- Affected command for testing
- Build caching
- Dependency graph visualization

### Development Server
```bash
nx serve knowledge-magnet
```

### Production Build
```bash
nx build knowledge-magnet
```

## Testing Strategy

### Unit Tests
- Component testing with Jest
- React Testing Library
- Snapshot testing

### Integration Tests
- User flow testing
- API integration tests

### E2E Tests (if applicable)
- Full application testing
- Critical path validation

## Performance Optimization

### Code Splitting
- Route-based splitting
- Lazy loading components
- Dynamic imports

### Memoization
- React.memo for expensive components
- useMemo for computed values
- useCallback for function props

### Bundle Optimization
- Tree shaking
- Minification
- Asset optimization

## Accessibility

- Semantic HTML
- ARIA labels
- Keyboard navigation
- Screen reader support

## Internationalization

Support for multiple languages:
- English (en)
- Latvian (lv) - partially implemented

## Documentation

VitePress-based documentation:
- User guides
- Admin guides
- Developer guides
- API reference

## Next Steps

- [System Architecture](/docs/en/developers/architecture/system-architecture) - Overall architecture
- [Database Schema](/docs/en/developers/architecture/database) - Data models
- [Getting Started](/docs/en/developers/setup/getting-started) - Development setup
