import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client/core'
import { createUploadLink } from 'apollo-upload-client'
import { GraphQLWsLink } from '@apollo/client/link/subscriptions'
import { createClient } from 'graphql-ws'
import { getMainDefinition } from '@apollo/client/utilities'

const API = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/,'')

const httpUri = API ? `${API}/graphql/` : '/graphql/'
const httpLink = createUploadLink({
  uri: httpUri,
  fetchOptions: { credentials: 'include' },
})

const wsUrl = API.startsWith('https')
  ? API.replace(/^https?/, 'wss') + '/graphql/'
  : API.replace(/^http/, 'ws') + '/graphql/'
const wsLink = new GraphQLWsLink(createClient({ url: wsUrl }))

const backendBase = window.__CONFIG__?.API_BASE || import.meta.env.VITE_API_BASE_URL || '';

const graphqlURL = window.__CONFIG__?.GRAPHQL_URL
  || (backendBase ? `${backendBase.replace(/\/$/, '')}/graphql` : '')
  || 'http://127.0.0.1:8000/graphql';

const link = createHttpLink({
  uri: graphqlURL.replace(/\/$/, ''),
  credentials: 'include',
});

export default new ApolloClient({
  link,
  cache: new InMemoryCache(),
  connectToDevTools: true,
});
