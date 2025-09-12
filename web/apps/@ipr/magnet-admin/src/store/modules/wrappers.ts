import { chromaWrapperGetters } from '@/store/modules/dataSources/chroma'
import { strapiWrapperGetters } from '@/store/modules/dataSources/strapi'

export default {
  state: {},
  getters: {
    ...strapiWrapperGetters,
    ...chromaWrapperGetters,
  },
}
