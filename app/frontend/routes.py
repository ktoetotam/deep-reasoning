from flask import Flask, Blueprint, request, jsonify, render_template
import requests
import os
from openai import OpenAI

from app.frontend import frontend_bp


def write_api_key_to_env(api_key):
    with open('app/frontend/.env', 'w') as env_file:
        env_file.write(f"LLM_API_KEY={api_key}\n")



def initialize_openai_client():
    global client, default_model
    try:
        client = OpenAI(api_key=os.getenv("LLM_API_KEY"))
        default_model = os.getenv("LLM_MODEL_NAME") or "deepseek-r1-distill-qwen-7b"
        client.base_url = os.getenv("LLM_API_BASE")
        client.api_key = os.getenv("LLM_API_KEY")
        print("Model:", default_model)
        print("Base URL:", client.base_url)
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")

# Initialize the OpenAI client initially
initialize_openai_client()

@frontend_bp.route('/research.html')
def research():
    # Render the deep research interface.
    # Make sure that research.html exists in your "templates" folder.
    api_key = os.getenv("LLM_API_KEY")
    models = get_models(api_key)
    return render_template('research.html',models=models)

@frontend_bp.route('/set_api_key', methods=['POST'])
def set_api_key():
    data = request.get_json()
    api_key = data.get('apiKey')
    if api_key:
        os.environ["LLM_API_KEY"] = api_key
        print(api_key)
        write_api_key_to_env("\""+api_key+"\"")
        initialize_openai_client()  # Reinitialize the OpenAI client
        models = get_models(api_key)
        print(models)
        return render_template('index.html',models=models)
    return jsonify({"success": False})


@frontend_bp.route('/')
def index():
    api_key = os.getenv("LLM_API_KEY")
    models = get_models(api_key)
    return render_template('index.html',models=models)


def get_models(api_key, url="https://api.siemens.com/llm/v1/models"):
    """
    Fetches models from the Siemens API and returns a list of model IDs.
    
    Parameters:
        api_key (str): Your Siemens API key.
        url (str): The API endpoint URL.
    
    Returns:
        list: A list containing the model IDs retrieved from the API.
    """
    headers = {
        "apikey": api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        # Extract model IDs from the response
        model_ids = [model['id'] for model in data.get('data', []) if "embedd" not in model['id']  ]
        return model_ids
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return []
    

