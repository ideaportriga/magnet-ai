import { describe, it, expect, beforeEach } from 'vitest'
import { showLoading, clearLoading, loadingState } from './loadingStore'

describe('loadingStore', () => {
  beforeEach(() => clearLoading())

  it('starts hidden', () => {
    expect(loadingState.pending).toBe(0)
    expect(loadingState.message).toBeNull()
  })

  it('increments pending and exposes the message', () => {
    showLoading({ message: 'Saving…' })
    expect(loadingState.pending).toBe(1)
    expect(loadingState.message).toBe('Saving…')
  })

  it('decrements only when the returned hide() is called', () => {
    const hide = showLoading()
    expect(loadingState.pending).toBe(1)
    hide()
    expect(loadingState.pending).toBe(0)
  })

  it('hide() is idempotent — extra calls do not over-decrement', () => {
    const hide = showLoading()
    showLoading()
    hide()
    hide()
    hide()
    expect(loadingState.pending).toBe(1)
  })

  it('keeps the overlay visible while any caller holds it', () => {
    const hide1 = showLoading()
    const hide2 = showLoading()
    hide1()
    expect(loadingState.pending).toBe(1)
    hide2()
    expect(loadingState.pending).toBe(0)
  })

  it('clearLoading force-clears even with pending callers', () => {
    showLoading()
    showLoading()
    clearLoading()
    expect(loadingState.pending).toBe(0)
    expect(loadingState.message).toBeNull()
  })

  it('clears the message once the last caller hides', () => {
    showLoading({ message: 'one' })
    const hide = showLoading()
    expect(loadingState.message).toBe('one')
    clearLoading()
    showLoading({ message: 'two' })
    showLoading()
    hide()
    expect(loadingState.message).toBe('two')
  })
})
