from flask import Flask
from templatepull import template_api

app = Flask(__name__)

app.register_blueprint(template_api)

if __name__ == "__main__":
    app.run()