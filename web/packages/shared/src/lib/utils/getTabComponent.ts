export default (tab) => {
  if (tab?.tab_type === 'Group') {
    return {
      name: 'multi-tab',
      props: {
        children: tab?.children,
      },
    }
  }
  if (tab?.tab_type === 'RAG') {
    return {
      name: 'search-tab',
      props: {
        rag_code: tab?.config?.rag_tool,
      },
    }
  }

  if (tab?.tab_type === 'Retrieval') {
    return {
      name: 'retrieval-tab',
      props: {
        retrieval_tool: tab?.config?.retrieval_tool,
      },
    }
  }

  if (tab?.tab_type === 'Agent') {
    return {
      name: 'agent-tab',
      props: {
        agent: tab?.config?.agent,
        tab: tab,
      },
    }
  }

  if (tab?.tab_type === 'Custom') {
    const jsonString = tab?.config?.jsonString

    try {
      const jsObject = JSON.parse(jsonString)
      const { component, ...props } = jsObject

      return {
        name: component,
        props,
      }
    } catch (error) {
      console.error('Invalid JSON string:', error.message)
    }
  }
}
