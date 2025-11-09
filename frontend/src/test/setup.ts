import { expect, afterEach, beforeAll } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

expect.extend(matchers)

// Mock scrollIntoView for JSDOM
beforeAll(() => {
  Element.prototype.scrollIntoView = () => {}
})

afterEach(() => {
  cleanup()
})
