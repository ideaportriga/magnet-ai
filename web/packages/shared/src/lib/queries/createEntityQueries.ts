import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
  type UseQueryOptions,
} from '@tanstack/vue-query'
import { computed, unref, type MaybeRef } from 'vue'
import type { EntityApi, PaginationParams, ListResponse } from '../api'

export interface BaseEntity {
  id?: string
  name?: string
  [key: string]: unknown
}
import { entityKeys } from './queryKeys'

type EntityKeyName = keyof typeof entityKeys

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
  /** Called when any mutation fails. Use to show error messages to the user. */
  onMutationError?: (error: Error, entityKeyName: string, operation: string) => void
}

let _globalOptions: EntityQueriesOptions = {}

/** Set global options for all entity queries (e.g., error handler). Call once at app init. */
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

  return {
    useList(params, options) {
      return useQuery<ListResponse<T>>({
        queryKey: computed(() => keys.list(unref(params) ?? {})),
        queryFn: () => api.list(unref(params) ?? undefined),
        placeholderData: keepPreviousData,
        ...options,
      })
    },

    useDetail(id, options) {
      const resolvedId = computed(() => unref(id))
      return useQuery<T>({
        queryKey: computed(() => keys.detail(resolvedId.value ?? '')),
        queryFn: () => api.getById(resolvedId.value!),
        enabled: computed(() => !!resolvedId.value),
        ...options,
      })
    },

    useCreate() {
      const qc = useQueryClient()
      return useMutation<T, Error, Partial<T>>({
        mutationFn: (data) => api.create(data),
        onSuccess: () => {
          qc.invalidateQueries({ queryKey: keys.lists() })
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
        onSuccess: () => {
          qc.invalidateQueries({ queryKey: keys.lists() })
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
