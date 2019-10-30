def heatwave_api(request):
    return 'Hello, World!\n'


if __name__ == "__main__":
    from flask import Flask, request
    app = Flask(__name__)

    @app.route('/')
    def index():
        return heatwave_api(request)

    app.run('127.0.0.1', 8000, debug=True)
