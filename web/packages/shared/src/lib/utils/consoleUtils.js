const noConsoleDebug = process.env.VUE_APP_NO_CONSOLE_DEBUG === 'true'

export let debug = console.debug

if (noConsoleDebug) {
  debug = () => {}
}
