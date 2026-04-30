import { afterEach } from 'vitest'

const noop = () => undefined

/**
 * jsdom doesn't ship with these APIs that Reka / Radix-style primitives rely on.
 * Polyfill before any component mounts.
 */

if (!('PointerEvent' in globalThis)) {
  // jsdom hasn't shipped a PointerEvent yet — borrow MouseEvent.
  // @ts-expect-error: shim
  globalThis.PointerEvent = class PointerEvent extends MouseEvent {
    pointerId = 1
    pointerType = 'mouse'
  }
}

if (!HTMLElement.prototype.hasPointerCapture) {
  HTMLElement.prototype.hasPointerCapture = () => false
}
if (!HTMLElement.prototype.setPointerCapture) {
  HTMLElement.prototype.setPointerCapture = () => undefined
}
if (!HTMLElement.prototype.releasePointerCapture) {
  HTMLElement.prototype.releasePointerCapture = () => undefined
}
if (!HTMLElement.prototype.scrollIntoView) {
  HTMLElement.prototype.scrollIntoView = () => undefined
}

if (!globalThis.ResizeObserver) {
  // @ts-expect-error: shim
  globalThis.ResizeObserver = class ResizeObserver {
    observe = noop
    unobserve = noop
    disconnect = noop
  }
}

if (!globalThis.IntersectionObserver) {
  // @ts-expect-error: shim
  globalThis.IntersectionObserver = class IntersectionObserver {
    observe = noop
    unobserve = noop
    disconnect = noop
    takeRecords() { return [] }
  }
}

if (!globalThis.DOMRect) {
  // @ts-expect-error: shim
  globalThis.DOMRect = class DOMRect {
    constructor(public x = 0, public y = 0, public width = 0, public height = 0) {}
    static fromRect(r?: { x: number; y: number; width: number; height: number }) {
      return new DOMRect(r?.x, r?.y, r?.width, r?.height)
    }
    get top() { return this.y }
    get left() { return this.x }
    get right() { return this.x + this.width }
    get bottom() { return this.y + this.height }
    toJSON() { return { ...this } }
  }
}

afterEach(() => {
  document.body.innerHTML = ''
})
