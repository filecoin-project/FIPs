#Suggestions from Ian - Change timedelta from 30 days to a few minutes
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import os
import json

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
#Select github's api transport
transport = AIOHTTPTransport(
    url='https://api.github.com/graphql',
    headers={'Authorization': f'Bearer {GITHUB_TOKEN}'}
)

#getAllDiscussions instantiates a client connected to github's api transport and sends a query for all discussion objects in a given date range
#startDateTime: datetime object for the start of the range
#endDateTime: datetime object for the end of the range
#return: a list of ids



def getAllDiscussions():
  ids = []
  discussionPosts = []
  client = Client(transport=transport, fetch_schema_from_transport=True)
  endCursor = ""
  while True:
    params = {'endCursor': endCursor }
    query = gql(
        """
    query getAllDiscussions($endCursor: String!){
      repository(owner: "NateWebb03", name: "FIPs") {
        discussions(first: 100, after: $endCursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
          pageInfo{
          endCursor
          hasNextPage
          }
          # type: DiscussionConnection
          totalCount # Int!
          
          nodes {
            #type: Discussion
            id
            lastEditedAt
            createdAt
            comments(first: 1){
              nodes{
              #Type: Comment
                id
                createdAt
                updatedAt
                publishedAt
                replies(first: 1){
                  nodes{
                    id
                    createdAt
                    lastEditedAt
                    updatedAt
                    publishedAt
                  }
                }
              }
            }
            labels(first: 10){
            #Type: LabelConnection
              nodes{
              #Type: Label
                name
                id
              }
            }
          }
        }
      }
    }
        """
    ) if endCursor != "" else gql(
        """
    query getAllDiscussions{
      repository(owner: "NateWebb03", name: "FIPs") {
        discussions(first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
          pageInfo{
          endCursor
          hasNextPage
          }
          # type: DiscussionConnection
          totalCount # Int!
          
          nodes {
            #type: Discussion
            id
            lastEditedAt
            createdAt
            comments(first: 1){
              nodes{
              #Type: Comment
                id
                createdAt
                updatedAt
                publishedAt
                replies(first: 1){
                  nodes{
                    id
                    createdAt
                    lastEditedAt
                    updatedAt
                    publishedAt
                  }
                }
              }
            }
            labels(first: 10){
            #Type: LabelConnection
              nodes{
              #Type: Label
                name
                id
              }
            }
          }
        }
      }
    }
        """
    )
    result = client.execute(query, variable_values=params)
    discussionPosts += (result['repository']['discussions']['nodes'])
    if result['repository']['discussions']['pageInfo']['hasNextPage']:
      endCursor = result['repository']['discussions']['pageInfo']['endCursor']
      continue
    else:
      break

  print(len(discussionPosts))
  return discussionPosts

#TODO: Add logic checking comments: updatedAt  replies: updatedAt & 
def isActive(discussionPost):
  return True

def updateDiscussions(discussionPosts, currentDateTime):
  client = Client(transport=transport, fetch_schema_from_transport=True)
  QUIET_LABEL = 'LA_kwDOCq44tc7jNGmM'
  ACTIVE_LABEL = 'LA_kwDOCq44tc7jNGan'
  NEW_LABEL = 'LA_kwDOCq44tc7jNGRJ'
  updates = []
  for d in discussionPosts:
    labelsToAdd = []
    labelsToRemove = []
    if datetime.datetime.fromisoformat(d['createdAt']) < currentDateTime - timedelta(days = 30):
      labelsToRemove += NEW_LABEL
    else:
      labelsToAdd += NEW_LABEL
    if isActive():
      labelsToAdd += ACTIVE_LABEL
      labelsToRemove += QUIET_LABEL
    else:
      labelsToRemove += ACTIVE_LABEL
      labelsToAdd += QUIET_LABEL
    updates += {'id': d['id'], 'add': labelsToAdd, 'remove': labelsToRemove}
    
    
  for u in updates: 
    mutate = gql(
      """
      mutation addLabel($id: ID!, $add: [ID!]!, $remove: [ID!]!){
        addLabelsToLabelable(input: {labelIds: $add, labelableId: $id})
        removeLabelsFromLabelable(input: {labelIds: $remove, labelableId: $id})
      }
      """
    )
  result = client.execute(mutate, variable_values=u)
  print(result)
  return
print(getAllDiscussions())
