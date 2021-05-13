from flask import Flask
from database import database_api
from table import table_api
from resource import resource_api

app = Flask(__name__)

app.register_blueprint(resource_api)
app.register_blueprint(database_api)
app.register_blueprint(table_api)

@app.route("/")
def hello():
    return "Archeplay Resource!"

if __name__ == "__main__":
    app.run()