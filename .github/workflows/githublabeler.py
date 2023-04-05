from datetime import datetime, timedelta
from github import Github
import os

# Authentication token for your GitHub account
try:
    GITHUB_TOKEN = os.getenv("TOKEN_SECRET")
except KeyError:
    GITHUB_TOKEN = "Token not available!"
    #logger.info("Token not available!")
    #raise

# The repository to check discussion posts for
REPO_NAME = "FIPs"

# Labels for discussion posts
NEW_LABEL = "New"
ACTIVE_LABEL = "Active"
QUIET_LABEL = "Quiet"

# Time delta for new discussions (30 days) and active discussions (2 months)
NEW_DELTA = timedelta(days=30)
ACTIVE_DELTA = timedelta(days=60)

# Initialize the PyGithub object with the authentication token
g = Github(GITHUB_TOKEN)

# Get the repository object for the specified repository name
repo = g.get_repo(REPO_NAME)

# Get all the discussions for the repository
discussions = repo.get_discussions()

# Iterate through the discussions and label them accordingly
for discussion in discussions:
    last_update = discussion.updated_at.replace(tzinfo=None)
    time_since_last_update = datetime.utcnow() - last_update
    if time_since_last_update <= NEW_DELTA:
        discussion.add_to_labels(NEW_LABEL) 
    elif time_since_last_update <= ACTIVE_DELTA:
        discussion.add_to_labels(ACTIVE_LABEL)     
    else:
        discussion.add_to_labels(QUIET_LABEL)
        
