# Contributing to Magnet AI

Thank you for your interest in contributing to Magnet AI!

## Getting Started

1.  **Read the Workflow Guide**: Please review [GIT_WORKFLOW.md](GIT_WORKFLOW.md) to understand our branching strategy, pull request process, and release cycle.
2.  **Fork the Repository**: Create a fork of the repository to work on your changes.
3.  **Clone the Repository**: Clone your fork locally.

## Development Environment

### API (Python)
-   We use **Poetry** for dependency management.
-   Install dependencies: `cd api && poetry install`
-   Run tests: `poetry run pytest`
-   Linting: `poetry run ruff check .`

### Web (Node.js/Vue)
-   We use **Yarn** and **Nx**.
-   Install dependencies: `cd web && yarn install`
-   Run tests: `yarn nx run-many --target=test --all`
-   Linting: `yarn nx run-many --target=lint --all`

## Pull Requests

-   Target the `develop` branch for new features.
-   Target the `main` branch for hotfixes (rare).
-   Ensure all CI checks pass before requesting a review.
-   Use descriptive titles and fill out the Pull Request template.

## Issue Reporting

-   Use the [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) template for bugs.
-   Use the [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) template for new ideas.

## Code of Conduct

Please be respectful and considerate of others. We follow the "Community First" principle.
