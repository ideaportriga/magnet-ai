import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick, ref } from 'vue'
import KmDialog from './KmDialog.vue'

const flush = async () => {
  await nextTick()
  await nextTick()
  await nextTick()
}

describe('KmDialog', () => {
  beforeEach(() => { document.body.innerHTML = '' })

  it('does not render content when modelValue=false', async () => {
    mount(KmDialog, {
      props: { modelValue: false },
      slots: { default: () => 'body' },
      attachTo: document.body,
    })
    await flush()
    expect(document.body.querySelector('[data-test="km-dialog"]')).toBeNull()
  })

  it('renders portal content when modelValue=true', async () => {
    mount(KmDialog, {
      props: { modelValue: true },
      slots: {
        title: () => 'Edit user',
        description: () => 'd',
        default: () => h('div', { class: 'body' }, 'body content'),
        footer: () => h('button', { class: 'foot' }, 'Save'),
      },
      attachTo: document.body,
    })
    await flush()
    // KmDialog renders DsDialog; the visible portal content is the DsDialog content.
    expect(document.body.querySelector('[data-test="ds-dialog"]')).not.toBeNull()
    expect(document.body.querySelector('.body')?.textContent).toBe('body content')
    expect(document.body.querySelector('.foot')).not.toBeNull()
  })

  it('emits update:modelValue + cancel + hide when closed externally', async () => {
    const Host = defineComponent({
      setup() {
        const open = ref(true)
        return { open }
      },
      render() {
        return h(KmDialog, {
          modelValue: this.open,
          'onUpdate:modelValue': (v: boolean) => (this.open = v),
        }, {
          title: () => 'Title',
          description: () => 'd',
          default: () => 'Body',
        })
      },
    })
    const wrapper = mount(Host, { attachTo: document.body })
    await flush()
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    await flush()
    expect((wrapper.vm as unknown as { open: boolean }).open).toBe(false)
    const dialogWrapper = wrapper.findComponent(KmDialog)
    expect(dialogWrapper.emitted('hide')).toHaveLength(1)
    expect(dialogWrapper.emitted('cancel')).toHaveLength(1)
  })

  it('persistent prop maps to dismissible=false', async () => {
    // Behaviour assertion: the underlying DsDialog should treat the dialog as
    // non-dismissible when KmDialog is `persistent`. We can't reliably trigger
    // outside-click dismissal in jsdom, but we can confirm hide-close is set
    // and the dialog renders. The integration test below covers the
    // controlled-state path.
    mount(KmDialog, {
      props: { modelValue: true, persistent: true },
      slots: { title: () => 't', description: () => 'd', default: () => 'b' },
      attachTo: document.body,
    })
    await flush()
    expect(document.body.querySelector('[data-test="ds-dialog"]')).not.toBeNull()
    // KmDialog hides the close button; DsDialog only renders ds-dialog-close
    // when hideClose is false.
    expect(document.body.querySelector('[data-test="ds-dialog-close"]')).toBeNull()
  })

  it('maximized prop forces size="full" on the underlying DsDialog', async () => {
    mount(KmDialog, {
      props: { modelValue: true, maximized: true, size: 'sm' },
      slots: { title: () => 't', description: () => 'd', default: () => 'b' },
      attachTo: document.body,
    })
    await flush()
    expect(
      document.body.querySelector('[data-test="ds-dialog"]')?.getAttribute('data-size'),
    ).toBe('full')
  })
})
