import { sortDateColumn } from '@shared/utils/sortDateColumn'
import { required } from '@shared/utils/validationRules'
import promptsControls from './prompts'

const templatesControls = {
  id: {
    name: 'id',
    label: 'id',
    field: 'id',
    readonly: true,
    display: false,
    ignorePatch: true,
  },
  title: {
    name: 'title',
    label: 'Title',
    field: 'title',
    readonly: true,
    display: true,
    rules: [required()],
    validate: true,
  },
  description: {
    name: 'description',
    label: 'Description',
    field: 'description',
    readonly: true,
    display: true,
    rules: [required('')],
    validate: true,
  },
  pinned: {
    name: 'pinned',
    label: 'Pinned',
    field: 'pinned',
    display: true,
    type: 'Boolean',
  },
  createdAt: {
    name: 'createdAt',
    label: 'Created',
    field: 'createdAt',
    type: 'Date',
    sort: sortDateColumn,
    format: (val) => val?.toFormat('dd.MM.yyyy H:mm'),
    ignorePatch: true,
  },
  updatedAt: {
    name: 'updatedAt',
    label: 'Updated',
    field: 'updatedAt',
    type: 'Date',
    sort: sortDateColumn,
    format: (val) => val?.toFormat('dd.MM.yyyy H:mm'),
    ignorePatch: true,
  },
  publishedAt: {
    name: 'publishedAt',
    label: 'Published',
    field: 'publishedAt',
    type: 'Date',
    sort: sortDateColumn,
    format: (val) => val?.toFormat('dd.MM.yyyy H:mm'),
    ignorePatch: true,
  },
  category: {
    name: 'category',
    label: 'Category',
    field: 'category',
    options: ['email'],
    validate: true,
    rules: [],
  },
  prompts: {
    name: 'prompts',
    label: 'Prompts',
    field: 'prompts',
    type: 'StrapiDataObject',
    config: promptsControls,
    display: false,
    ignorePatch: true, //TODO REMOVE
  },
}

export default templatesControls
