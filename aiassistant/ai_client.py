import json
import logging
import os

import requests
from django.core.cache import caches

from aiassistant.constants import assistant_tools
from aiassistant.tools import get_all_charities, search_for_coffee, search_items
from ebay.ebay_client import EbayClient
from ebay.models import Item

API_KEY = os.environ.get("AI_KEY")
BASE_URL = "https://inference.do-ai.run/v1/chat/completions"
INVALID_AI_DESCRIPTION = 'AI description is unavailable'
logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = (
    "You are a shopping assistant for Charity Shop, a website that lists eBay items "
    "sold to benefit charities. Help people search, choose categories, understand "
    "how purchases support nonprofits, and use the site. "
    "Do not invent specific current listings, prices, or stock. "
    "When asked about if the site has a specific item perform a search for the item and return the results. "
    "In the results return the item name and url. "
    "Always present items in a list. "
    "Always use the search_items function first and also use another tool and return the results if relevant. "
    "For example, if the user asks for coffee, use the search_items function to search for coffee and then use the search_for_coffee tool and return the results of each. "
)


def _error_detail(data):
    error = data.get('error') if isinstance(data, dict) else None
    if isinstance(error, dict):
        return error.get('message') or error.get('code')
    if isinstance(error, str) and error.strip():
        return error
    return None


def _message_text(message):
    if not isinstance(message, dict):
        return ""

    content = message.get('content')
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                text = part.get('text') or part.get('content') or ''
                if text:
                    parts.append(str(text))
        joined = ''.join(parts).strip()
        if joined:
            return joined

    for key in ('text', 'output_text'):
        value = message.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""

def call_ai_api(messages, tools=None, stream=False):
    payload = {
        "model": "gemma-4-31B-it",
        "messages": messages,
        "max_completion_tokens": 2560,
        "temperature": 0.3,
        "stream": stream,
    }

    if tools:
        payload["tools"] = tools

    headers = {
        "Authorization": "Bearer " + (API_KEY or ""),
        "Content-Type": "application/json",
    }

    try:
        return requests.post(
            BASE_URL,
            headers=headers,
            json=payload,
            timeout=90,
            stream=payload['stream'],
        )
    except requests.RequestException as e:
        return {'detail': str(e)}
    except Exception:
        return {'detail': INVALID_AI_DESCRIPTION}


def get_ai_response_data(response):
    data = response.json()
    choices = data.get('choices') or []
    return choices[0]


def get_ai_advice(ebay_id):
    item = Item.objects.get(ebay_id=ebay_id)

    if not item.seller_description:
        ebay_client = EbayClient(item.charity_id)
        item_details = ebay_client.getItemDetails(ebay_id)
        item.seller_description = item_details['seller_description']

    system_prompt = (
        "You research a single eBay listing and write a detailed description of that item. "
        "Provide infomation a buyer should know that is not available in the item name or seller description."
        "Never describe a different product."
    )

    response = call_ai_api([
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"Item name: {item.name}, Seller description: {item.seller_description}"
            ),
        },
    ])

    if isinstance(response, dict):
        return {'detail': response.get('detail') or INVALID_AI_DESCRIPTION}

    try:
        if not response.ok:
            data = response.json()
            return {'detail': _error_detail(data) or INVALID_AI_DESCRIPTION}

        data = get_ai_response_data(response)
        content = _message_text(data.get('message') or {})
        if not content:
            return {'detail': INVALID_AI_DESCRIPTION}

        item.ai_description = content
        item.save()
        caches['diskcache'].delete(f'item_{ebay_id}')
    except Exception:
        try:
            return response.json()
        except Exception:
            return {'detail': INVALID_AI_DESCRIPTION}

    return {'description': content}


def _execute_tool_call(tool_call):
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

    return {
        "role": "tool",
        "content": content,
        "tool_call_id": tool_call.get('id'),
    }

def _iter_sse_data(response):
    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            continue
        line = raw_line.strip()
        if not line.startswith('data:'):
            continue
        data = line[5:].strip()
        if data == '[DONE]':
            break
        try:
            yield json.loads(data)
        except json.JSONDecodeError:
            logger.warning('Skipping invalid SSE chunk: %s', data)


