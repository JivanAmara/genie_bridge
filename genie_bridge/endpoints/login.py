import flask
import p4d
import json
import hashlib
from datetime import datetime

from genie_bridge.db import db_connections
from genie_bridge.endpoints import (
    register_endpoint, err_resp, HTTPStatusOk, HTTPStatusClientError, HTTPStatusServerError
)
from genie_bridge.config import DBHost, userkey, passwordkey

def generate_token(req):
    addr = req.remote_addr
    now = datetime.now()
    nowstr = now.strftime("%Y-%m-%d_%H:%M:%S")
    h = hashlib.sha256()
    key = "{}{}".format(addr, nowstr)
    h.update(key.encode('utf8'))
    token = h.hexdigest()
    return token

def register(app):
    @register_endpoint(app, '/login', 'usage_login.html', {'userkey': userkey, 'passwordkey': passwordkey})
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
                return err_resp("invalid user, password, host ({}), or service not running".format(DBHost), HTTPStatusClientError)
            else:
                return err_resp(str(ex), HTTPStatusServerError)
        except Exception as ex:
            return err_resp(str(ex), HTTPStatusServerError)

        token = generate_token(req)
        db_connections[token] = {"db": db, "last_access": datetime.now()}

        return json.dumps({"token": token}), HTTPStatusOk
