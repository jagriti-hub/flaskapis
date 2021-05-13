from flask import Flask
from publish import publish_api

app = Flask(__name__)

app.register_blueprint(publish_api)

if __name__ == "__main__":
    app.run()