import flask

from genie_bridge.endpoints import endpoint_list, err_resp, login, try1

app = flask.Flask(__name__)

@app.route('/', methods=['GET'])
def usage_all():
    return flask.render_template('usage_all.html', endpoints=endpoint_list)


# Error pages as json
http_errors = {
    400: "client error",
    404: "page not found",
    500: "internal server error",

}
for status, message in http_errors.items():
    def error_handler(e):
        return err_resp(message, status)
    app.error_handler_spec[None][404] = error_handler

# Register endpoints
login.register(app)
try1.register(app)

if __name__ == '__main__':
    app.run()
