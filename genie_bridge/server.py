import os
import atexit
import json
import hashlib
from datetime import datetime, time, timedelta
import logging
import sys

import flask
import p4d

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stderr))

app = flask.Flask(__name__)

# This uses an api token (hex string) as the key to a dict of the form:
#   {
#       "db": <authenticated 4d database connection>,
#       "last_access": datetime.datetime
#   }
db_connections = {}
# This is a list of active endpoints, populated through Endpoint.__init__()
endpoints = []

# Time in seconds after last use of token to invalidate it.
TokenInactivityTimeout = timedelta(seconds=300)

HTTPStatusOk = 200
HTTPStatusClientError = 400
HTTPStatusServerError = 500
userkey = "user"
passwordkey = "password"
DBHost = os.environ.get('DBHost')

# Close all db connections on exit
def close_all_db_connections(db_connections):
    logger.info('shutdown - closing {} connections...'.format(len(db_connections)))
    for token, db_details in db_connections.items():
        if db_connections[token]["db"].connected:
            db_connections[token]["db"].close()
    logger.info('shutdown - closing connections, done')
atexit.register(close_all_db_connections, db_connections)

def err_resp(msg, status):
    json_msg = json.dumps({"detail": msg})
    resp = flask.Response(json_msg)
    resp.headers['Content-Type'] = 'application/json'
    return resp, status

def generate_token(req):
    addr = req.remote_addr
    now = datetime.now()
    nowstr = now.strftime("%Y-%m-%d_%H:%M:%S")
    h = hashlib.sha256()
    key = "{}{}".format(addr, nowstr)
    h.update(key.encode('utf8'))
    token = h.hexdigest()
    return token

class Endpoint():
    path = ""
    template = ""
    # Additional context for template
    context = {}
    handler = None

    def __init__(self, path, handler, template, extra_context):
        self.path = path
        self.handler = handler
        app.add_url_rule(path, handler.__name__, self.get_rerouter(handler), methods=["POST", "GET"])
        if self not in endpoints:
            endpoints.append(self)
        self.context.update(extra_context)
        __call__ = self.get_rerouter(self.handler)

    def get_rerouter(self, func):
        get_handler = lambda: (self.doc_html(), 200)
        def wrapped_func():
            if flask.request.method == 'GET':
                return get_handler()
            else:
                return func()
        return wrapped_func

    def doc_html(self):
        self.context.update({"path": self.path, "template": self.template})
        html = flask.render_template('usage_login.html', **self.context)
        return html

def register_endpoint(path, doc_template, extra_context):
    def decorator(handler):
        ep = Endpoint(path, handler, doc_template, extra_context)
        def wrapped_func():
            return ep()
        # The function doesn't get used directly, so don't return a wrapped function.
        return wrapped_func
    return decorator

@register_endpoint('/login', 'usage_login.html', {'userkey': userkey, 'password': passwordkey})
def login():
    req = flask.request
    if not req.is_json:
        msg = "request must be json encoded with Content-Type set to 'application/json'"
        return err_resp(msg, HTTPStatusClientError)

    req_body = req.get_json()

    if userkey not in req_body and passwordkey not in req_body:
        return err_resp('request must contain "user" and "pass" parameters', HTTPStatusClientError)

    user = req_body[userkey]
    password = req_body[passwordkey]

    try:
        db = p4d.connect(user=user, password=password, host=DBHost)
        # db = p4d.connect(user="dr a demo", password="genie1", host="127.0.0.1")
    except p4d.OperationalError as ex:
        if str(ex) == 'Unable to connect to 4D Server':
            return err_resp("invalid user, password, or host", HTTPStatusClientError)
        else:
            return err_resp(str(ex), HTTPStatusServerError)
    except Exception as ex:
        return err_resp(str(ex), HTTPStatusServerError)

    token = generate_token(req)
    db_connections[token] = {"db": db, "last_access": datetime.now()}

    return json.dumps({"token": token}), HTTPStatusOk

def clean_db_connections():
    n = datetime.now()
    for token, db_details in db_connections.items():
        if n - db_details["last_access"] > TokenInactivityTimeout:
            if db_connections[token]["db"].connected:
                db_connections[token]["db"].close()
            del db_connections[token]

def get_db(token):
    clean_db_connections()
    if token not in db_connections:
        raise Exception("invalid token")

    db_connections[token]["last_access"] = datetime.now()
    return db_connections["db"]

@app.route('/', methods=['GET'])
def usage_all():
    return flask.render_template('usage_all.html')

# Encode types not supported by default for json encoding
class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if type(o) == datetime:
            # return 'datetime.datetime'
            return o.strftime('%m/%d/%Y')
        elif type(o) == time:
            # return 'datetime.time'
            return o.strftime('%H:%M')
        else:
            return str(type(o))

@app.route("/try1", methods=['GET', 'POST'])
def try1():
    req = flast.request
    db = get_db(auth_token)

    cursor = db.cursor()
    cursor.execute("SELECT startdate, starttime, enddate, apptduration / 60 FROM Appt WHERE LastUpdated >= '20180123225459'")
    result = cursor.fetchall()
    data = []
    for r in result:
        data.append({
            "startdate": r[0],
            "starttime": r[1],
            "enddate": r[2],
            "aptduration": r[3],
        })

    resultJson = json.dumps(data, cls=MyEncoder)
    resp = flask.Response(resultJson)
    resp.headers['Content-Type'] = 'application/json'

    return resp, 200