def _merge_tool_call_delta(tool_calls_by_index, delta_tool_calls):
    for tool_call in delta_tool_calls or []:
        index = tool_call.get('index', 0)
        current = tool_calls_by_index.setdefault(index, {
            'id': '',
            'type': 'function',
            'function': {'name': '', 'arguments': ''},
        })
        if tool_call.get('id'):
            current['id'] = tool_call['id']
        if tool_call.get('type'):
            current['type'] = tool_call['type']
        function = tool_call.get('function') or {}
        if function.get('name'):
            current['function']['name'] += function['name']
        if function.get('arguments'):
            current['function']['arguments'] += function['arguments']


def stream_ai_completion(messages, tools=None):
    """
    Stream a chat completion.
    Yields token events as they arrive. Returns a final summary dict:
    {"finish_reason": str|None, "tool_calls": list|None, "content": str}
    """

    finish_reason = None
    tool_calls_by_index = {}
    content_parts = []

    try:
        with call_ai_api(messages, tools=tools, stream=True) as response:
            if not response.ok:
                try:
                    detail = _error_detail(response.json()) or INVALID_AI_DESCRIPTION
                except Exception:
                    detail = INVALID_AI_DESCRIPTION
                yield {'type': 'error', 'detail': detail}
                return {
                    'finish_reason': 'error',
                    'tool_calls': None,
                    'content': '',
                }

            for chunk in _iter_sse_data(response):
                choices = chunk.get('choices') or []
                if not choices:
                    continue
                choice = choices[0]
                if choice.get('finish_reason'):
                    finish_reason = choice['finish_reason']
                delta = choice.get('delta') or {}
                content = delta.get('content')
                if content:
                    content_parts.append(content)
                    yield {'type': 'token', 'content': content}
                if delta.get('tool_calls'):
                    _merge_tool_call_delta(tool_calls_by_index, delta['tool_calls'])
    except requests.RequestException as e:
        yield {'type': 'error', 'detail': str(e)}
        return {'finish_reason': 'error', 'tool_calls': None, 'content': ''}
    except Exception as e:
        logger.error(f"Error in stream_ai_completion: {repr(e)}")
        yield {'type': 'error', 'detail': 'AI chat is unavailable'}
        return {'finish_reason': 'error', 'tool_calls': None, 'content': ''}

    tool_calls = None
    if tool_calls_by_index:
        tool_calls = [tool_calls_by_index[index] for index in sorted(tool_calls_by_index)]
    return {
        'finish_reason': finish_reason,
        'tool_calls': tool_calls,
        'content': ''.join(content_parts),
    }


def ai_assistant_chat_stream(messages):
    """
    Generator of websocket-friendly events:
    {"type": "token", "content": "..."} | {"type": "done"} | {"type": "error", ...}
    """
    conversation = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}] + list(messages)

    try:
        stream = stream_ai_completion(conversation, tools=assistant_tools)
        summary = None
        while True:
            try:
                event = next(stream)
            except StopIteration as stop:
                summary = stop.value
                break
            if event.get('type') == 'error':
                yield event
                return
            yield event

        if not summary or summary.get('finish_reason') == 'error':
            if not summary:
                yield {'type': 'error', 'detail': 'AI chat is unavailable'}
            return

        tool_calls = summary.get('tool_calls') or []
        if summary.get('finish_reason') == 'tool_calls' or tool_calls:
            assistant_message = {
                'role': 'assistant',
                'content': summary.get('content') or None,
                'tool_calls': tool_calls,
            }
            conversation.append(assistant_message)
            for tool_call in tool_calls:
                conversation.append(_execute_tool_call(tool_call))

            final_stream = stream_ai_completion(conversation, tools=assistant_tools)
            while True:
                try:
                    event = next(final_stream)
                except StopIteration:
                    break
                if event.get('type') == 'error':
                    yield event
                    return
                yield event

        yield {'type': 'done'}
    except Exception as e:
        logger.error(f"Error in ai_assistant_chat_stream: {repr(e)}")
        yield {'type': 'error', 'detail': 'AI chat is unavailable'}