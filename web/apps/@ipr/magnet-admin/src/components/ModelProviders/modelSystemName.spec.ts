import { describe, expect, it } from 'vitest'

import { validSystemName } from '@shared/utils/validationRules'
import { toModelSystemName } from './modelSystemName'

describe('toModelSystemName', () => {
  it.each([
    ['OPENAI', 'gpt-4o', 'OPENAI_GPT-4O'],
    ['OPENAI', 'gpt-4.1', 'OPENAI_GPT-4_1'],
    ['AZURE_OPEN_AI', 'gpt-4.1-mini', 'AZURE_OPEN_AI_GPT-4_1-MINI'],
    ['OPENROUTER', 'openai/gpt-4o', 'OPENROUTER_OPENAI_GPT-4O'],
    ['BEDROCK', 'anthropic.claude-3-5-sonnet-20240620-v1:0', 'BEDROCK_ANTHROPIC_CLAUDE-3-5-SONNET-20240620-V1_0'],
    ['OLLAMA', 'llama3.1:8b', 'OLLAMA_LLAMA3_1_8B'],
    ['OPENAI', ' my model. ', 'OPENAI_MY_MODEL'],
  ])('%s + %s -> %s', (provider, model, expected) => {
    const name = toModelSystemName(provider, model)
    expect(name).toBe(expected)
    expect(validSystemName()(name)).toBe(true)
  })

  it('works without a provider and never starts with a digit', () => {
    expect(toModelSystemName(null, '4.1-turbo')).toBe('_4_1-TURBO')
    expect(toModelSystemName(undefined, 'gpt-4.1')).toBe('GPT-4_1')
  })
})
