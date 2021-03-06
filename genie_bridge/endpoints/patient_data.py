import flask
import json
from genie_bridge.endpoints import (
    register_endpoint, err_resp, DateTimeFriendlyEncoder, InvalidToken,
    HTTPStatusOk, HTTPStatusClientError, HTTPStatusUnauthenticated
)
from genie_bridge.db import get_db

def register(app):
    @register_endpoint(app, "/patient_data/<since>/<before>", 'usage_patient_data.html')
    def patient_data(since, before):
        req = flask.request
        if not req.is_json:
            return err_resp('request content is not json or content-type not set to "application/json"', HTTPStatusClientError)
        req_body = req.get_json()
        auth_token = req_body["token"]

        try:
            db = get_db(auth_token)
        except InvalidToken as ex:
            return err_resp(str(ex), HTTPStatusUnauthenticated)

        cursor = db.cursor()
        cols = [
            'id', 'firstname', 'surname', 'dob', 'sex', 'HomePhone', 'EmailAddress',
            'AddressLine1', 'suburb', 'state', 'postcode', 'accounttype',
            'HealthFundName', 'LastUpdated', 'CreationDate',
        ]
        sql = '''
            SELECT {cols}
            FROM Patient
            WHERE LastUpdated >= '{since}' AND LastUpdated < '{before}'
            ORDER BY LastUpdated DESC
        '''.format(cols=', '.join(cols), since=since, before=before)
        cursor.execute(sql)
        result = cursor.fetchall()

        data = []
        for r in result:
            dictrow = { cols[i]: r[i] for i in range(len(cols)) }
            data.append(dictrow)

        resultJson = json.dumps(data, cls=DateTimeFriendlyEncoder)
        resp = flask.Response(resultJson)
        resp.headers['Content-Type'] = 'application/json'

        return resp, HTTPStatusOk
