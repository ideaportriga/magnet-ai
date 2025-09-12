const tabTypes = [
  {
    label: 'Tab Group',
    val: 'Group',
  },
  {
    label: 'RAG Tool',
    val: 'RAG',
  },
  {
    label: 'Retrieval Tool',
    val: 'Retrieval',
  },
  {
    label: 'Custom',
    val: 'Custom',
  },
  {
    label: 'Agent',
    val: 'Agent',
  },
]

function getTabByVal(val) {
  return tabTypes.find((tab) => tab.val === val)
}

export default tabTypes
export { getTabByVal }
