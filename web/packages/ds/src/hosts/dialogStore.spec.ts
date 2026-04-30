import { describe, it, expect } from 'vitest'
import { pushConfirm, settleConfirm, dialogQueue } from './dialogStore'

const flushMicrotasks = () => new Promise<void>((r) => queueMicrotask(() => r()))

describe('dialogStore', () => {
  it('queues a confirm dialog with open=true', () => {
    const promise = pushConfirm({ title: 'Delete user?' })
    expect(dialogQueue.items).toHaveLength(1)
    expect(dialogQueue.items[0].open).toBe(true)
    expect(dialogQueue.items[0].title).toBe('Delete user?')
    // Settle to avoid leaking a pending promise across tests.
    settleConfirm(dialogQueue.items[0].id, false)
    return promise
  })

  it('resolves true when confirmed', async () => {
    const promise = pushConfirm({ title: 'Confirm?' })
    const id = dialogQueue.items[dialogQueue.items.length - 1].id
    settleConfirm(id, true)
    await expect(promise).resolves.toBe(true)
  })

  it('resolves false when cancelled', async () => {
    const promise = pushConfirm({ title: 'Cancel test?' })
    const id = dialogQueue.items[dialogQueue.items.length - 1].id
    settleConfirm(id, false)
    await expect(promise).resolves.toBe(false)
  })

  it('removes the item from the queue after settling', async () => {
    const startCount = dialogQueue.items.length
    const promise = pushConfirm({ title: 'A' })
    expect(dialogQueue.items).toHaveLength(startCount + 1)
    const id = dialogQueue.items[dialogQueue.items.length - 1].id
    settleConfirm(id, false)
    await promise
    await flushMicrotasks()
    expect(dialogQueue.items.find((i) => i.id === id)).toBeUndefined()
  })

  it('settleConfirm on an unknown id is a no-op', () => {
    const before = dialogQueue.items.length
    settleConfirm('nonexistent', true)
    expect(dialogQueue.items).toHaveLength(before)
  })
})
