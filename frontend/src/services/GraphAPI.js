import { ApolloClient, InMemoryCache, HttpLink, gql } from '@apollo/client';

export const client = new ApolloClient({
  link: new HttpLink({ uri: 'http://localhost:8000/graphql' }),
  cache: new InMemoryCache(),
});

export const RUN_PIPELINE = gql`
  mutation RunPipeline {
    runPipeline
  }
`;

export const PIPELINE_STATUS = gql`
  query PipelineStatus {
    pipelineStatus
  }
`;

export const GET_ENTITIES = gql`
  query GetGeospatialEntities {
    getGeospatialEntities {
      name
      lat
      lon
      type
    }
  }
`;