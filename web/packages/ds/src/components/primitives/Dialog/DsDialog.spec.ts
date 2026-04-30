import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, ref, nextTick } from 'vue'
import DsDialog from './DsDialog.vue'

const flush = async () => {
  await nextTick()
  await nextTick()
  await nextTick()
}

describe('DsDialog', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  it('renders nothing in DOM when open=false', async () => {
    mount(DsDialog, {
      props: { open: false },
      slots: {
        title: () => 'Title',
        default: () => 'Body content',
      },
      attachTo: document.body,
    })
    await flush()
    expect(document.body.querySelector('[data-test="ds-dialog"]')).toBeNull()
  })

  it('renders portal content when open=true', async () => {
    mount(DsDialog, {
      props: { open: true },
      slots: {
        title: () => 'Edit user',
        description: () => 'Update user fields',
        default: () => h('div', { class: 'body-marker' }, 'body'),
        footer: () => h('button', { class: 'footer-marker' }, 'Save'),
      },
      attachTo: document.body,
    })
    await flush()

    expect(document.body.querySelector('[data-test="ds-dialog"]')).not.toBeNull()
    expect(document.body.querySelector('[data-test="ds-dialog-overlay"]')).not.toBeNull()
    expect(document.body.querySelector('.body-marker')?.textContent).toBe('body')
    expect(document.body.querySelector('.footer-marker')).not.toBeNull()
  })

  it('renders an accessible title and description', async () => {
    mount(DsDialog, {
      props: { open: true },
      slots: {
        title: () => 'Edit user',
        description: () => 'Update user fields',
        default: () => 'body',
      },
      attachTo: document.body,
    })
    await flush()
    const dialog = document.body.querySelector('[role="dialog"]') as HTMLElement
    expect(dialog).not.toBeNull()
    expect(dialog.getAttribute('aria-labelledby')).toBeTruthy()
    expect(dialog.getAttribute('aria-describedby')).toBeTruthy()
  })

  it('shows close button by default and hides it with `hide-close`', async () => {
    const w1 = mount(DsDialog, {
      props: { open: true },
      slots: { title: () => 't', description: () => 'd', default: () => 'b' },
      attachTo: document.body,
    })
    await flush()
    expect(document.body.querySelector('[data-test="ds-dialog-close"]')).not.toBeNull()
    w1.unmount()
    document.body.innerHTML = ''

    mount(DsDialog, {
      props: { open: true, hideClose: true },
      slots: { title: () => 't', description: () => 'd', default: () => 'b' },
      attachTo: document.body,
    })
    await flush()
    expect(document.body.querySelector('[data-test="ds-dialog-close"]')).toBeNull()
  })

  it('reflects size as data-size', async () => {
    mount(DsDialog, {
      props: { open: true, size: 'lg' },
      slots: { title: () => 't', description: () => 'd', default: () => 'b' },
      attachTo: document.body,
    })
    await flush()
    const dialog = document.body.querySelector('[data-test="ds-dialog"]') as HTMLElement
    expect(dialog.getAttribute('data-size')).toBe('lg')
  })

  it('emits update:open when close button is clicked', async () => {
    const Host = defineComponent({
      setup() {
        const open = ref(true)
        return { open }
      },
      render() {
        return h(DsDialog, {
          open: this.open,
          'onUpdate:open': (v: boolean) => (this.open = v),
        }, {
          title: () => 'Title',
          description: () => 'd',
          default: () => 'Body',
        })
      },
    })
    const wrapper = mount(Host, { attachTo: document.body })
    await flush()
    const closeBtn = document.body.querySelector('[data-test="ds-dialog-close"]') as HTMLElement
    expect(closeBtn).not.toBeNull()
    closeBtn.click()
    await flush()
    expect((wrapper.vm as unknown as { open: boolean }).open).toBe(false)
  })
})
