export default [
  {
    name: 'MaternityRules',
    msg: 'start',
    speaker: 'UserInput',
  },
  {
    name: 'PowerOutageRules',
    msg: 'start',
    speaker: 'UserInput',
  },
  {
    name: 'EmailAgent',
    msg: JSON.stringify({
      email_id: '12',
      source_system: 'Mock',
    }),
    views: [
      {
        name: 'IPR Activity List View Email',
        entity: 'action',
        applet: 'IPR Activity List Applet With Navigation',
      },
      {
        name: 'IPR Activity Children View',
        entity: 'action',
        applet: 'IPR Activity Form Applet',
      },
      {
        name: 'All Inbound Item List View',
        entity: 'action',
        applet: 'Comm Inbound Item List Applet',
      },
      {
        name: 'Activity List View',
        entity: 'action',
        applet: 'Activity List Applet With Navigation',
      },
    ],
    description: 'Hi! By analyzing an email, I can detect the right scenario and generate a response for the customer.',
    label: 'Analyze Email',
    noRecordLabel: 'Please open or select an inbound email to start analysis...',
  },
  {
    name: 'EmailAgentSF',
    msg: JSON.stringify({
      email_id: '14',
      source_system: 'Mock',
    }),
    views: [],
    description: 'Hi! By analyzing an email, I can detect the right scenario and generate a response for the customer.',
    label: 'Analyze Email',
    noRecordLabel: 'Please open or select an inbound email to start analysis...',
  },
  {
    name: 'SRAgent',
    msg: JSON.stringify({
      id: 'SR_1',
      number: 'SR_NR_1',
      planner: {
        name: 'Martins Petters',
        email: 'm.p@test.com',
      },
      helpdesk: {
        name: 'Helpdesk',
        email: 'helpdesk@test.com',
      },
    }),
    views: [
      {
        name: 'All Service Request List View',
        entity: 'service',
        applet: 'Service Request List Applet',
      },
    ],
    description: 'Hi! By analyzing an service request, I can help with approval process.',
    label: 'Analyze Service Request',
    noRecordLabel: 'Please open or select an service request to start analysis...',
  },
]
