from django.shortcuts import render
from django.http import HttpResponse
from dotenv import load_dotenv
from .models import Petfinder_API_Token
from datetime import datetime, timezone
import requests
from requests.structures import CaseInsensitiveDict
import os

def update_petfinder_token():
  load_dotenv()
  PETFINDER_API_KEY = os.getenv('PETFINDER_API_KEY')
  PETFINDER_SECRET = os.getenv('PETFINDER_SECRET')
  url = 'https://api.petfinder.com/v2/oauth2/token'
  payload = { 'grant_type': 'client_credentials', 'client_id':{PETFINDER_API_KEY}, 'client_secret':{PETFINDER_SECRET} }
  response = requests.post(url, data = payload)
  response = response.json()
  return response['access_token']
  

def get_pathfinder_token():
  token_object = Petfinder_API_Token.objects.first()
  # TODO update timezone awareness if we set a server timezone/use tomezones
  token_age = datetime.now(timezone.utc) - token_object.date
  print(token_age.total_seconds(), '<- Token Age')
  if token_age.total_seconds() >= 3000:
    token_object.token = update_petfinder_token()
    token_object.save()
  return token_object.token

# query_list expects a list of key, value tuples ex. [(key, value), (key2, value2), ...]
def get_pathfinder_request(endpoint = '', query_list = ''):
  url = 'https://api.petfinder.com/v2/'
  url = url + endpoint
  query_string = ''
  if query_list:
    for i, query in enumerate(query_list):
      query_string = query_string + '?' if i == 0 else query_string + '&'
      query_string = query_string + f'{query[0]}={query[1]}'
  token = get_pathfinder_token()
  headers = CaseInsensitiveDict()
  headers["Accept"] = "application/json"
  headers["Authorization"] = f"Bearer {token}"
  response = requests.get(url, headers=headers)
  return response.json()
  
def home(request):  
  response = get_pathfinder_request([('type', 'dog'), ('location', '78729')],'animals')
  return render(request, 'home.html', {'response': response})