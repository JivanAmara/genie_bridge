import atexit
from datetime import datetime
from genie_bridge.endpoints import InvalidToken
from genie_bridge.config import logger, TokenInactivityTimeout
from p4d import ProgrammingError

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
    tokens = list(db_connections.keys())
    for t in tokens:
        if n - db_connections[t]["last_access"] > TokenInactivityTimeout:
            if db_connections[t]["db"].connected:
                try:
                    db_connections[t]["db"].close()
                except Exception as e:
                    logger.Error(e)
            del db_connections[t]
