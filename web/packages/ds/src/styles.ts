/**
 * Convenience entry point that pulls the @ds layers that are SAFE to load
 * alongside Quasar (tokens + composition + utilities).
 *
 * The reset is intentionally NOT included here: it would fight Quasar's own
 * `quasar/src/css/index.sass`. Apps that no longer load Quasar import the
 * reset explicitly:
 *
 *   import '@ds/styles'
 *   import '@ds/reset'
 *
 * Or use the layers individually:
 *
 *   import '@ds/tokens'
 *   import '@ds/composition'
 *   import '@ds/utilities'
 */

import './tokens/index.css'
import './composition/index.css'
import './utilities/index.css'
