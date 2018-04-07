import flask
import json
from datetime import datetime, time
from genie_bridge.config import ResponseJSONDateTimeFormat, ResponseJSONTimeFormat

class InvalidToken(Exception):
    pass

HTTPStatusOk = 200
HTTPStatusClientError = 400
HTTPStatusUnauthenticated = 401
HTTPStatusServerError = 500

# This is a list of active endpoints, populated through Endpoint.__init__()
endpoint_list = []

class Endpoint():
    path = ""
    template = ""
    # Additional context for template
    context = {}
    handler = None
    doc_html = ""

    def __init__(self, app, path, handler, template, extra_context):
        self.path = path
        self.handler = handler
        self.template = template
        c = {"path": path}
        c.update(extra_context)
        self.context = c

        with app.app_context():
            self.doc_html = flask.render_template(template, **c)

        app.add_url_rule(path, handler.__name__, self.get_rerouter(handler), methods=["POST", "GET"])
        if self not in endpoint_list:
            endpoint_list.append(self)
        __call__ = self.get_rerouter(self.handler)

    def get_rerouter(self, func):
        ''' Uses doc_html instead of func() for GET requests
        '''
        get_handler = lambda: (self.doc_html, 200)
        def wrapped_func(*args, **kwargs):
            if flask.request.method == 'GET':
                return get_handler()
            else:
                return func(*args, **kwargs)
        return wrapped_func

def register_endpoint(app, path, doc_template, extra_context={}):
    def decorator(handler):
        ep = Endpoint(app, path, handler, doc_template, extra_context)
        def wrapped_func(*args, **kwargs):
            return ep(*args, **kwargs)
        # The function doesn't get used directly, so don't return a wrapped function.
        return wrapped_func
    return decorator

def err_resp(msg, status):
    json_msg = json.dumps({"detail": msg})
    resp = flask.Response(json_msg)
    resp.headers['Content-Type'] = 'application/json'
    if status == 401:
        resp.headers['WWW-Authenticate'] = 'Bearer'
    return resp, status

# Encode types not supported by default for json encoding
class DateTimeFriendlyEncoder(json.JSONEncoder):
    def default(self, o):
        if type(o) == datetime:
            # return 'datetime.datetime'
            return o.strftime(ResponseJSONDateTimeFormat)
        elif type(o) == time:
            # return 'datetime.time'
            return o.strftime(ResponseJSONTimeFormat)
        else:
            return str(type(o))
