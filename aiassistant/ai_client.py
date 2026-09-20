import logging
import requests
from django.core.cache import caches
from ebay.models import Item
import os
from ebay.ebay_client import EbayClient

API_KEY = os.environ.get("AI_KEY")
BASE_URL = "https://inference.do-ai.run/v1/chat/completions"
INVALID_AI_DESCRIPTION = 'AI description is unavailable'

def _message_text(message):
    if not isinstance(message, dict):
        return ''

    content = message.get('content')
    if isinstance(content, str) and content.strip():
        return content.strip()

    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get('type') in (None, 'text', 'output_text'):
                parts.append(part.get('text') or part.get('content') or '')
        text = ''.join(parts).strip()
        if text:
            return text

    for key in ('output_text', 'text'):
        value = message.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ''


def _error_detail(data):
    error = data.get('error') if isinstance(data, dict) else None
    if isinstance(error, dict):
        return error.get('message') or error.get('code')
    if isinstance(error, str) and error.strip():
        return error
    return None

def get_ai_advice(ebay_id):

    item = Item.objects.get(ebay_id=ebay_id)

    if  not item.seller_description:
        ebay_client = EbayClient(item.charity_id)
        item_details = ebay_client.getItemDetails(ebay_id)
        item.seller_description = item_details['seller_description']

    system_prompt = """You research a single eBay listing and write a detailed description of that item. "
        "Provide infomation a buyer should know that is not available in the item name or seller description."
        "Never describe a different product."""

    try:
        response = requests.post(
            BASE_URL,
            headers={
                "Authorization": "Bearer " + API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "model": "gemma-4-31B-it",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Item name: {item.name}, Seller description: {item.seller_description}"},
                ],
                "max_completion_tokens": 1024,
                "temperature": 0.3,
            },
            timeout=60,
        )
    except requests.RequestException:
        return {'detail': 'AI description is unavailable'}

    try:
        data = response.json()
    except ValueError:
        return {'detail': 'AI description is unavailable'}

    if not response.ok:
        return {'detail': _error_detail(data) or 'AI description is unavailable'}

    choices = data.get('choices') or []
    message = choices[0].get('message') if choices and isinstance(choices[0], dict) else {}
    content = _message_text(message)

    if not content:
        return {'detail': 'AI description is unavailable'}

    item.ai_description = content
    item.save()
    caches['diskcache'].delete(f'item_{ebay_id}')

    return {'description': content}
