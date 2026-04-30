import { describe, it, expect, beforeEach } from 'vitest'
import {
  pushToast,
  dismissToast,
  clearToasts,
  toastQueue,
} from './toastStore'

describe('toastStore', () => {
  beforeEach(() => clearToasts())

  it('pushes a toast and exposes it via the queue', () => {
    const handle = pushToast({ tone: 'success', message: 'Saved' })
    expect(toastQueue.items).toHaveLength(1)
    expect(toastQueue.items[0].id).toBe(handle.id)
    expect(toastQueue.items[0].message).toBe('Saved')
    expect(toastQueue.items[0].tone).toBe('success')
  })

  it('assigns the default duration per tone', () => {
    pushToast({ tone: 'success', message: 'a' })
    pushToast({ tone: 'error', message: 'b' })
    pushToast({ tone: 'confirm', message: 'c' })
    expect(toastQueue.items[0].duration).toBe(2500)
    expect(toastQueue.items[1].duration).toBe(5000)
    expect(toastQueue.items[2].duration).toBe(0) // confirm = sticky
  })

  it('respects an explicit duration override', () => {
    pushToast({ tone: 'success', message: 'a', duration: 100 })
    expect(toastQueue.items[0].duration).toBe(100)
  })

  it('dismisses a toast by handle', () => {
    const handle = pushToast({ tone: 'info', message: 'a' })
    expect(toastQueue.items).toHaveLength(1)
    handle.dismiss()
    expect(toastQueue.items).toHaveLength(0)
  })

  it('invokes onDismiss when removed', () => {
    let calls = 0
    const handle = pushToast({
      tone: 'info',
      message: 'a',
      onDismiss: () => { calls += 1 },
    })
    handle.dismiss()
    expect(calls).toBe(1)
  })

  it('dismissToast on an unknown id is a no-op', () => {
    pushToast({ tone: 'info', message: 'a' })
    dismissToast('nonexistent')
    expect(toastQueue.items).toHaveLength(1)
  })

  it('clearToasts empties the queue and runs onDismiss for each', () => {
    let calls = 0
    pushToast({ tone: 'info', message: 'a', onDismiss: () => { calls += 1 } })
    pushToast({ tone: 'info', message: 'b', onDismiss: () => { calls += 1 } })
    clearToasts()
    expect(toastQueue.items).toHaveLength(0)
    expect(calls).toBe(2)
  })

  it('produces unique ids for concurrent pushes', () => {
    const ids = new Set<string>()
    for (let i = 0; i < 50; i += 1) {
      ids.add(pushToast({ tone: 'info', message: `msg-${i}` }).id)
    }
    expect(ids.size).toBe(50)
  })
})
