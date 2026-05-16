from pydantic import BaseModel

class User(BaseModel):
    username: str
    clearance_level: str  # public, internal, or restricted

# Hierarchical clearance mapping to evaluate security walls mathematically
CLEARANCE_WEIGHTS = {
    "public": 1,
    "internal": 2,
    "restricted": 3
}

# Simple Mock Corporate Database
USERS_DB = {
    "alice": User(username="alice", clearance_level="public"),
    "bob": User(username="bob", clearance_level="internal"),
    "charlie": User(username="charlie", clearance_level="restricted"),
}
