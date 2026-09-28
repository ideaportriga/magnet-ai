import { describe, it, expect } from 'vitest'
import { h } from 'vue'
import { mount } from '@vue/test-utils'
import KmBlockInput from './BlockInput.vue'

function transfer(data: Record<string, string>, files: File[] = []) {
  return {
    getData: (type: string) => data[type] ?? '',
    files,
  }
}

function mountInput(props: Record<string, unknown> = {}) {
  return mount(KmBlockInput, {
    props: { modelValue: ['a', 'b'], placeholder: 'Paste here', ...props },
    slots: { block: ({ item }: { item: unknown }) => h('span', { class: 'label' }, String(item)) },
    attachTo: document.body,
    // The empty-state icon needs the Quasar plugin, which unit tests don't install.
    global: { stubs: { QIcon: true } },
  })
}

describe('KmBlockInput', () => {
  it('renders one block per item through the slot', () => {
    const wrapper = mountInput()
    expect(wrapper.findAll('[data-test="km-block-input-block"]').map((b) => b.text())).toEqual(['a', 'b'])
  })

  it('shows the empty state only without items and draft', async () => {
    const wrapper = mountInput({ modelValue: [], hint: 'Several pages are fine' })
    expect(wrapper.find('.km-block-input__empty').text()).toContain('Paste here')
    await wrapper.setProps({ draft: 'typing' })
    expect(wrapper.find('.km-block-input__empty').exists()).toBe(false)
  })

  it('emits commit-text on Enter but not on Shift+Enter', async () => {
    const wrapper = mountInput({ draft: 'use EU prices' })
    const draft = wrapper.find('[data-test="km-block-input-draft"]')
    await draft.trigger('keydown', { key: 'Enter', shiftKey: true })
    expect(wrapper.emitted('commit-text')).toBeUndefined()
    await draft.trigger('keydown', { key: 'Enter' })
    expect(wrapper.emitted('commit-text')).toEqual([['use EU prices']])
  })

  it('captures a paste into the empty draft', async () => {
    const wrapper = mountInput()
    const draft = wrapper.find('[data-test="km-block-input-draft"]')
    await draft.trigger('paste', { clipboardData: transfer({ 'text/plain': 'line 1\nline 2', 'text/html': '<p>x</p>' }) })
    expect(wrapper.emitted('transfer')?.[0]?.[0]).toEqual({ html: '<p>x</p>', text: 'line 1\nline 2', files: [] })
  })

  it('leaves short pastes and pastes while typing to the draft', async () => {
    const wrapper = mountInput({ captureMinLength: 40 })
    const draft = wrapper.find('[data-test="km-block-input-draft"]')
    await draft.trigger('paste', { clipboardData: transfer({ 'text/plain': 'gpt-4.1' }) })
    expect(wrapper.emitted('transfer')).toBeUndefined()

    await wrapper.setProps({ draft: 'note: ' })
    await draft.trigger('paste', { clipboardData: transfer({ 'text/plain': 'a\nlong\npaste' }) })
    expect(wrapper.emitted('transfer')).toBeUndefined()
  })

  it('captures a short paste that carries a table', async () => {
    const wrapper = mountInput({ captureMinLength: 40 })
    await wrapper
      .find('[data-test="km-block-input-draft"]')
      .trigger('paste', { clipboardData: transfer({ 'text/plain': '$2 $8', 'text/html': '<table><tr><td>$2</td></tr></table>' }) })
    expect(wrapper.emitted('transfer')).toHaveLength(1)
  })

  it('emits transfer on drop', async () => {
    const wrapper = mountInput()
    await wrapper.find('.km-block-input__control').trigger('drop', { dataTransfer: transfer({ 'text/plain': 'dragged' }) })
    expect(wrapper.emitted('transfer')?.[0]?.[0]).toMatchObject({ text: 'dragged' })
  })

  it('Backspace on an empty draft focuses the last block, a second one removes it', async () => {
    const wrapper = mountInput()
    await wrapper.find('[data-test="km-block-input-draft"]').trigger('keydown', { key: 'Backspace' })
    const blocks = wrapper.findAll('[data-test="km-block-input-block"]')
    expect(document.activeElement).toBe(blocks[1].element)

    await blocks[1].trigger('keydown', { key: 'Backspace' })
    expect(wrapper.emitted('update:modelValue')).toEqual([[['a']]])
    expect(wrapper.emitted('remove')).toEqual([['b', 1]])
    wrapper.unmount()
  })

  it('Delete removes the focused block and Enter activates it', async () => {
    const wrapper = mountInput()
    const first = wrapper.findAll('[data-test="km-block-input-block"]')[0]
    await first.trigger('keydown', { key: 'Enter' })
    expect(wrapper.emitted('activate')).toEqual([['a', 0]])
    await first.trigger('keydown', { key: 'Delete' })
    expect(wrapper.emitted('update:modelValue')).toEqual([[['b']]])
    wrapper.unmount()
  })
})
