from flask import Flask, redirect, request

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    target = "https://natgea-thnaweya.abdohamdii701.workers.dev/"
    if path:
        target += path
    if request.query_string:
        target += "?" + request.query_string.decode('utf-8')
    return redirect(target, code=302)
