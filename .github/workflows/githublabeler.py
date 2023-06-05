#Suggestions from Ian - Change timedelta from 30 days to a few minutes
from datetime import datetime, timedelta, timezone
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import os


#These labels are for NateWebb03/FIPs
QUIET_LABEL = 'LA_kwDOJKIKAM8AAAABTBrWYg'
ACTIVE_LABEL = 'LA_kwDOJKIKAM8AAAABTBrVow'
NEW_LABEL = 'LA_kwDOJKIKAM8AAAABTBrTjA'
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
#Select github's api transport
transport = AIOHTTPTransport(
    url='https://api.github.com/graphql',
    headers={'Authorization': f'Bearer {GITHUB_TOKEN}'}
)

#getAllDiscussions instantiates a client connected to github's api transport and sends a query for all discussion objects in a given date range
#startDateTime: datetime object for the start of the range
#endDateTime: datetime object for the end of the range
#return: a list of dictionaries each containing separate return values from graphql queries


#TODO: solve edge cases for >100 replies or comments
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
            comments(first: 100){
              nodes{
              #Type: Comment
                id
                createdAt
                updatedAt
                publishedAt
                replies(first: 50){
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
            comments(first: 50){
              nodes{
              #Type: Comment
                id
                createdAt
                updatedAt
                publishedAt
                replies(first: 50){
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
  print(discussionPosts)
  return discussionPosts


def isActive(discussionPost):
  currentDateTime = datetime.now(timezone.utc)
  comments = discussionPost['comments']['nodes']
  if datetime.fromisoformat(discussionPost['createdAt']) > currentDateTime - timedelta(days = 60):
    return True
  if discussionPost['lastEditedAt'] != None:
    if datetime.fromisoformat(discussionPost['lastEditedAt']) > currentDateTime - timedelta(days = 60):
      return True
  for comment in comments:
    replies = comment['replies']['nodes']
    if datetime.fromisoformat(comment['updatedAt']) > currentDateTime - timedelta(days = 60):
      return True
    if datetime.fromisoformat(comment['createdAt']) > currentDateTime - timedelta(days = 60):
      return True
    for reply in replies:
      if datetime.fromisoformat(reply['updatedAt']) > currentDateTime - timedelta(days = 60):
        return True
      if datetime.fromisoformat(reply['createdAt']) > currentDateTime - timedelta(days = 60):
        return True
  return False



def getUpdates(discussionPosts):
  currentDateTime = datetime.now(timezone.utc)
  print(currentDateTime.tzinfo)
  #These labels are for FILECOIN-PROJECT/FIPs
  #QUIET_LABEL = "LA_kwDOCq44tc7jNGmM"
  #ACTIVE_LABEL = "LA_kwDOCq44tc7jNGan"
  #NEW_LABEL = "LA_kwDOCq44tc7jNGRJ"

  updates = []
  for d in discussionPosts:
    createdAtTime = datetime.fromisoformat(d['createdAt'])
    labelsToAdd = []
    labelsToRemove = []
    if createdAtTime < currentDateTime - timedelta(days = 30):
      labelsToRemove.append(NEW_LABEL)
    else:
      labelsToAdd.append(NEW_LABEL)
    if isActive(d):
      labelsToAdd.append(ACTIVE_LABEL)
      labelsToRemove.append(QUIET_LABEL)
    else:
      labelsToRemove.append(ACTIVE_LABEL)
      labelsToAdd.append(QUIET_LABEL)
    updates.append({'id': d['id'], 'add': labelsToAdd, 'remove': labelsToRemove})
  return updates

   
def updateLabels(updatesList):
  client = Client(transport=transport, fetch_schema_from_transport=True)
  print(updatesList)
  for u in updatesList: 
    mutate = gql(
      """
      mutation changeLabels($id: ID!, $add: [ID!]!, $remove: [ID!]!){
        addLabelsToLabelable(input:{labelIds:$add, labelableId:$id}){
          labelable{
            labels(first: 10){
              nodes{
                name
              }
            }
          }
        }
        removeLabelsFromLabelable(input:{labelIds:$remove, labelableId:$id}){
          labelable{
            labels(first: 10){
              nodes{
                name
              }
            }
          }
        }
      }
      """
    )
    result = client.execute(mutate, variable_values=u)
    print(result)
  return



def main():
  discussions = getAllDiscussions()
  updates = getUpdates(discussions)
  updateLabels(updates)
if __name__ == "__main__":
  main()