import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, ref } from 'vue'
import DsTextarea from './DsTextarea.vue'

describe('DsTextarea', () => {
  it('renders a <textarea> with the data-test hook', () => {
    const wrapper = mount(DsTextarea)
    expect(wrapper.element.tagName).toBe('TEXTAREA')
    expect(wrapper.attributes('data-test')).toBe('ds-textarea')
  })

  it('updates v-model on input', async () => {
    const Host = defineComponent({
      setup() {
        const value = ref('')
        return { value }
      },
      render() {
        return h(DsTextarea, {
          modelValue: this.value,
          'onUpdate:modelValue': (v: string | number) => (this.value = String(v)),
        })
      },
    })
    const wrapper = mount(Host)
    await wrapper.find('textarea').setValue('multi\nline')
    expect((wrapper.vm as unknown as { value: string }).value).toBe('multi\nline')
  })

  it('respects defaultValue', () => {
    const wrapper = mount(DsTextarea, { props: { defaultValue: 'seed' } })
    expect((wrapper.element as HTMLTextAreaElement).value).toBe('seed')
  })

  it('forwards aria-invalid and disabled to the underlying textarea', () => {
    const wrapper = mount(DsTextarea, { attrs: { 'aria-invalid': 'true', disabled: '' } })
    expect(wrapper.attributes('aria-invalid')).toBe('true')
    expect((wrapper.element as HTMLTextAreaElement).disabled).toBe(true)
  })
})
