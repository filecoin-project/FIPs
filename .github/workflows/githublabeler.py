from datetime import datetime, timedelta, timezone
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import os


# These labels are for FILECOIN-PROJECT/FIPs
QUIET_LABEL = "LA_kwDOCq44tc7jNGmM"
ACTIVE_LABEL = "LA_kwDOCq44tc7jNGan"
NEW_LABEL = "LA_kwDOCq44tc7jNGRJ"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# TODO: solve edge cases for > 100 replies or comments
# getAllDiscussions returns a list of all discussion posts in the FIPs repo


def getAllDiscussions(client):
    discussionPosts = []
    endCursor = ""
    while True:
        params = {'endCursor': endCursor}
        query = gql(
            """
    query getAllDiscussions($endCursor: String!){
      repository(owner: "filecoin-project", name: "FIPs") {
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
        ) if endCursor != "" else gql(
            """
    query getAllDiscussions{
      repository(owner: "filecoin-project", name: "FIPs") {
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
    return discussionPosts

# isActive takes a discussion post and returns true if it has been active
# in the last 60 days


def isActive(discussionPost):
    currentDateTime = datetime.now(timezone.utc)
    comments = discussionPost['comments']['nodes']
    if datetime.fromisoformat(
            discussionPost['createdAt']) > currentDateTime - timedelta(days=60):
        return True
    if discussionPost['lastEditedAt'] is not None:
        if datetime.fromisoformat(
                discussionPost['lastEditedAt']) > currentDateTime - timedelta(days=60):
            return True
    for comment in comments:
        replies = comment['replies']['nodes']
        if datetime.fromisoformat(
                comment['updatedAt']) > currentDateTime - timedelta(days=60):
            return True
        if datetime.fromisoformat(
                comment['createdAt']) > currentDateTime - timedelta(days=60):
            return True
        for reply in replies:
            if datetime.fromisoformat(
                    reply['updatedAt']) > currentDateTime - timedelta(days=60):
                return True
            if datetime.fromisoformat(
                    reply['createdAt']) > currentDateTime - timedelta(days=60):
                return True
    return False

# getUpdates takes a list of discussion posts and returns a list of
# updates to be made to the labels


def getUpdates(discussionPosts):
    currentDateTime = datetime.now(timezone.utc)

    updates = []
    for d in discussionPosts:
        createdAtTime = datetime.fromisoformat(d['createdAt'])
        labelsToAdd = []
        labelsToRemove = []
        if createdAtTime < currentDateTime - timedelta(days=30):
            labelsToRemove.append(NEW_LABEL)
        else:
            labelsToAdd.append(NEW_LABEL)
        if isActive(d):
            labelsToAdd.append(ACTIVE_LABEL)
            labelsToRemove.append(QUIET_LABEL)
        else:
            labelsToRemove.append(ACTIVE_LABEL)
            labelsToAdd.append(QUIET_LABEL)
        updates.append(
            {'id': d['id'], 'add': labelsToAdd, 'remove': labelsToRemove})
    return updates

# updateLabels takes a list of updates and updates the labels on github
# accordingly using the github api


def updateLabels(updatesList, client):
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
    transport = AIOHTTPTransport(
        url='https://api.github.com/graphql',
        headers={'Authorization': f'Bearer {GITHUB_TOKEN}'}
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)
    discussions = getAllDiscussions(client)
    updates = getUpdates(discussions)
    updateLabels(updates, client)


if __name__ == "__main__":
    main()
