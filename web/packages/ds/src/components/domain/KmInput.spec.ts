import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick, ref } from 'vue'
import KmInput from './KmInput.vue'

describe('KmInput', () => {
  it('renders an <input> by default with the data-test hook', () => {
    const wrapper = mount(KmInput)
    const input = wrapper.find('[data-test="km-input"]')
    expect(input.exists()).toBe(true)
    expect(input.element.tagName).toBe('INPUT')
  })

  it('renders a <textarea> when type="textarea"', () => {
    const wrapper = mount(KmInput, { props: { type: 'textarea' } })
    expect(wrapper.find('[data-test="km-input"]').element.tagName).toBe('TEXTAREA')
  })

  it('renders a <textarea> when multiline is set', () => {
    const wrapper = mount(KmInput, { props: { multiline: true } })
    expect(wrapper.find('[data-test="km-input"]').element.tagName).toBe('TEXTAREA')
  })

  it('sets textarea row bounds as CSS variables', () => {
    const wrapper = mount(KmInput, {
      props: {
        autogrow: true,
        minRows: 1,
        maxRows: 10,
      },
    })

    const style = wrapper.find('textarea').attributes('style')
    expect(style).toContain('--km-input-textarea-min-content-size: 1lh;')
    expect(style).toContain('--km-input-textarea-max-content-size: 10lh;')
    expect(wrapper.find('.km-input').attributes('data-single-row')).toBe('true')
  })

  it('autosizes autogrow textarea and leaves single-row mode after growth', async () => {
    const wrapper = mount(KmInput, {
      props: {
        autogrow: true,
        minRows: 1,
        maxRows: 10,
      },
    })
    const textareaWrapper = wrapper.find('textarea')
    const textarea = textareaWrapper.element as HTMLTextAreaElement

    textarea.style.minBlockSize = '30px'
    textarea.style.maxBlockSize = '60px'
    Object.defineProperty(textarea, 'scrollHeight', { configurable: true, value: 80 })

    await textareaWrapper.setValue('line 1\nline 2\nline 3')
    await nextTick()

    expect(textarea.style.blockSize).toBe('60px')
    expect(textarea.style.overflowY).toBe('auto')
    expect(wrapper.find('.km-input').attributes('data-single-row')).toBeUndefined()
  })

  it('renders the label and links it to the input via for/id', () => {
    const wrapper = mount(KmInput, { props: { label: 'Email' } })
    const label = wrapper.find('label.km-input__label')
    const input = wrapper.find('[data-test="km-input"]')
    expect(label.text()).toBe('Email')
    expect(label.attributes('for')).toBe(input.attributes('id'))
  })

  it('emits update:modelValue and input on user typing', async () => {
    const Host = defineComponent({
      setup() {
        const value = ref('')
        return { value }
      },
      render() {
        return h(KmInput, {
          modelValue: this.value,
          'onUpdate:modelValue': (v: string | number | null) => (this.value = v == null ? '' : String(v)),
        })
      },
    })
    const wrapper = mount(Host)
    await wrapper.find('input').setValue('hello')
    expect((wrapper.vm as unknown as { value: string }).value).toBe('hello')
  })

  it('forwards prefix / suffix as separate affix spans', () => {
    const wrapper = mount(KmInput, { props: { prefix: '$', suffix: 'USD' } })
    const affixes = wrapper.findAll('.km-input__affix')
    expect(affixes).toHaveLength(2)
    expect(affixes[0].text()).toBe('$')
    expect(affixes[1].text()).toBe('USD')
  })

  it('wraps append slot content and marks the control as append-bearing', () => {
    const wrapper = mount(KmInput, {
      slots: {
        append: '<button type="button">Send</button>',
      },
    })

    expect(wrapper.find('.km-input').attributes('data-append')).toBe('true')
    expect(wrapper.find('.km-input__append button').text()).toBe('Send')
  })

  it('shows clear button when clearable + value present, and clears on click', async () => {
    const Host = defineComponent({
      setup() {
        const value = ref('hello')
        return { value }
      },
      render() {
        return h(KmInput, {
          clearable: true,
          modelValue: this.value,
          'onUpdate:modelValue': (v: string | number | null) => (this.value = v == null ? '' : String(v)),
        })
      },
    })
    const wrapper = mount(Host)
    const clearBtn = wrapper.find('[data-test="km-input-clear"]')
    expect(clearBtn.exists()).toBe(true)
    await clearBtn.trigger('click')
    expect((wrapper.vm as unknown as { value: string }).value).toBe('')
  })

  it('does not show clear button when value is empty', () => {
    const wrapper = mount(KmInput, { props: { clearable: true, modelValue: '' } })
    expect(wrapper.find('[data-test="km-input-clear"]').exists()).toBe(false)
  })

  it('reflects errorMessage as aria-invalid + visible error text', () => {
    const wrapper = mount(KmInput, { props: { errorMessage: 'Required' } })
    expect(wrapper.find('[data-test="km-input"]').attributes('aria-invalid')).toBe('true')
    expect(wrapper.text()).toContain('Required')
  })

  it('marks the wrapper with data-disabled when disabled', () => {
    const wrapper = mount(KmInput, { props: { disabled: true } })
    expect(wrapper.find('.km-input').attributes('data-disabled')).toBe('true')
  })

  it('passes dense to underlying DsInput as size="sm"', () => {
    const wrapper = mount(KmInput, { props: { dense: true } })
    expect(wrapper.find('[data-test="km-input"]').attributes('data-size')).toBe('sm')
  })
})
