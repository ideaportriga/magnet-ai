import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
  type UseQueryOptions,
} from '@tanstack/vue-query'
import { computed, unref, type MaybeRef } from 'vue'
import type { EntityApi, PaginationParams, ListResponse } from '@shared/api'
import type { BaseEntity } from '@/types'
import { entityKeys } from './queryKeys'

type EntityKeyName = keyof typeof entityKeys

// §C.2 — per-entity staleTime overrides. Live dashboards (traces, metrics,
// jobs) need fresh data every few seconds; stable catalogs (agents,
// providers, models) can cache for minutes. Anything not listed here gets
// the QueryClient default (60s, see plugins/vueQuery.ts).
const STALE_TIME_BY_ENTITY: Partial<Record<EntityKeyName, number>> = {
  traces: 5_000,
  metrics: 5_000,
  jobs: 10_000,
  conversations: 15_000,
  agents: 60_000,
  providers: 300_000,
  ai_models: 300_000,
  prompts: 300_000,
  collections: 60_000,
} as Partial<Record<EntityKeyName, number>>

export interface EntityQueries<T extends BaseEntity> {
  useList: (
    params?: MaybeRef<PaginationParams & Record<string, unknown>>,
    options?: Partial<UseQueryOptions<ListResponse<T>>>,
  ) => ReturnType<typeof useQuery<ListResponse<T>>>

  useDetail: (
    id: MaybeRef<string | null | undefined>,
    options?: Partial<UseQueryOptions<T>>,
  ) => ReturnType<typeof useQuery<T>>

  useCreate: () => ReturnType<typeof useMutation<T, Error, Partial<T>>>
  useUpdate: () => ReturnType<typeof useMutation<T, Error, { id: string; data: Partial<T> }>>
  useRemove: () => ReturnType<typeof useMutation<void, Error, string>>
  useSync: () => ReturnType<typeof useMutation<unknown, Error, string>>
  useTest: () => ReturnType<typeof useMutation<unknown, Error, { id: string; body?: unknown }>>
}

export interface EntityQueriesOptions {
  onMutationError?: (error: Error, entityKeyName: string, operation: string) => void
}

let _globalOptions: EntityQueriesOptions = {}

export function setEntityQueriesOptions(options: EntityQueriesOptions) {
  _globalOptions = options
}

export function createEntityQueries<T extends BaseEntity>(
  entityKeyName: EntityKeyName,
  api: EntityApi<T>,
): EntityQueries<T> {
  const keys = entityKeys[entityKeyName]

  function handleMutationError(error: Error, operation: string) {
    _globalOptions.onMutationError?.(error, entityKeyName, operation)
  }

  const entityStaleTime = STALE_TIME_BY_ENTITY[entityKeyName]

  return {
    useList(params, options) {
      return useQuery<ListResponse<T>>({
        queryKey: computed(() => keys.list(unref(params) ?? {})),
        queryFn: () => api.list(unref(params) ?? undefined),
        placeholderData: keepPreviousData,
        ...(entityStaleTime !== undefined ? { staleTime: entityStaleTime } : {}),
        ...options,
      })
    },

    useDetail(id, options) {
      const resolvedId = computed(() => unref(id))
      return useQuery<T>({
        queryKey: computed(() => keys.detail(resolvedId.value ?? '')),
        queryFn: () => api.getById(resolvedId.value!),
        enabled: computed(() => !!resolvedId.value),
        ...(entityStaleTime !== undefined ? { staleTime: entityStaleTime } : {}),
        ...options,
      })
    },

    useCreate() {
      const qc = useQueryClient()
      return useMutation<T, Error, Partial<T>>({
        mutationFn: (data) => api.create(data),
        onSuccess: () => {
          qc.invalidateQueries({ queryKey: keys.all })
          qc.invalidateQueries({ queryKey: ['catalog'] })
        },
        onError: (error) => handleMutationError(error, 'create'),
      })
    },

    useUpdate() {
      const qc = useQueryClient()
      return useMutation<T, Error, { id: string; data: Partial<T> }>({
        mutationFn: ({ id, data }) => api.update(id, data),
        onSuccess: (_, { id }) => {
          qc.invalidateQueries({ queryKey: keys.lists() })
          qc.invalidateQueries({ queryKey: keys.detail(id) })
        },
        onError: (error) => handleMutationError(error, 'update'),
      })
    },

    useRemove() {
      const qc = useQueryClient()
      return useMutation<void, Error, string>({
        mutationFn: (id) => api.remove(id),
        onSuccess: (_, id) => {
          qc.removeQueries({ queryKey: keys.detail(id) })
          qc.invalidateQueries({ queryKey: keys.lists() })
          qc.invalidateQueries({ queryKey: ['catalog'] })
        },
        onError: (error) => handleMutationError(error, 'remove'),
      })
    },

    useSync() {
      const qc = useQueryClient()
      return useMutation<unknown, Error, string>({
        mutationFn: (id) => api.sync(id),
        onSuccess: (_, id) => {
          qc.invalidateQueries({ queryKey: keys.lists() })
          qc.invalidateQueries({ queryKey: keys.detail(id) })
        },
        onError: (error) => handleMutationError(error, 'sync'),
      })
    },

    useTest() {
      return useMutation<unknown, Error, { id: string; body?: unknown }>({
        mutationFn: ({ id, body }) => api.test(id, body),
        onError: (error) => handleMutationError(error, 'test'),
      })
    },
  }
}
