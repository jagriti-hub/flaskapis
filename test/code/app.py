from flask import Flask
from product import product_api
from service import service_api
from resource import resource_api

app = Flask(__name__)

app.register_blueprint(product_api)
app.register_blueprint(service_api)
app.register_blueprint(resource_api)

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run()