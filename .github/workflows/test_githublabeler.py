import githublabeler
import pytest
FAKE_ID = 'fakeID'
activeDiscussionPosts = []
activeDiscussionPosts.append({'createdAt': '3023-06-01T22:42:26Z', 'lastEditedAt' : '2022-06-01T22:42:26Z',
                                  'comments': {'nodes': [{'createdAt' : '2022-06-01T22:42:26Z', 
                                  'updatedAt': '2022-06-01T22:42:26Z', 'replies': {'nodes': [{'createdAt': '2022-06-01T22:42:26Z'
                                  ,'updatedAt':'2022-06-01T22:42:26Z' }]}}]}})
activeDiscussionPosts.append({'createdAt': '2022-06-01T22:42:26Z', 'lastEditedAt' : '3023-06-01T22:42:26Z',
                                  'comments': {'nodes': [{'createdAt' : '2022-06-01T22:42:26Z', 
                                  'updatedAt': '2022-06-01T22:42:26Z', 'replies': {'nodes': [{'createdAt': '2022-06-01T22:42:26Z'
                                  ,'updatedAt':'2022-06-01T22:42:26Z' }]}}]}})
activeDiscussionPosts.append({'createdAt': '2022-06-01T22:42:26Z', 'lastEditedAt' : '2022-06-01T22:42:26Z',
                                  'comments': {'nodes': [{'createdAt' : '2022-06-01T22:42:26Z', 
                                  'updatedAt': '3023-06-01T22:42:26Z', 'replies': {'nodes': [{'createdAt': '2022-06-01T22:42:26Z'
                                  ,'updatedAt':'2022-06-01T22:42:26Z' }]}}]}})
activeDiscussionPosts.append({'createdAt': '2022-06-01T22:42:26Z', 'lastEditedAt' : '2022-06-01T22:42:26Z',
                                  'comments': {'nodes': [{'createdAt' : '3023-06-01T22:42:26Z', 
                                  'updatedAt': '2022-06-01T22:42:26Z', 'replies': {'nodes': [{'createdAt': '2022-06-01T22:42:26Z'
                                  ,'updatedAt':'2022-06-01T22:42:26Z' }]}}]}})
activeDiscussionPosts.append({'createdAt': '2022-06-01T22:42:26Z', 'lastEditedAt' : '2022-06-01T22:42:26Z',
                                  'comments': {'nodes': [{'createdAt' : '2022-06-01T22:42:26Z', 
                                  'updatedAt': '2022-06-01T22:42:26Z', 'replies': {'nodes': [{'createdAt': '2022-06-01T22:42:26Z'
                                  ,'updatedAt':'3023-06-01T22:42:26Z' }]}}]}})
activeDiscussionPosts.append({'createdAt': '2022-06-01T22:42:26Z', 'lastEditedAt' : '2022-06-01T22:42:26Z',
                                  'comments': {'nodes': [{'createdAt' : '2022-06-01T22:42:26Z', 
                                  'updatedAt': '2022-06-01T22:42:26Z', 'replies': {'nodes': [{'createdAt': '3023-06-01T22:42:26Z'
                                  ,'updatedAt':'2022-06-01T22:42:26Z' }]}}]}})

quietDiscussionPosts = []
quietDiscussionPosts.append({'id':FAKE_ID, 'createdAt': '2022-06-01T22:42:26Z', 'lastEditedAt' : '2022-06-01T22:42:26Z',
                                  'comments': {'nodes': [{'createdAt' : '2022-06-01T22:42:26Z', 
                                  'updatedAt': '2022-06-01T22:42:26Z', 'replies': {'nodes': [{'createdAt': '2022-06-01T22:42:26Z'
                                  ,'updatedAt':'2022-06-01T22:42:26Z' }]}}]}})

newDiscussionPosts = []
newDiscussionPosts.append({'id':FAKE_ID, 'createdAt': '3022-06-01T22:42:26Z', 'lastEditedAt' : '2022-06-01T22:42:26Z',
                                  'comments': {'nodes': [{'createdAt' : '2022-06-01T22:42:26Z', 
                                  'updatedAt': '2022-06-01T22:42:26Z', 'replies': {'nodes': [{'createdAt': '2022-06-01T22:42:26Z'
                                  ,'updatedAt':'2022-06-01T22:42:26Z' }]}}]}})


def test_isActive():
  
  for d in activeDiscussionPosts:
    assert githublabeler.isActive(d) == True
  
  for d in quietDiscussionPosts:
    assert githublabeler.isActive(d) == False
def test_getUpdates():
  assert githublabeler.getUpdates(quietDiscussionPosts) == [{'id':FAKE_ID,
                                                             'add': [githublabeler.QUIET_LABEL], 
                                                             'remove': [ githublabeler.NEW_LABEL, githublabeler.ACTIVE_LABEL]}]
  assert githublabeler.getUpdates(activeDiscussionPosts) == [{'id':FAKE_ID,
                                                              'add': [githublabeler.ACTIVE_LABEL],
                                                              'remove': [githublabeler.NEW_LABEL, githublabeler.QUIET_LABEL]}]
  assert githublabeler.getUpdates(newDiscussionPosts) == [{'id':FAKE_ID,
                                                            'add': [githublabeler.NEW_LABEL, githublabeler.ACTIVE_LABEL],
                                                            'remove': [githublabeler.QUIET_LABEL]}]