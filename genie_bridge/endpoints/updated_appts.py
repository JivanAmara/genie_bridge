import flask
import json
from genie_bridge.endpoints import (
    register_endpoint, err_resp, DateTimeFriendlyEncoder, InvalidToken,
    HTTPStatusOk, HTTPStatusClientError, HTTPStatusUnauthenticated
)
from genie_bridge.db import get_db

def register(app):
    @register_endpoint(app, "/updated_appts/<since>", 'usage_updated_appts.html')
    def updated_appts(since):
        req = flask.request
        if not req.is_json:
            return err_resp('request content is not json', HTTPStatusClientError)
        req_body = req.get_json()
        auth_token = req_body["token"]

        try:
            db = get_db(auth_token)
        except InvalidToken as ex:
            return err_resp(str(ex), HTTPStatusUnauthenticated)

        cursor = db.cursor()
        cursor.execute("SELECT startdate, starttime, enddate, apptduration / 60 FROM Appt WHERE LastUpdated >= '{}'".format(since))
        result = cursor.fetchall()
        data = []
        for r in result:
            data.append({
                "startdate": r[0],
                "starttime": r[1],
                "enddate": r[2],
                "aptduration": r[3],
            })

        resultJson = json.dumps(data, cls=DateTimeFriendlyEncoder)
        resp = flask.Response(resultJson)
        resp.headers['Content-Type'] = 'application/json'

        return resp, HTTPStatusOk
