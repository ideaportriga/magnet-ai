import store from '@/store/index'
const system = store.getters.sourceSystem
console.log(`Panels for ${system || 'standalone'}`)
export default [
  {
    name: 'qa',
    label: 'Q & A',
    component: 'search-tab',
  },
  {
    name: 'email_agent',
    label: 'Email Agent',
    component: system === 'Salesforce' ? 'agent-tab' : 'conversation-tab-email-agent',
  },
  {
    name: 'sr_agent',
    label: 'SR Approval Agent',
    component: 'conversation-tab-approval-agent',
  },
  {
    name: 'conversation',
    label: 'Chat',
    component: 'conversation-tab',
  },
]
