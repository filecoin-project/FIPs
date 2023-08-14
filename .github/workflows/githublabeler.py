from datetime import datetime, timedelta, timezone
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import os


#### FIPs Governance Bot v1
# This file is designed to automate the github labeling process for the `filecoin-project/FIPs` repo.
# The current labeling process is documented at https://github.com/filecoin-project/FIPs/discussions/292.
# Currently only the first three labels, Quiet, Active, and New, are automated.
# This file is designed to be run on a cron job through the github workflows interface.


# These labels are for FILECOIN-PROJECT/FIPs
QUIET_LABEL = "LA_kwDOCq44tc7jNGmM"
ACTIVE_LABEL = "LA_kwDOCq44tc7jNGan"
NEW_LABEL = "LA_kwDOCq44tc7jNGRJ"

ACTIVE_DAYS = 60
NEW_DAYS = 30

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


# Was this discussion created in the last 30 days?
def isNew(discussionPost, now):
    return datetime.fromisoformat(discussionPost['createdAt']) < now - timedelta(days=NEW_DAYS)

# Has this discussion had any activity in the last 60 days?
# Currently checks for new comments, replies, or edits to the post
def isActive(discussionPost, now):
    comments = discussionPost['comments']['nodes']
    activeCutoff = now - timedelta(days=ACTIVE_DAYS)
    if datetime.fromisoformat(discussionPost['createdAt']) > activeCutoff:
        return True
    if discussionPost['lastEditedAt'] is not None:
        if datetime.fromisoformat(discussionPost['lastEditedAt']) > activeCutoff:
            return True

    for comment in comments:
        if datetime.fromisoformat(comment['updatedAt']) > activeCutoff:
            return True
        if datetime.fromisoformat(comment['createdAt']) > activeCutoff:
            return True

        replies = comment['replies']['nodes']
        for reply in replies:
            if datetime.fromisoformat(reply['updatedAt']) > activeCutoff:
                return True
            if datetime.fromisoformat(reply['createdAt']) > activeCutoff:
                return True
    return False

# getUpdates takes a list of discussion posts and returns a list of
# updates to be made to the labels
def getUpdates(discussionPosts, now):
    updates = []
    for d in discussionPosts:
        labelsToAdd = []
        labelsToRemove = []
        if isNew(d, now):
            labelsToRemove.append(NEW_LABEL)
        else:
            labelsToAdd.append(NEW_LABEL)
        if isActive(d, now):
            labelsToAdd.append(ACTIVE_LABEL)
            labelsToRemove.append(QUIET_LABEL)
        else:
            labelsToRemove.append(ACTIVE_LABEL)
            labelsToAdd.append(QUIET_LABEL)
        updates.append({
            'id': d['id'],
            'add': labelsToAdd,
            'remove': labelsToRemove
        })
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
    now = datetime.now(timezone.utc)
    updates = getUpdates(discussions, now)
    updateLabels(updates, client)

if __name__ == "__main__":
    main()
