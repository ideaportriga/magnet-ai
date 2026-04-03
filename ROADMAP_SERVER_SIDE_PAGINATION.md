# Roadmap: Server-Side Pagination & Search

## Current State

All entities now use server-side pagination, search, and sorting by default.

## Infrastructure

`useDataTable` composable defaults: `manualPagination: true, manualSorting: true, manualFiltering: true`.
Backend API accepts: `currentPage`, `pageSize`, `orderBy`, `sortOrder`, `search` + custom filter params.
Search is debounced (300ms) before sending to server.

## Per-Entity Status

### Server-Side Pagination (completed)

- [x] **jobs** — was already server-side
- [x] **observability_traces** — was already server-side
- [x] **files** — was already server-side
- [x] **collections** — removed `manual*: false` overrides
- [x] **rag_tools** — removed `manual*: false` overrides
- [x] **retrieval** — removed `manual*: false` overrides
- [x] **promptTemplates** — removed `manual*: false` overrides
- [x] **evaluation_sets** — removed `manual*: false` overrides
- [x] **mcp_servers** — removed `manual*: false` overrides
- [x] **api_keys** — removed `manual*: false` overrides
- [x] **api_servers** — removed `manual*: false` overrides
- [x] **knowledge_graph** — removed `manual*: false` overrides
- [x] **documents** — removed `manual*: false` overrides, keeps `extraParams` for collection_id
- [x] **model** — converted `dataFilter` tab filter to `extraParams: { type }`, kept `dataFilter` for is_default pinning only
- [x] **assistant_tools** — converted `dataFilter` tab filter to `extraParams: { type }`
- [x] **agents** — rewritten from raw `useList()` to `useList(queryParams)` with server-side search/sort/pagination
- [x] **ai_apps** — rewritten from raw `useList()` to `useList(queryParams)` with server-side search/sort/pagination
- [x] **evaluation_jobs** — removed `manual*: false` from flat table; grouped view uses paginated data

### No Changes Needed

- [x] **plugins** — static data, loaded once on startup, does not change without server restart
- [x] **provider** — small dataset, load all with long staleTime, no server-side pagination needed

## Notes

### evaluation_jobs grouped view
The grouped view (groupBy job/tool) aggregates data client-side. With server-side pagination, grouping applies only to the current page. For full grouping across all records, a backend aggregation endpoint would be needed.

### Edit Buffer Safety
No changes needed. Draft buffer is isolated from query refetches — `syncOnRefetch` is `false` by default.
