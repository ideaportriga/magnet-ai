/**
 * Side-effect re-export so `@ds/tokens` resolves through the Nx tsconfig
 * paths plugin (which only handles TS/JS) and Vite's CSS pipeline takes
 * over for the actual stylesheet.
 */
import './index.css'
