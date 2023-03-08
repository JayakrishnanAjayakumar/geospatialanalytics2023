import sqlite3
def getDB(name):
    with sqlite3.connect(f'databases/{name}.db') as db:
        return db
            