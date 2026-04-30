import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick, ref } from 'vue'
import DsPopover from './DsPopover.vue'

const flush = async () => {
  await nextTick()
  await nextTick()
  await nextTick()
}

describe('DsPopover', () => {
  beforeEach(() => { document.body.innerHTML = '' })

  it('does not render content when closed', async () => {
    mount(DsPopover, {
      props: { open: false },
      slots: {
        trigger: () => h('button', { id: 'trigger' }, 'Open'),
        default: () => h('div', { class: 'popover-body' }, 'Body'),
      },
      attachTo: document.body,
    })
    await flush()
    expect(document.body.querySelector('[data-test="ds-popover"]')).toBeNull()
  })

  it('renders portal content when open', async () => {
    mount(DsPopover, {
      props: { open: true },
      slots: {
        trigger: () => h('button', { id: 'trigger' }, 'Open'),
        default: () => h('div', { class: 'popover-body' }, 'Body'),
      },
      attachTo: document.body,
    })
    await flush()
    expect(document.body.querySelector('[data-test="ds-popover"]')).not.toBeNull()
    expect(document.body.querySelector('.popover-body')?.textContent).toBe('Body')
  })

  it('emits update:open when controlled state changes externally', async () => {
    const Host = defineComponent({
      setup() {
        const open = ref(true)
        return { open }
      },
      render() {
        return h(DsPopover, {
          open: this.open,
          'onUpdate:open': (v: boolean) => (this.open = v),
        }, {
          trigger: () => h('button', 'Open'),
          default: () => h('div', { class: 'body' }, 'Body'),
        })
      },
    })
    const wrapper = mount(Host, { attachTo: document.body })
    await flush()
    expect(document.body.querySelector('.body')).not.toBeNull()
    // Pressing Esc closes the popover via Reka's dismiss layer.
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    await flush()
    expect((wrapper.vm as unknown as { open: boolean }).open).toBe(false)
  })

  it('forwards width as inline-size on the content', async () => {
    mount(DsPopover, {
      props: { open: true, width: 320 },
      slots: {
        trigger: () => h('button', 'Open'),
        default: () => h('div', 'Body'),
      },
      attachTo: document.body,
    })
    await flush()
    const content = document.body.querySelector('[data-test="ds-popover"]') as HTMLElement
    expect(content?.style.inlineSize).toBe('320px')
  })
})
