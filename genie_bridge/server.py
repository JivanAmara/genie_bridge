import flask

# Endpoint helpers
from genie_bridge.endpoints import endpoint_list, err_resp
# Enpoints
from genie_bridge.endpoints import login, updated_appts, patient_data

app = flask.Flask(__name__)

# Register endpoints
login.register(app)
updated_appts.register(app)
patient_data.register(app)

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
    @app.errorhandler(status)
    def eh(e):
        return err_resp(message, status)

if __name__ == '__main__':
    app.run()
