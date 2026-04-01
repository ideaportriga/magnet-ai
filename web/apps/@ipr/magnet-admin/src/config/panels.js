// sourceSystem is set via URL query param, read from route at runtime
const urlParams = new URLSearchParams(window.location.hash?.split('?')[1] || '')
const system = urlParams.get('sourceSystem') || ''
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
