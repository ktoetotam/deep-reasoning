from flask import Flask, Blueprint, request, jsonify, render_template
from app.api import api_bp
from dotenv import load_dotenv
import os
from openai import OpenAI
from app.tools import deep_researcher_no_flask as dr 
import re
import asyncio

# Load environment variables from .env file
load_dotenv()
load_dotenv("app/frontend/.env")
total_tok = 0
# Initialize the OpenAI client using environment variables
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



@api_bp.route('/hello', methods=['GET'])
def hello_api():
    return jsonify(message="Hello from the API!")


def convert_to_openai_format(conversation):
    openai_conversation = []
    for message in conversation:
        if message.startswith('User:'):
            role = 'user'
            content = message[len('User:'):].strip()
        elif message.startswith('Bot:'):
            role = 'assistant'
            content = message[len('Bot:'):].strip()
        else:
            raise ValueError(f"Unknown role in message: {message}")
        openai_conversation.append({"role": role, "content": content})
    return openai_conversation

def extract_think_content(text):
    match = re.search(r'<think>(.*?)</think>(.*)', text, re.DOTALL)
    if match:
        return [match.group(1).strip(), match.group(2).strip()]
    return [text]


def ask_openai(prompt, chat_history=None, model=None):
    """
    Sends a prompt (with optional chat history) to the OpenAI API and returns the response.
    If a chat_history list is provided, it is concatenated with the new prompt to form context.
    """
    if model is None:
        model = default_model
    
    global total_tok
    token_limit = 4096
    # If there is chat history, join it together with the new prompt.
    if chat_history and isinstance(chat_history, list):
        # Join previous messages (assumed to be strings) and append the new prompt.
        
        chat_history = convert_to_openai_format(chat_history)
        print("chat_history",chat_history)
        if len(chat_history) <= 1:
            chat_history.append({'role': 'user', 'content': prompt})
            total_tok = len(prompt.split())
    else:
            chat_history = {'role': 'user', 'content': prompt}

    try:
        response = client.chat.completions.create(
            model=model,
            messages=chat_history,
            max_tokens=token_limit
        )
        # Extract the assistant's reply from the response
        print("response",response)
        answer = response.choices[0].message.content

        total_tok += response.usage.total_tokens
        _, total_tok = trim_chat_history(chat_history, token_limit, total_tok)

        try:
            answer = extract_think_content(answer)
            if len(answer) == 2:
                answer = "Thoughts:" + "\n" + answer[0] + "\n\n\n" + "Answer:" + "\n" + answer[1]
                return answer
        except Exception as e:
            print(f"Error extracting think content: {e}")
        
        print("answer",answer, total_tok)
        return answer[0]
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return None

def trim_chat_history(chat_history, token_limit, total_tok):
    while total_tok > token_limit:
        chat_history.pop(0)
        total_tok = sum(len(message['content'].split()) for message in chat_history)
    return chat_history,total_tok


research_assistant = dr.ResearchAssistant(iteration_limit=1)
@api_bp.route('/research/chat', methods=['POST'])
def research_chat():

    data = request.get_json()
    print(data)
    user_query = data.get("prompt", "").strip()
    if not user_query:
        return jsonify({"error": "No query provided."}), 400

    try:
        # Run the asynchronous research routine.
        selected_model = data.get("model", default_model)
        research_assistant.model = selected_model
        print("Using model:", selected_model)
        final_report, links = asyncio.run(research_assistant.run_research(user_query))
        print(final_report, links)
        return jsonify({"report": final_report, "links": links})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@api_bp.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint to process chat messages.
    Expects JSON data with:
      - "prompt": The latest user message.
      - "history": (Optional) A list of previous messages.
      - "model": (Optional) A string with the desired model name.
    Returns a JSON response with the generated message.
    """
    data = request.get_json()
    print(data)
    # Retrieve the prompt, chat history, and model selection from the request data
    prompt = data.get("prompt", "")
    chat_history = data.get("history", [])
    selected_model = data.get("model", default_model)
    chatID = data.get("chatId", "")

    # Log incoming request for debugging
    print("Received prompt:", prompt)
    print("Chat history:", chat_history)
    print("Using model:", selected_model)

    # Get the LLM response using the ask_openai function
    answer = ask_openai(prompt, chat_history, model=selected_model)
    if answer is None:
        return jsonify({"error": "Error calling LLM API"}), 500

    # Return the answer (and optionally echo back the chat history)
    return jsonify({
        "response": answer,
        "history": chat_history + [prompt, answer]
    })
