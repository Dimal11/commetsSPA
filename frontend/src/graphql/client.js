import { ApolloClient, InMemoryCache } from '@apollo/client/core';
import { createUploadLink } from 'apollo-upload-client';

const graphqlURL = (window.__CONFIG__?.GRAPHQL_URL || '/graphql/').replace(/\/?$/, '/');

export const CAPTCHA_URL = ((window.__CONFIG__?.CAPTCHA_URL) || '/api/captcha/').replace(/\/?$/, '/');

export const getCaptchaImageUrl = () => `${CAPTCHA_URL}image?ts=${Date.now()}`;
export const refreshCaptcha = () => fetch(`${CAPTCHA_URL}refresh`, {
  method: 'POST',
  credentials: 'include',
});
export const verifyCaptcha = (value) => fetch(`${CAPTCHA_URL}verify`, {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ value }),
});

const link = createUploadLink({
  uri: graphqlURL,
  fetchOptions: { credentials: 'include' },
});

export default new ApolloClient({
  link,
  cache: new InMemoryCache(),
  connectToDevTools: import.meta.env.DEV,
});
