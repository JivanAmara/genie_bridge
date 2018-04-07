import atexit
from datetime import datetime
from genie_bridge.endpoints import InvalidToken
from genie_bridge.config import logger, TokenInactivityTimeout

# This uses an api token (hex string) as the key to a dict of the form:
#   {
#       "db": <authenticated 4d database connection>,
#       "last_access": datetime.datetime
#   }
db_connections = {}


# Close all db connections on exit
def close_all_db_connections(db_connections):
    logger.info('shutdown - closing {} connections...'.format(len(db_connections)))
    for token, db_details in db_connections.items():
        if db_connections[token]["db"].connected:
            db_connections[token]["db"].close()
    logger.info('shutdown - closing connections, done')
atexit.register(close_all_db_connections, db_connections)

def get_db(token):
    clean_db_connections()
    if token not in db_connections:
        raise InvalidToken("invalid token")

    db_connections[token]["last_access"] = datetime.now()
    return db_connections[token]["db"]

def clean_db_connections():
    n = datetime.now()
    for token, db_details in db_connections.items():
        if n - db_details["last_access"] > TokenInactivityTimeout:
            if db_connections[token]["db"].connected:
                db_connections[token]["db"].close()
            del db_connections[token]
