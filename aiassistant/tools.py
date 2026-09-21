import json
import requests
from bs4 import BeautifulSoup
from django.core.serializers.json import DjangoJSONEncoder
from ebay.models import Charity
from ebay.serializers import CharitySerializer

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def checkMysticMonk():
   mystic_monk_coffee_url = "https://www.mysticmonkcoffee.com/collections/all-coffee?filter.p.m.coffee_product.coffee_size=12oz&filter.v.availability=1"
   response = requests.get(mystic_monk_coffee_url, headers=headers)
   soup = BeautifulSoup(response.text, "html.parser")
   coffee = soup.find_all("product-card", class_="product-card")
   ##coffee_names  = [coffee.find("div", class_="coffee-title").text for coffee in coffee]
   coffee_names = soup.find_all("div", class_="coffee-title")
   print(coffee_names)

def get_all_charities():
   data = CharitySerializer(Charity.objects.all(), many=True).data
   return json.dumps(list(data), cls=DjangoJSONEncoder)

if __name__ == "__main__":
   checkMysticMonk()