import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def checkMysticMonk():
   mystic_monk_coffee_url = "https://www.mysticmonkcoffee.com/collections/all-coffee?filter.p.m.coffee_product.coffee_size=12oz&filter.v.availability=1"
   response = requests.get(mystic_monk_coffee_url, headers=headers)
   soup = BeautifulSoup(response.text, "html.parser")
   coffee = soup.find_all("product-card", class_="product-card")
   print(coffee)

if __name__ == "__main__":
   checkMysticMonk()