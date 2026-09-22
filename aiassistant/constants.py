get_all_charities_function = {
    "name": "get_all_charities",
    "description": "Retrieve all charities from the database.",
}

search_function = {
    "name": "search_items",
    "description": "Search for a product on the website.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query."},
            "charity_id": {"type": "string", "description": "The charity id of the charity to filter by."},
            "category": {"type": "string", "description": "The category of the product to filter by."},
            "charity_ids": {"type": "array", "description": "The charity ids of the charities to filter by."},
        },
        "required": ["query"],
    },
}

assistant_tools = [{"type": "function", "function": get_all_charities_function}, {"type": "function", "function": search_function}]