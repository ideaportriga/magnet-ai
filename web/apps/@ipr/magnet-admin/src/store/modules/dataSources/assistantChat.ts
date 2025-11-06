import { generateGetters } from '@/store/utils'

interface AssistantChatState {
  messageList: any[]
  messagesLoading: boolean
  draftMessage: string
  isTyping: boolean
  currentUser:
    | {
        name: string
        role: 'customer' | 'employee'
      }
    | {}
  currentConversation:
    | {
        conversationId: string
        caseId: string
      }
    | {}
  recomendedMessage: string
  assistantLoading: boolean
}

const state = (): AssistantChatState => ({
  messageList: [],
  messagesLoading: true,
  draftMessage: '',
  isTyping: false,
  currentUser: {},
  currentConversation: {},
  recomendedMessage: '',
  assistantLoading: false,
})

const [baseGetters] = generateGetters({
  state: state(),
  namespace: 'assistantChat',
})

const getters = {
  isTyping: (state) => state.isTyping,
  currentUser: (state) => state.currentUser,
  messageList: (state) => state.messageList,
  draftMessage: (state) => state.draftMessage,
  recomendedMessage: (state) => state.recomendedMessage,
  messagesLoading: (state) => state.messagesLoading,
  currentConversation: (state) => state.currentConversation,
  assistantLoading: (state) => state.assistantLoading,
}

const actions = {
  applyRecomendedMessage({ commit }, draftMessage) {
    commit('set', { draftMessage })
  },
  setMessageList({ commit, state }, payload) {
    commit('set', {
      messageList: payload.map((message) => ({ ...message, user: message.username === state.currentUser.name })),
      messagesLoading: false,
    })
  },
  addMessage({ commit, state }, payload) {
    commit('newMessage', payload)
  },
  reset({ commit }) {
    console.log('reset')
    commit('set', state())
  },
  set({ commit }, payload) {
    commit('set', payload)
  },
}
const mutations = {
  set(state, payload) {
    Object.entries(payload).forEach(([key, value]) => {
      state[key] = value
    })
  },
  newMessage(state, payload) {
    state.draftMessage = ''
    state.recomendedMessage = ''
    state.messageList.push(payload)
  },
}

const assistantChatStore = {
  namespaced: true,
  getters,
  mutations,
  actions,
  state,
}
export default assistantChatStore
