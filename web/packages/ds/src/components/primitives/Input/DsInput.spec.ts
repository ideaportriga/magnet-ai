import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, ref } from 'vue'
import DsInput from './DsInput.vue'

describe('DsInput', () => {
  it('renders an <input type="text"> by default', () => {
    const wrapper = mount(DsInput)
    expect(wrapper.element.tagName).toBe('INPUT')
    expect(wrapper.attributes('type')).toBe('text')
    expect(wrapper.attributes('data-test')).toBe('ds-input')
  })

  it('honours `type` prop', () => {
    const wrapper = mount(DsInput, { props: { type: 'email' } })
    expect(wrapper.attributes('type')).toBe('email')
  })

  it('reflects size as data-size, defaulting to "md"', () => {
    expect(mount(DsInput).attributes('data-size')).toBe('md')
    expect(mount(DsInput, { props: { size: 'sm' } }).attributes('data-size')).toBe('sm')
    expect(mount(DsInput, { props: { size: 'lg' } }).attributes('data-size')).toBe('lg')
  })

  it('updates v-model on input', async () => {
    const Host = defineComponent({
      setup() {
        const value = ref('')
        return { value }
      },
      render() {
        return h(DsInput, { modelValue: this.value, 'onUpdate:modelValue': (v: string | number) => (this.value = String(v)) })
      },
    })
    const wrapper = mount(Host)
    const input = wrapper.find('input')
    await input.setValue('hello')
    expect((wrapper.vm as unknown as { value: string }).value).toBe('hello')
  })

  it('uses defaultValue when v-model is not supplied', () => {
    const wrapper = mount(DsInput, { props: { defaultValue: 'seed' } })
    expect((wrapper.element as HTMLInputElement).value).toBe('seed')
  })

  it('forwards aria-invalid attr to the underlying input', () => {
    const wrapper = mount(DsInput, { attrs: { 'aria-invalid': 'true' } })
    expect(wrapper.attributes('aria-invalid')).toBe('true')
  })

  it('forwards disabled attr to the underlying input', () => {
    const wrapper = mount(DsInput, { attrs: { disabled: '' } })
    expect((wrapper.element as HTMLInputElement).disabled).toBe(true)
  })
})
