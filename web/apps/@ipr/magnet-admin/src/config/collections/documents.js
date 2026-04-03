import { sortDateColumn } from '@shared/utils/sortDateColumn'
import { formatDateTime } from '@shared/utils/dateTime'
import { m } from '@/paraglide/messages'

const documnentsControls = {
  id: {
    name: 'id',
    label: 'id',
    field: 'id',
    readonly: true,
    fromMetadata: false,
    display: false,
  },
  content: {
    name: 'content',
    label: m.common_content(),
    field: 'content',
    readonly: true,
    fromMetadata: false,
    display: false,
  },
  content_override: {
    name: 'content_override',
    label: m.collections_contentOverride(),
    field: 'content_override',
    readonly: true,
    fromMetadata: false,
    display: false,
  },
  originalContent: {
    name: 'originalContent',
    label: m.collections_originalContent(),
    field: 'originalContent',
    readonly: true,
    fromMetadata: false,
    display: false,
  },
  title: {
    name: 'metadata.title',
    label: m.common_title(),
    field: (row) => row?.metadata?.['title'],
    display: true,
    columnNumber: 0,
    fromMetadata: false,
    style: 'max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;',
  },
  type: {
    name: 'metadata.type',
    label: m.common_type(),
    field: (row) => row?.metadata?.['type'],
    display: true,
    columnNumber: 1,
    fromMetadata: false,
  },
  createdTime: {
    name: 'metadata.createdTime',
    label: m.common_created(),
    field: (row) => row?.metadata?.['createdTime'],
    type: 'Date',
    sort: sortDateColumn,
    format: (val) => formatDateTime(val),
    columnNumber: 2,
    fromMetadata: false,
  },
  modifiedTime: {
    name: 'metadata.modifiedTime',
    label: m.common_modifiedShort(),
    field: (row) => row?.metadata?.['modifiedTime'],
    type: 'Date',
    sort: sortDateColumn,
    format: (val) => formatDateTime(val),
    columnNumber: 3,
    fromMetadata: false,
  },
  metadata: {
    name: 'metadata',
    label: m.common_metadata(),
    field: 'metadata',
    readonly: false,
    type: 'Object',
    display: false,
    fromMetadata: false,
    ignorePatch: true,
  },
}

export default documnentsControls
