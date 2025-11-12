import { sortDateColumn } from '@shared/utils/sortDateColumn'
import { required } from '@shared/utils/validationRules'

const promptsControls = {
  id: {
    name: 'id',
    label: 'id',
    field: 'id',
    readonly: true,
    display: false,
    ignorePatch: true,
  },
  name: {
    name: 'name',
    label: 'Name',
    field: 'name',
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
    rules: [required()],
    validate: true,
  },
  blockHeading: {
    name: 'blockHeading',
    label: 'Block Heading',
    field: 'blockHeading',
  },
  createdAt: {
    name: 'createdAt',
    label: 'Created',
    field: 'createdAt',
    type: 'Date',
    sort: sortDateColumn,
    format: (val) => val?.toLocaleString(),
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
  prompt: {
    name: 'prompt',
    label: 'Prompt',
    field: 'prompt',
    rules: [required()],
    validate: true,
  },
  backgroundPrompt: {
    name: 'backgroundPrompt',
    label: 'Background Prompt',
    field: 'backgroundPrompt',
  },
  wordsMax: {
    name: 'wordsMax',
    label: 'Max Words',
    field: 'wordsMax',
    type: 'Number',
  },
  outputFormat: {
    name: 'outputFormat',
    label: 'Output Format',
    field: 'outputFormat',
    options: ['Bulleted list'],
  },
  model: {
    name: 'model',
    label: 'model',
    field: 'model',
    // TODO - move options to main.json?
    options: [
      // {
      //   label: 'GPT-3.5 Turbo',
      //   value: 'gpt-35-turbo',
      //   isJSONFormat: true,
      //   jsonFormatDocumetaion: 'https://platform.openai.com/docs/guides/structured-outputs/json-mode',
      // },
      // {
      //   label: 'GPT-4',
      //   value: 'gpt-4',
      //   isJSONFormat: true,
      //   jsonFormatDocumetaion: 'https://platform.openai.com/docs/guides/structured-outputs/json-mode',
      // },
      // {
      //   label: 'GPT-4 Turbo',
      //   value: 'gpt-4-turbo',
      //   isJSONFormat: true,
      //   jsonFormatDocumetaion: 'https://platform.openai.com/docs/guides/structured-outputs/json-mode',
      // },
      {
        label: 'GPT-4o',
        value: 'gpt-4o',
        isJSONFormat: true,
        isJSONSchema: true,
        jsonFormatDocumetaion: 'https://platform.openai.com/docs/guides/structured-outputs/json-mode',
      },
      {
        label: 'GPT-4o mini',
        value: 'gpt-4o-mini',
        isJSONFormat: true,
        jsonFormatDocumetaion: 'https://platform.openai.com/docs/guides/structured-outputs/json-mode',
      },
      {
        label: 'Cohere Command R+',
        value: 'cohere-command-r-plus',
      },
    ],
    rules: [required()],
    validate: true,
    default: 'gpt-35-turbo',
  },
  temperature: {
    type: 'Number',
    name: 'temperature',
    label: 'temperature',
    field: 'temperature',
    default: 1,
  },
  topP: {
    type: 'Number',
    name: 'topP',
    label: 'Top P',
    field: 'topP',
    default: 1,
  },
}

export default promptsControls
