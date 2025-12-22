export interface Document {
  id: string
  name: string
  type: string
  content_profile?: string
  description?: string
  title?: string
  chunks_count: number
  status: string
  status_message?: string
  processing_time?: number
  created_at: string
  updated_at?: string
  source_name?: string
  toc?: TocNode[]
  summary?: string
  total_pages?: number
}

export interface Chunk {
  id: string
  document_id: string
  document_name: string
  name: string
  title?: string
  page?: number
  parent?: string
  chunk_type?: string
  content?: string
  content_format?: string
  created_at?: string
  toc_reference?: string
}

export interface TocNode {
  name: string
  text?: string
  children?: TocNode[]
}

export type TreeNodeType = 'toc' | 'chunk' | 'group'

export interface TreeNode {
  id: string
  label: string
  type: TreeNodeType
  children?: TreeNode[]
  count?: number
  chunk?: Chunk
}
