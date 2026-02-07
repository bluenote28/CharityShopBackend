import boto3
import logging

logger = logging.getLogger(__name__)
client = boto3.client('bedrock-runtime', region_name= 'us-east-1')
MODEL = "google.gemma-3-12b-it"


def get_item_description(item_title):

    try: 
        response = client.converse(
            modelId=MODEL,
            messages = [{
                'role': 'user',
                'content': [{'text': item_title}]
            }],
            system=[{'text': 'Please provide a summary of the ebay title you provided. Provide information that a shopper would want to have'}]

        )

    except client.exceptions.AccessDeniedException:
        logger.error("Access denied accessing Amazon bedrock")
        return "error"
    
    except Exception as e:
        logger.error(f"Exception occurred accessing Amazon Bedrock: {e}")
        return "error"


    return response.json()

