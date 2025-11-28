import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

const basePath = process.env.WEB_BASE_PATH || "/"
const helpPath = process.env.WEB_HELP_PATH || ""

const base = `${basePath}${helpPath}`


//  https:vitepress.dev/reference/site-config
export default withMermaid(defineConfig({
  title: "Magnet AI",
  description: "Magnet AI",
  head: [
    ['link', { rel: 'icon', href: `${base}logo.svg`, type: 'image/svg+xml' }]
  ],
  themeConfig: {
    logo: '/logo.svg',
    //  https:vitepress.dev/reference/default-theme-config
    socialLinks: [
      { icon: 'github', link: 'https:github.com/vuejs/vitepress' }
    ],
    footer: {
      copyright: 'Copyright © 2025 Ideaport Riga AS',
    }

  },
  base,
  locales: {
    root: {
      label: 'English',
      lang: 'en',
      link: "/docs/en/",
      title: "Magnet AI",
      description: "Magnet AI",
      themeConfig: {
        nav: [
          { text: 'Home', link: '/docs/en/' },
          { text: 'Quickstarts', link: '/docs/en/quickstarts/introduction/what-is-magnet-ai' },
          { text: 'Admin Guide', link: '/docs/en/admin/connect/models/overview' },
          { text: 'Developer Guide', link: '/docs/en/developers/overview' },
        ],
        sidebar: {
          '/docs/en/quickstarts/': [
            {
              text: 'Introduction',

              items: [
                { text: 'What is Magnet AI', link: '/docs/en/quickstarts/introduction/what-is-magnet-ai' },
                { text: 'Use cases', link: '/docs/en/quickstarts/introduction/use-cases' },
                // { text: 'Demo video', link: '/docs/en/quickstarts/introduction/demo-video' },
                // { text: 'Playground', link: '/docs/en/quickstarts/introduction/playground' },
              ]
            },
            {
              text: 'Quickstarts',

              items: [
                {
                  text: 'Prompt Templates',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/quickstarts/prompt-templates/overview' },
                    { text: 'Configuration steps', link: '/docs/en/quickstarts/prompt-templates/configuration-steps' },
                    { text: 'How to use', link: '/docs/en/quickstarts/prompt-templates/how-to-use' },
                  ]
                },
                {
                  text: 'RAG Tools',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/quickstarts/rag-tools/overview' },
                    { text: 'Configuration steps', link: '/docs/en/quickstarts/rag-tools/configuration-steps' },
                    { text: 'How to use', link: '/docs/en/quickstarts/rag-tools/how-to-use' },
                  ]
                },
                {
                  text: 'Retrieval Tools',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/quickstarts/retrieval-tools/overview' },
                    { text: 'Configuration steps', link: '/docs/en/quickstarts/retrieval-tools/configuration-steps' },
                    { text: 'How to use', link: '/docs/en/quickstarts/retrieval-tools/how-to-use' },
                  ]
                },
                {
                  text: 'Agents',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/quickstarts/agents/overview' },
                    { text: 'Building blocks', link: '/docs/en/quickstarts/agents/building-blocks' },
                    { text: 'Configuration steps', link: '/docs/en/quickstarts/agents/configuration-steps' },
                    { text: 'API Tools', link: '/docs/en/quickstarts/agents/api-tools' },
                  ]
                },
                {
                  text: 'Variants',
                  collapsed: true,
                  items: [
                    { text: 'Using variants', link: '/docs/en/quickstarts/variants/using-variants' },
                  ]
                },
                {
                  text: 'AI Apps',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/quickstarts/ai-apps/overview' },
                    { text: 'Configuration steps', link: '/docs/en/quickstarts/ai-apps/configuration-steps' },
                  ]
                },
                {
                  text: 'Evaluations',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/quickstarts/evaluations/overview' },
                    { text: 'Configuration steps', link: '/docs/en/quickstarts/evaluations/configuration-steps' },
                  ]
                },
                {
                  text: 'Usage dashboards',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/quickstarts/usage-dashboards/overview' },
                    { text: 'RAG Queries', link: '/docs/en/quickstarts/usage-dashboards/rag-tools' },
                    { text: 'Agent Conversations', link: '/docs/en/quickstarts/usage-dashboards/agent-conversations' },
                    { text: 'LLM Calls', link: '/docs/en/quickstarts/usage-dashboards/llm-calls' },
                  ]
                },
              ]
            },
            {
              text: "How-to's",
              items: [
                {
                  text: 'How to Build a Q&A Agent',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/quickstarts/how-tos/build-qa-agent/overview' },
                    { text: 'Video Tutorial', link: '/docs/en/quickstarts/how-tos/build-qa-agent/demo-video' },
                    { text: 'Step-by-step instructions', link: '/docs/en/quickstarts/how-tos/build-qa-agent/step-by-step' },
                  ]
                }
              ]
            }
          ],
          '/docs/en/admin/': [
            {
              text: 'Connect',
              items: [
                {
                  text: 'Models',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/admin/connect/models/overview' },
                    { text: 'Adding Models', link: '/docs/en/admin/connect/models/adding-models' },
                    { text: 'Model Providers', link: '/docs/en/admin/connect/models/model-providers' },
                    { text: 'Model Configuration', link: '/docs/en/admin/connect/models/model-configuration' },
                  ]
                },
                {
                  text: 'Knowledge Sources',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/admin/connect/knowledge-sources/overview' },
                    { text: 'Knowledge Sources types', link: '/docs/en/admin/connect/knowledge-sources/types' },
                    { text: 'Knowledge Source settings', link: '/docs/en/admin/connect/knowledge-sources/settings' },
                  ]
                },
                {
                  text: 'API Tools',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/admin/connect/api-tools/overview' },
                    { text: 'Configuration', link: '/docs/en/admin/connect/api-tools/configuration' },
                  ]
                }
              ]
            },
            {
              text: 'Configure',
              items: [
                { text: 'Common tasks', link: '/docs/en/admin/configure/common-tasks' },
                {
                  text: 'Prompt Templates',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/admin/configure/prompt-templates/overview' },
                    { text: 'Configuration', link: '/docs/en/admin/configure/prompt-templates/configuration' },
                    { text: 'Default Prompt Templates', link: '/docs/en/admin/configure/prompt-templates/default' },
                  ]
                },
                {
                  text: 'RAG Tools',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/admin/configure/rag-tools/overview' },
                    { text: 'Configuration', link: '/docs/en/admin/configure/rag-tools/configuration' },
                  ]
                },
                {
                  text: 'Retrieval Tools',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/admin/configure/retrieval-tools/overview' },
                    { text: 'Configuration', link: '/docs/en/admin/configure/retrieval-tools/configuration' },
                  ]
                },
                {
                  text: 'Agents',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/docs/en/admin/configure/agents/overview' },
                    { text: 'Topics and Actions Overview', link: '/docs/en/admin/configure/agents/topics-actions' },
                    { text: 'Configuring Topics and Actions', link: '/docs/en/admin/configure/agents/configuration-topics' },
                    { text: 'Configuring Channels', link: '/docs/en/admin/configure/agents/configuration-channels' },
                    { text: 'Other Settings', link: '/docs/en/admin/configure/agents/configuration-other' },
                  ]
                }
              ]
            }
          ],
          '/docs/en/developers/': [
            {
              text: 'General',
              items: [
                { text: 'Overview', link: '/docs/en/developers/overview' },
              ]
            },
            {
              text: 'Development Setup',
              items: [
                { text: 'Getting Started', link: '/docs/en/developers/setup/getting-started' },
                { text: 'Local Development', link: '/docs/en/developers/setup/local-development' },
                { text: 'Testing', link: '/docs/en/developers/setup/testing' },
                { text: 'Deployment', link: '/docs/en/developers/setup/deployment' },
              ]
            },

            {
              text: 'Guides',
              items: [
                { text: 'Git Workflow', link: '/docs/en/developers/guides/git-workflow' },
                { text: 'Logging', link: '/docs/en/developers/guides/logging' },
                { text: 'Security', link: '/docs/en/developers/guides/security' },
                { text: 'API Structure', link: '/docs/en/developers/guides/api-structure' },
                { text: 'Plugins Guide', link: '/docs/en/developers/guides/plugins' },
              ]
            },
            {
              text: 'Architecture',
              items: [
                { text: 'System Architecture', link: '/docs/en/developers/architecture/system-architecture' },
                { text: 'Backend Architecture', link: '/docs/en/developers/architecture/backend' },
                { text: 'Frontend Architecture', link: '/docs/en/developers/architecture/frontend' },
                { text: 'Database Schema', link: '/docs/en/developers/architecture/database' },
              ]
            },
            {
              text: 'API Reference',
              items: [
                { text: 'REST API', link: '/docs/en/developers/api/rest-api' },
                { text: 'Authentication', link: '/docs/en/developers/api/authentication' },
                { text: 'API Endpoints', link: '/docs/en/developers/api/endpoints' },
              ]
            },
            {
              text: 'Plugin Development',
              items: [
                { text: 'Plugin System', link: '/docs/en/developers/plugins/plugin-system' },
                { text: 'Creating Plugins', link: '/docs/en/developers/plugins/creating-plugins' },
                { text: 'Plugin API', link: '/docs/en/developers/plugins/plugin-api' },
                { text: 'Plugin Examples', link: '/docs/en/developers/plugins/examples' },
              ]
            },
          ],
        },

        socialLinks: [
          { icon: 'github', link: 'https:github.com/vuejs/vitepress' }
        ]
      }
    },
    // lv: {
    //   label: 'Latviešu',
    //   lang: 'lv',
    //   title: "Magnet AI",
    //   link: "/docs/lv/",
    //   description: "Magnet AI",
    //   themeConfig: {
    //     nav: [
    //       { text: 'Sākums', link: '/docs/lv/' },
    //       { text: 'Ātrā sākšana', link: '/docs/lv/quickstarts/introduction/what-is-magnet-ai' },
    //       { text: 'Administrēšanas rokasgrāmata', link: '/docs/lv/admin/connect/models/overview' },
    //     ],
    //     sidebar: {
    //       '/docs/lv/quickstarts/': [
    //         {
    //           text: 'Ievads',
    //           items: [
    //             { text: 'Kas ir Magnet AI', link: '/docs/lv/quickstarts/introduction/what-is-magnet-ai' },
    //             { text: 'Lietojuma gadījumi', link: '/docs/lv/quickstarts/introduction/use-cases' },
    //             { text: 'Demo video', link: '/docs/lv/quickstarts/introduction/demo-video' },
    //             { text: 'Playground', link: '/docs/lv/quickstarts/introduction/playground' },
    //           ]
    //         },
    //         {
    //           text: 'Ātrā sākšana',
    //           items: [
    //             {
    //               text: 'Prompt veidnes',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Pārskats', link: '/docs/lv/quickstarts/prompt-templates/overview' },
    //                 { text: 'Konfigurācijas soļi', link: '/docs/lv/quickstarts/prompt-templates/configuration-steps' },
    //                 { text: 'Kā lietot', link: '/docs/lv/quickstarts/prompt-templates/how-to-use' },
    //               ]
    //             },
    //             {
    //               text: 'RAG rīki',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Pārskats', link: '/docs/lv/quickstarts/rag-tools/overview' },
    //                 { text: 'Konfigurācijas soļi', link: '/docs/lv/quickstarts/rag-tools/configuration-steps' },
    //                 { text: 'Kā lietot', link: '/docs/lv/quickstarts/rag-tools/how-to-use' },
    //               ]
    //             },
    //             {
    //               text: 'Atsaukšanas rīki',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Pārskats', link: '/docs/lv/quickstarts/retrieval-tools/overview' },
    //                 { text: 'Konfigurācijas soļi', link: '/docs/lv/quickstarts/retrieval-tools/configuration-steps' },
    //                 { text: 'Kā lietot', link: '/docs/lv/quickstarts/retrieval-tools/how-to-use' },
    //               ]
    //             },
    //             {
    //               text: 'Aģenti',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Pārskats', link: '/docs/lv/quickstarts/agents/overview' },
    //                 { text: 'Būvbloki', link: '/docs/lv/quickstarts/agents/building-blocks' },
    //                 { text: 'Konfigurācijas soļi', link: '/docs/lv/quickstarts/agents/configuration-steps' },
    //                 { text: 'API rīki', link: '/docs/lv/quickstarts/agents/api-tools' },
    //                 { text: 'Kā lietot', link: '/docs/lv/quickstarts/agents/how-to-use' },
    //               ]
    //             },
    //             {
    //               text: 'Varianti',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Kā lietot variantus', link: '/docs/lv/quickstarts/variants/using-variants' },
    //               ]
    //             },
    //             {
    //               text: 'AI lietotnes',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Pārskats', link: '/docs/lv/quickstarts/ai-apps/overview' },
    //                 { text: 'Konfigurācijas soļi', link: '/docs/lv/quickstarts/ai-apps/configuration-steps' },
    //               ]
    //             },
    //             {
    //               text: 'Lietošanas paneļi',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Pārskats', link: '/docs/lv/quickstarts/usage-dashboards/overview' },
    //                 { text: 'RAG rīki', link: '/docs/lv/quickstarts/usage-dashboards/rag-tools' },
    //                 { text: 'Aģentu sarunas', link: '/docs/lv/quickstarts/usage-dashboards/agent-conversations' },
    //                 { text: 'LLM izsaukumi', link: '/docs/lv/quickstarts/usage-dashboards/llm-calls' },
    //               ]
    //             },
    //             {
    //               text: 'Novērtējumi',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Pārskats', link: '/docs/lv/quickstarts/evaluations/overview' },
    //                 { text: 'Konfigurācijas soļi', link: '/docs/lv/quickstarts/evaluations/configuration-steps' },
    //               ]
    //             },
    //           ]
    //         },
    //         {
    //           text: "Kā izdarīt",
    //           items: [
    //             {
    //               text: 'Kā izveidot J&A aģentu',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Pārskats', link: '/docs/lv/quickstarts/how-tos/build-qa-agent/overview' },
    //                 { text: 'Demo video', link: '/docs/lv/quickstarts/how-tos/build-qa-agent/demo-video' },
    //                 { text: 'Soli pa solim instrukcijas', link: '/docs/lv/quickstarts/how-tos/build-qa-agent/step-by-step' },
    //               ]
    //             }
    //           ]
    //         }
    //       ],
    //       '/docs/lv/admin/': [
    //         {
    //           text: 'Savienot',
    //           items: [
    //             {
    //               text: 'Modeļi',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Pārskats', link: '/docs/lv/admin/connect/models/overview' },
    //                 { text: 'Pievienot modeļus', link: '/docs/lv/admin/connect/models/adding-models' },
    //                 { text: 'Modeļu cenas', link: '/docs/lv/admin/connect/models/model-pricing' },
    //               ]
    //             },
    //             {
    //               text: 'Zināšanu avoti',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Pārskats', link: '/docs/lv/admin/connect/knowledge-sources/overview' },
    //                 { text: 'Pievienot zināšanu avotus', link: '/docs/lv/admin/connect/knowledge-sources/adding' },
    //               ]
    //             }
    //           ]
    //         },
    //         {
    //           text: 'Konfigurēt',
    //           items: [
    //             {
    //               text: 'Prompt veidnes',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Pārskats', link: '/docs/lv/admin/configure/prompt-templates/overview' },
    //                 { text: 'Konfigurācija', link: '/docs/lv/admin/configure/prompt-templates/configuration' },
    //                 { text: 'Noklusētās prompt veidnes', link: '/docs/lv/admin/configure/prompt-templates/default' },
    //               ]
    //             },
    //             {
    //               text: 'RAG rīki',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Pārskats', link: '/docs/lv/admin/configure/rag-tools/overview' },
    //                 { text: 'Konfigurācija', link: '/docs/lv/admin/configure/rag-tools/configuration' },
    //               ]
    //             },
    //             {
    //               text: 'Aģenti',
    //               collapsed: true,
    //               items: [
    //                 { text: 'Pārskats', link: '/docs/lv/admin/configure/agents/overview' },
    //                 { text: 'Tēmas un darbības', link: '/docs/lv/admin/configure/agents/topics-actions' },
    //                 { text: 'Cita konfigurācija', link: '/docs/lv/admin/configure/agents/other-configuration' },
    //               ]
    //             }
    //           ]
    //         }
    //       ]
    //     },
    //     socialLinks: [
    //       { icon: 'github', link: 'https:github.com/vuejs/vitepress' }
    //     ]
    //   }
    // }
  }
}))
