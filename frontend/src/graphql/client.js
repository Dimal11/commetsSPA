import { ApolloClient, InMemoryCache } from '@apollo/client/core';
import { createUploadLink } from 'apollo-upload-client';

const backendBase = ((window.__CONFIG__?.API_BASE || import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

const graphqlURL = window.__CONFIG__?.GRAPHQL_URL || (backendBase ? `${backendBase}/graphql/` : '/graphql/')

const link = createUploadLink({
  uri: graphqlURL,
  credentials: 'include',
  fetchOptions: { credentials: 'include' },
});

export default new ApolloClient({
  link,
  cache: new InMemoryCache(),
  connectToDevTools: import.meta.env.DEV,
});
