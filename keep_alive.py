from flask import Flask, rander_template
from threading import Thread

app = Flask(__name__)
@app.route('/')

def index():
  return "I'am Alive"
def run():
  app.run(host='0.0.0.0', port=8080)
def keep_alive():
  t=Thread(target=run)
  t.start()
