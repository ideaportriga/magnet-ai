import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick, ref } from 'vue'
import KmSelect from './KmSelect.vue'

const flush = async () => {
  await nextTick()
  await nextTick()
  await nextTick()
}

describe('KmSelect', () => {
  it('keeps the dropdown search field empty when the selected value is a system name', async () => {
    const Host = defineComponent({
      setup() {
        const value = ref('BEELINE_GPT_OSS_120B')
        return { value }
      },
      render() {
        return h(KmSelect, {
          modelValue: this.value,
          options: [
            {
              display_name: 'Beeline: gpt-oss-120b',
              system_name: 'BEELINE_GPT_OSS_120B',
            },
          ],
          optionLabel: 'display_name',
          optionValue: 'system_name',
          emitValue: true,
          hasDropdownSearch: true,
          'onUpdate:modelValue': (next: unknown) => { this.value = String(next ?? '') },
        })
      },
    })

    const wrapper = mount(Host, { attachTo: document.body })
    await wrapper.find('[data-test="km-select"]').trigger('click')
    await flush()

    const searchInput = document.body.querySelector('.km-select__search-input') as HTMLInputElement | null
    expect(searchInput).not.toBeNull()
    expect(searchInput?.value).toBe('')
    expect(document.body.textContent).toContain('Beeline: gpt-oss-120b')
    expect(document.body.textContent).not.toContain('No options available')
  })
})