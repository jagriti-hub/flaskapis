from flask import Flask
from product import product_api
from service import service_api
from resource import resource_api
from data import data_api
from table import table_api
from testcase import testcase_api
from autogeneratemethod import autogeneratemethod_api

app = Flask(__name__)

app.register_blueprint(product_api)
app.register_blueprint(service_api)
app.register_blueprint(resource_api)
app.register_blueprint(data_api)
app.register_blueprint(table_api)
app.register_blueprint(testcase_api)
app.register_blueprint(autogeneratemethod_api)

if __name__ == "__main__":
    app.run()