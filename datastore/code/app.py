from flask import Flask
from gitpush import git_api

app = Flask(__name__)

app.register_blueprint(git_api)

if __name__ == "__main__":
    app.run()