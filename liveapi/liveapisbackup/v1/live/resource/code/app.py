from flask import Flask
from resource import resource_api

app = Flask(__name__)

app.register_blueprint(resource_api)

@app.route("/")
def hello():
    return "Archeplay Resource!"

if __name__ == "__main__":
    app.run()