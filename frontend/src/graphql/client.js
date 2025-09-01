import { ApolloClient, InMemoryCache, HttpLink } from '@apollo/client/core'
import { createUploadLink } from 'apollo-upload-client'
import { GraphQLWsLink } from '@apollo/client/link/subscriptions'
import { createClient } from 'graphql-ws'
import { getMainDefinition } from '@apollo/client/utilities'

const API = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/,'')

const httpUri = API ? `${API}/graphql/` : '/graphql'
const httpLink = createUploadLink({
  uri: httpUri,
  fetchOptions: { credentials: 'include' },
})

const wsUrl = API.startsWith('https')
  ? API.replace(/^https?/, 'wss') + '/graphql'
  : API.replace(/^http/, 'ws') + '/graphql'
const wsLink = new GraphQLWsLink(createClient({ url: wsUrl }))

const link = new HttpLink({
  uri: '/graphql/',
  fetchOptions: { credentials: 'include' },
});

export const apolloClient = new ApolloClient({
  link,
  cache: new InMemoryCache(),
})
