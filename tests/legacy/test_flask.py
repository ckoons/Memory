#!/usr/bin/env python
"""
Simple Flask test app to verify that Flask is working
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World! Flask is working!'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8003, debug=True)