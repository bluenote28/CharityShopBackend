import logging
import requests
from django.core.cache import caches
from ebay.models import Item
import os
from ebay.ebay_client import EbayClient
from aiassistant.tools import get_all_charities, search_for_coffee,search_items
from aiassistant.constants import assistant_tools
import json

API_KEY = os.environ.get("AI_KEY")
BASE_URL = "https://inference.do-ai.run/v1/chat/completions"
INVALID_AI_DESCRIPTION = 'AI description is unavailable'
logger = logging.getLogger(__name__)

def _error_detail(data):
    error = data.get('error') if isinstance(data, dict) else None
    if isinstance(error, dict):
        return error.get('message') or error.get('code')
    if isinstance(error, str) and error.strip():
        return error
    return None


def call_ai_api(messages, tools=None):
    payload = {
        "model": "gemma-4-31B-it",
        "messages": messages,
        "max_completion_tokens": 1024,
        "temperature": 0.3,
    }
    if tools:
        payload["tools"] = tools

    try:
        return requests.post(
            BASE_URL,
            headers={
                "Authorization": "Bearer " + API_KEY,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
    except requests.RequestException:
        return {'detail': 'AI description is unavailable'}

def get_ai_response_data(response):
    data = response.json()
    choices = data.get('choices') or []
    choice = choices[0]
    return choice

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
        data = get_ai_response_data(response)
        content = data.get('message').get('content')

        item.ai_description = content
        item.save()
        caches['diskcache'].delete(f'item_{ebay_id}')

    except Exception as e:
        return response.json()
    
    return {'description': content}

def ai_assistant_chat(messages):
    system = (
        "You are a shopping assistant for Charity Shop, a website that lists eBay items "
        "sold to benefit charities. Help people search, choose categories, understand "
        "how purchases support nonprofits, and use the site. "
        "Do not invent specific current listings, prices, or stock. "
        "When asked about if the site has a specific item perform a search for the item and return the results. "
        "In the results return the item name, image, and url." 
        "Always use the search_items function first and also use another tool and return the results if relevant"
        "For example, if the user asks for coffee, use the search_items function to search for coffee and then use the search_for_coffee tool and return the results of each."
        "Use markdown when it helps readability."
    )

    conversation = [{"role": "system", "content": system}] + list(messages)
    response = call_ai_api(conversation, tools=assistant_tools)

    try:
        data = get_ai_response_data(response)
        assistant_message = data.get('message') or {}

        if data.get('finish_reason') == "tool_calls":
            tool_call = (assistant_message.get('tool_calls') or [])[0]
            function = tool_call.get('function') or {}
            tool_name = function.get('name')
            if tool_name == "get_all_charities":
                conversation.append(assistant_message)
                conversation.append({
                    "role": "tool",
                    "content": get_all_charities(),
                    "tool_call_id": tool_call.get('id'),
                })
                response = call_ai_api(conversation, tools=assistant_tools)
                data = get_ai_response_data(response)
                content = (data.get('message') or {}).get('content')
                return {'message': content}
            elif tool_name == "search_items":
                conversation.append(assistant_message)
                conversation.append({
                    "role": "tool",
                    "content": search_items(json.loads(function.get('arguments'))),
                    "tool_call_id": tool_call.get('id'),
                })
                response = call_ai_api(conversation, tools=assistant_tools)
                data = get_ai_response_data(response)
                content = (data.get('message') or {}).get('content')
                return {'message': content}
            elif tool_name == "search_for_coffee":
                conversation.append(assistant_message)
                conversation.append({
                    "role": "tool",
                    "content": search_for_coffee(),
                    "tool_call_id": tool_call.get('id'),
                })
                response = call_ai_api(conversation, tools=assistant_tools)
                data = get_ai_response_data(response)
                content = (data.get('message') or {}).get('content')
                return {'message': content}

        return {'message': assistant_message.get('content')}

    except Exception as e:
        logger.error(f"Error in ai_assistant_chat: {repr(e)}")
        return response.json() if hasattr(response, 'json') else response
