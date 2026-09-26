import json
import requests
from bs4 import BeautifulSoup
from django.core.serializers.json import DjangoJSONEncoder
from django.core import serializers
#from ebay.models import Charity
#from ebay.serializers import CharitySerializer
#from ebay.search import search

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def searchforCoffee():
   mystic_monk_coffee_url = "https://www.mysticmonkcoffee.com/collections/all-coffee?filter.p.m.coffee_product.coffee_size=12oz&filter.v.availability=1"
   response = requests.get(mystic_monk_coffee_url, headers=headers)
   soup = BeautifulSoup(response.text, "html.parser")
   coffee = soup.find_all("product-card", class_="product-card")
   ##coffee_names  = [coffee.find("div", class_="coffee-title").text for coffee in coffee]
   coffee_names = soup.find_all("div", class_="coffee-title")
   coffee_images = soup.find_all("img", class_="coffee-image")
   coffee_urls = soup.find_all("a", class_="coffee-card__link-overlay")
   coffee_urls = [coffee_url["href"] for coffee_url in coffee_urls]
   print(coffee_urls)

def get_all_charities():
   data = CharitySerializer(Charity.objects.all(), many=True).data
   return json.dumps(list(data), cls=DjangoJSONEncoder)

def search_items(arguments):
   query = arguments.get('query') or None
   charity_id = arguments.get('charity_id') or None
   category = arguments.get('category') or None
   charity_ids = arguments.get('charity_ids') or None
   data = serializers.serialize('json', search(query, charity_id, category, charity_ids)[:10])
   return data
 

if __name__ == "__main__":
   searchforCoffee()