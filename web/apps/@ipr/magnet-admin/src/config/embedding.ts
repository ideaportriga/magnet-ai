// pgvector HNSW/IVFFlat indexes support at most 2000 dimensions, so vector
// search over embeddings wider than that falls back to sequential scans.
export const MAX_INDEXABLE_VECTOR_SIZE = 2000

interface EmbeddingModelLike {
  configs?: { vector_size?: number } | null
}

/**
 * Warning text for embedding models whose vectors are too wide to be indexed
 * by the vector database. Returns an empty string when the model is fine (or
 * unknown), so it can be used directly in `v-if`.
 */
export function embeddingVectorSizeWarning(model: EmbeddingModelLike | null | undefined): string {
  const size = model?.configs?.vector_size
  if (!size || size <= MAX_INDEXABLE_VECTOR_SIZE) return ''
  return (
    `This model produces ${size}-dimension vectors, but the database can only index vectors ` +
    `up to ${MAX_INDEXABLE_VECTOR_SIZE} dimensions. Semantic search will fall back to slow full scans ` +
    `as content grows — consider a model with vectors of ${MAX_INDEXABLE_VECTOR_SIZE} dimensions or fewer.`
  )
}
