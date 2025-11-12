import { nxE2EPreset } from '@nx/cypress/plugins/cypress-preset'
import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    ...nxE2EPreset(__filename, {
      cypressDir: 'cypress',
      webServerCommands: {
        default: 'nx run magnet-admin:dev',
        production: 'nx run magnet-admin:preview',
      },
    }),
    baseUrl: 'https://localhost:7000',
  },
})
