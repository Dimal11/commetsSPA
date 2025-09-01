import { ApolloClient, InMemoryCache } from '@apollo/client/core';
import { createUploadLink } from 'apollo-upload-client';

const backendBase =
  (window.__CONFIG__ && window.__CONFIG__.API_BASE) ||
  import.meta.env.VITE_API_BASE_URL ||
  '';

const graphqlURL =
  (window.__CONFIG__ && window.__CONFIG__.GRAPHQL_URL) ||
  (backendBase ? `${backendBase.replace(/\/$/, '')}/graphql/` : '/graphql/');


const link = createUploadLink({
  uri: graphqlURL,
  fetchOptions: { credentials: 'include' },
});

export default new ApolloClient({
  link,
  cache: new InMemoryCache(),
  connectToDevTools: import.meta.env.DEV,
});
