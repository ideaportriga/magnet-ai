# Background tasks (Taskiq)

Magnet uses **Taskiq** for all background work — RAG indexing,
Note Taker post-processing, periodic housekeeping crons, and
similar fire-and-forget jobs. Taskiq replaces APScheduler from
previous releases; this document covers the run-time topology
and the knobs you'll touch in production.

## Two run modes

Taskiq can run inside the API process (default) or as separate
worker / scheduler CLIs. The choice is **per-component**:

| Setting | Default | When `true` |
|---|---|---|
| `TASKIQ_INPROCESS_WORKER_ENABLED` | `true` | The worker runs as an asyncio task inside the API process. |
| `TASKIQ_INPROCESS_SCHEDULER_ENABLED` | `true` | The scheduler runs as an asyncio task inside the API process. |

### Single-container (default)

In the default Azure / Docker deployment, one Python process runs
the API, worker, and scheduler together. This is the simplest
layout: one container image, one process, one set of logs.

```yaml
# docker-compose.yml — single API container
services:
  api:
    image: magnet-ai/api:latest
    environment:
      TASKIQ_INPROCESS_WORKER_ENABLED: "true"
      TASKIQ_INPROCESS_SCHEDULER_ENABLED: "true"
```

### Multi-process (local dev, K8s)

For local development or production K8s clusters where you want
the worker on its own pod (separate scaling, separate restart
window), opt out of the in-process scheduler and worker:

```yaml
services:
  api:
    environment:
      TASKIQ_INPROCESS_WORKER_ENABLED: "false"
      TASKIQ_INPROCESS_SCHEDULER_ENABLED: "false"

  worker:
    command: >
      taskiq worker tasks.broker:broker
        --fs-discover
        --tasks-pattern 'src/tasks/definitions/*.py'
        --tasks-pattern 'src/tasks/schedules/*.py'
        --ack-type when_executed
        --workers 1
        --max-async-tasks 4
        --max-tasks-per-child 20
        --hardkill-count 1
        --log-level INFO

  scheduler:
    command: >
      taskiq scheduler tasks.scheduler:scheduler
        --fs-discover
        --tasks-pattern 'src/tasks/definitions/*.py'
        --tasks-pattern 'src/tasks/schedules/*.py'
        --skip-first-run
        --log-level INFO
```

`npm run dev` (the local-dev orchestration script) launches the
multi-process layout: API, worker, scheduler, and Vite, each in
its own coloured pane via `concurrently`.

::: warning Scheduler is a singleton
**Never** run more than one scheduler replica. Schedule sources
are not idempotent across multiple firing scheduler — duplicate
jobs are the result. The API equivalent: set
`TASKIQ_INPROCESS_SCHEDULER_ENABLED=true` on at most one
replica, or run a single dedicated scheduler container.
:::

## Tuning

Worker concurrency and timeouts are configured via env vars. The
defaults are sized for the bundled single-process deployment; in
K8s with dedicated worker pods you typically increase
concurrency.

| Variable | Default | Effect |
|---|---|---|
| `TASKIQ_WORKER_CONCURRENCY` | `8` | Max concurrent async tasks per worker (`--max-async-tasks`). |
| `TASKIQ_WORKER_PROCESSES` | `1` | Worker child processes (`--workers`). Multiplies concurrency by N. |
| `TASKIQ_DEFAULT_TIMEOUT_SECONDS` | `1800` | Hard per-task timeout (default 30 min). |
| `TASKIQ_WAIT_TASKS_TIMEOUT` | `1860` | Graceful-shutdown wait. **Must** be ≥ `TASKIQ_DEFAULT_TIMEOUT_SECONDS`. |
| `TASKIQ_SCHEDULER_UPDATE_INTERVAL` | `10` | Seconds between scheduler polls. |
| `TASKIQ_SCHEDULER_SKIP_FIRST_RUN` | `true` | On boot, skip schedules that would have fired during downtime. |
| `TASKIQ_STUCK_PROCESSING_GRACE_SECONDS` | `120` | Grace time after the per-task timeout before a `PROCESSING` job is flagged stuck. |

## Broker

Taskiq runs against a **Postgres-backed broker** by default —
the same database as the application data, so no extra service
to operate. The broker writes to dedicated tables shipped by
migration `2026-04-21_taskiq_migration`:

- `taskiq_messages` — pending and in-flight jobs.
- `taskiq_schedules` — cron-style schedule definitions.
- `taskiq_result` — completed task results.

To switch to a Redis or RabbitMQ broker, override
`TASKIQ_BROKER_URL` and redeploy; the schemas are otherwise
unchanged.

## Stuck-task detection

`TASKIQ_STUCK_PROCESSING_GRACE_SECONDS` is the grace window
between a task's nominal timeout and when the runtime considers
it abandoned. Stuck tasks are surfaced in the **Jobs** admin
page with a yellow status chip; you can:

- **Cancel** — moves the job to `failed`, releases the slot.
- **Reset** — moves the job back to `pending` so it re-enters the
  queue. Use sparingly; idempotency is the task author's
  responsibility.

## Observability

Every Taskiq run carries the same OpenTelemetry trace context as
the originating HTTP request (when applicable). The dev stack
ships a Grafana / Loki configuration with:

- A `notetaker.running_jobs` gauge showing per-stage Note Taker
  jobs.
- A `taskiq_jobs_total` counter labelled by task name and outcome.
- Loki queries on `{application="magnet-ai", logger="taskiq"}`.

See [Observability / Logs](../developers/guides/logging) for the
LogQL examples.

## Migrating from APScheduler

If you are upgrading a deployment that used APScheduler (pre-alpha
releases):

1. Stop the old API.
2. Apply the `2026-04-21_taskiq_migration` Alembic revision. It
   creates the new tables; it does **not** carry over pending
   APScheduler jobs (they were transient anyway).
3. Drop the `APScheduler` env vars from your deployment manifest
   — they are no longer read.
4. Set the four `TASKIQ_*` knobs above for your topology.
5. Start the new API; verify the scheduler is firing by watching
   the logs for `taskiq.scheduler` entries.

The old `apscheduler` package is no longer installed, so any
custom plug-ins that imported from it will fail at import time
and need porting to the Taskiq broker API.
