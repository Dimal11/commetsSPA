import { createApp } from 'vue'
import { DefaultApolloClient } from '@vue/apollo-composable'
import { apolloClient } from './graphql/client'
import App from './App.vue'
import './style.css'

createApp(App)
  .provide(DefaultApolloClient, apolloClient)
  .mount('#app')

