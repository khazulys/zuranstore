import requests

#MIDTRANS_SERVER_KEY = 'Mid-server-tOgLcriijkzlz9WShqtW7yOS'

def check_url(url):
    while True:
      response = requests.get(url).text
      if 'has been paid' in response:
        return True
        break
