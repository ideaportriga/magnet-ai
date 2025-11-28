# Magnet UI Frontend

## How to start

Install dependencies:

```sh
corepack enable
yarn install
```

To explore the workspace, run:

```sh
yarn nx graph
```

## Configuration files for Magnet AI

You need to create main.json file in `magnet-admin/public/config/main.json` with the following content:

```json
{
  "auth": {
    "enabled": true,
    "provider": "Microsoft",
    "popup": {
      "width": "600",
      "height": "400"
    }
  },
  "api": {
    "aiBridge": {
      "baseUrl": "http://localhost:8000"
    }
  },
  "panel": {
    "baseUrl": "https://localhost:7002"
  },
  "admin": {
    "baseUrl": "https://localhost:7000"
  }
}
```

auth - configuration for authentication
api - configuration for Magnet AI Backend
panel - configuration for Magnet AI Panel host
admin - configuration for Magnet AI Admin host

and in `magnet-panel/public/config/main.json` :

```json
{
  "theme": "siebel",
  "auth": {
    "enabled": true,
    "provider": "Microsoft",
    "popup": {
      "width": "600",
      "height": "400"
    }
  },
  "api": {
    "aiBridge": {
      "baseUrl": "http://localhost:8000"
    }
  },
  "admin": {
    "baseUrl": "https://localhost:7000"
  },
  "panel": {
    "baseUrl": "https://localhost:7002"
  }
}
```

theme - configuration for Magnet AI Panel theme `default/siebel/salesforce`

## How to run tasks

To run a task for a project, use the following command:

```sh
yarn nx [task] [project]
```
task - dev, build, preview etc. project - project name (magnet-admin / magnet-panel)

```sh
yarn nx dev magnet-admin
```

For run several apps in parallel:

```sh
yarn nx run-many --target=[task] --projects=[project1],[project2]
```

```sh
yarn nx run-many --target=dev --projects=magnet-admin,magnet-panel
```



# Nx Monorepo Project Structure

This document describes the structure and organization of an Nx monorepo, as inferred from the provided configuration files (`nx.json`, `tsconfig.base.json`) and the project dependency graph.

## Project Structure
The monorepo is organized into several packages, each residing in the `packages/` directory. Below is a breakdown of the projects and their relationships, as shown in the dependency graph:

### 1. `@ipr/magnet-e2e`
- **Type**: End-to-end testing project (likely using Cypress, as indicated in `nx.json` plugins).
- **Dependencies**: 
  - Implicitly depends on `magnet-admin` (as shown by the "implicit" arrow in the graph), suggesting it tests functionalities related to the `magnet-admin` project.
- **Purpose**: Handles end-to-end testing for the monorepo, ensuring the integration of various components works as expected.

### 2. `magnet-admin`
- **Type**: Magnet AI Administration application.
- **Dependencies**:
  - Depends on `shared` (core shared utilities).
  - Depends on `themes` (assets for theming purposes).
  - Depends on `ui-comp` (shared UI components).

### 3. `magnet-docs`
- **Type**: Magnet AI Documentation
- **Purpose**: Contains documentation for the Magnet AI system, likely providing guidance on installation, configuration, and usage.

### 4. `magnet-panel`
- **Type**: Application or library (likely a frontend or control panel).
- **Dependencies**:
  - Depends on `shared` (core shared utilities).
  - Depends on `themes` (assets for theming purposes).
  - Depends on `ui-comp` (shared UI components).
- **Purpose**: Provides a user interface for AI Application. 

### 5. `ui-comp`
- **Type**: UI components library
- **Dependencies**:
  - Depends on `shared` (core shared utilities).
- **Purpose**: A reusable library of vue UI components used across all apps. 

### 6. `shared`
- **Type**: Library (shared utilities)
- **Purpose**: Contains shared code, utilities, or configurations used by multiple projects in the monorepo, ensuring consistency and reducing duplication.

### 7. `themes`
- **Type**: Styles (assets for theming purposes).
- **Purpose**: Manages themes or styling configurations for the monorepo, ensuring a consistent look and feel across applications.

## Configuration Details

### `nx.json`
- **Named Inputs**: Defines `default` and `production` input sets for builds, excluding test files, ESLint configurations, and Cypress files in production builds. Includes a `sharedGlobals` input referencing `.gitlab-ci.yml` for CI/CD integration.
- **Plugins**: Integrates Nx plugins for ESLint, Vite, Cypress, and Jest, enabling targets like `build`, `test`, `e2e`, `lint`, and `serve`.
- **Target Defaults**: Ensures `e2e-ci` targets depend on upstream `build` targets, maintaining a correct build order.

### `tsconfig.base.json`
- **Compiler Options**: Configured for TypeScript with ES2015 target, ESNext modules, and DOM/ES2020 libraries. Enables source maps, decorators, and import helpers.
- **Paths**: Defines aliases for importing from packages:
  - `@shared` points to `packages/shared/src/index.ts`.
  - `@shared/*` points to `packages/shared/src/lib/*`.
  - `@themes` points to `packages/themes/src/index.ts`.
  - `@ui` points to `packages/ui-comp/src/index.ts`.
- **Exclusions**: Excludes `node_modules` and `tmp` directories from compilation.

## Development Workflow
- Use Nx commands (e.g., `nx build`, `nx test`, `nx e2e`) to manage and run tasks across projects.
- Leverage the `shared` and `themes` packages to maintain consistency in logic and styling.
- Test end-to-end functionality with `@ipr/magnet-e2e`, ensuring integration across `magnet-admin`, `magnet-panel`, and other components.

## Notes
- The monorepo avoids cloud connectivity (`neverConnectToCloud: true` in `nx.json`), suggesting an on-premises or isolated development environment.
- The structure supports scalability, with clear separation of concerns between admin, panel, UI, themes, and shared logic.
