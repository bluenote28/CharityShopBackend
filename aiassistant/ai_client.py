import logging
import requests
from django.core.cache import caches
from ebay.models import Item
import os
from ebay.ebay_client import EbayClient

API_KEY = os.environ.get("AI_KEY")
BASE_URL = "https://inference.do-ai.run/v1/chat/completions"
INVALID_AI_DESCRIPTION = 'AI description is unavailable'

def _error_detail(data):
    error = data.get('error') if isinstance(data, dict) else None
    if isinstance(error, dict):
        return error.get('message') or error.get('code')
    if isinstance(error, str) and error.strip():
        return error
    return None


def call_ai_api(messages):
    try:
        response = requests.post(
            BASE_URL,
            headers={
                "Authorization": "Bearer " + API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "model": "gemma-4-31B-it",
                "messages": messages,
                "max_completion_tokens": 1024,
                "temperature": 0.3,
            },
            timeout=60,
        )
    except requests.RequestException:
        return {'detail': 'AI description is unavailable'}

    return response

def get_ai_advice(ebay_id):

    item = Item.objects.get(ebay_id=ebay_id)

    if  not item.seller_description:
        ebay_client = EbayClient(item.charity_id)
        item_details = ebay_client.getItemDetails(ebay_id)
        item.seller_description = item_details['seller_description']

    system_prompt = """You research a single eBay listing and write a detailed description of that item. "
        "Provide infomation a buyer should know that is not available in the item name or seller description."
        "Never describe a different product."""

    response = call_ai_api([{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Item name: {item.name}, Seller description: {item.seller_description}"}])

    try:
        choices = data.get('choices') or []
        content = choices[0].get('message')

        item.ai_description = content
        item.save()
        caches['diskcache'].delete(f'item_{ebay_id}')

    except Exception as e:
        return response.json()
    
    return {'description': content}

def ai_assistant_chat(messages):
    system = """You are a shopping assistant for Charity Shop, a website that lists eBay items "
    "sold to benefit charities. Help people search, choose categories, understand "
    "how purchases support nonprofits, and use the site. "
    "Do not invent specific current listings, prices, or stock. "
    "Suggest search phrases and category names instead. Keep answers concise. "
    "Use markdown when it helps readability."""

    response = call_ai_api([{"role": "system", "content": system}] + messages)

    try:

        choices = data.get('choices') or []
        content = choices[0].get('message')
        return {'message': content}

    except Exception as e:
        return response.json()
