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
        "max_completion_tokens": 2560,
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
            timeout=90,
        )

    except requests.RequestException as e:
        return {'detail': str(e)}
    except Exception as e:
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
        "In the results return the item name and url. "
        "Always present items in a markdown list with no list header. "
        "Always use the search_items function first and also use another tool and return the results if relevant. "
        "For example, if the user asks for coffee, use the search_items function to search for coffee and then use the search_for_coffee tool and return the results of each. "
    )

    conversation = [{"role": "system", "content": system}] + list(messages)

    try:
        response = call_ai_api(conversation, tools=assistant_tools)
        data = get_ai_response_data(response)
        assistant_message = data.get('message') or {}

        if data.get('finish_reason') == "tool_calls":
            tool_calls = assistant_message.get('tool_calls') or []
            conversation.append(assistant_message)
            for tool_call in tool_calls:
                function = tool_call.get('function') or {}
                name = function.get('name')
                raw_arguments = function.get('arguments') or '{}'
                arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
                if name == "get_all_charities":
                    content = get_all_charities()
                elif name == "search_items":
                    content = search_items(arguments)
                elif name == "search_for_coffee":
                    content = json.dumps(search_for_coffee())
                else:
                    content = json.dumps({"error": f"Unknown tool: {name}"})
                conversation.append({
                    "role": "tool",
                    "content": content,
                    "tool_call_id": tool_call.get('id'),
                })
            response = call_ai_api(conversation, tools=assistant_tools)
            data = get_ai_response_data(response)
            assistant_message = data.get('message') or {}

        return {'message': assistant_message.get('content')}

    except Exception as e:
        logger.error(f"Error in ai_assistant_chat: {repr(e)}")
        return response.json() if hasattr(response, 'json') else response
