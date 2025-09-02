import { gql } from '@apollo/client/core';

export const COMMENTS_QUERY = gql`
  query Comments(
    $page: Int!
    $pageSize: Int!
    $orderField: OrderField!
    $desc: Boolean!
    $parentId: ID
  ) {
    comments(
      page: $page
      pageSize: $pageSize
      orderField: $orderField
      desc: $desc
      parentId: $parentId
    ) {
      count
      results {
        id
        textHtml
        createdAt
        repliesCount
        author {
          name
          email
          __typename
        }
        attachments {
          id
          url
          isImage
          contentType
          width
          height
          size
          __typename
        }
        __typename
      }
      __typename
    }
  }
`;

export const CREATE_COMMENT_MUTATION = gql`
  mutation Create($input: CreateCommentInput!) {
    createComment(input: $input) {
      id
      textHtml
      createdAt
      repliesCount
      author {
        name
        email
        __typename
      }
      attachments {
        id
        url
        isImage
        contentType
        width
        height
        size
        __typename
      }
      __typename
    }
  }
`;
