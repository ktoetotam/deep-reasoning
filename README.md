# Deep Reasoning

This project is a Flask application with separated frontend and backend (API) blueprints.

## Installation

To set up the project, follow these steps:

### Prerequisites

- Python 3.11 or higher
- Poetry (for dependency management)

### Step 1: Clone the repository
```
curl -sSL https://install.python-poetry.org | python3 -
m https://github.com/mariasukhareva/llm-api-frontend.git
```
### Step 2: Install dependencies

Navigate to the project directory and install the dependencies using Poetry:

```sh
cd deep-reasoning
poetry install
```

### Step 3: Set up environment variables

Create a `.env` file in the project root and add the necessary environment variables:
```
OPENROUTER_API_KEY=YOURKEY
SERPAPI_API_KEY=YOURKEY
JINA_API_KEY=YOURKEY
GOOGLE_API_KEY=YOURKEY
GOOGLE_API_CX=YOURKEY
OPENROUTER_URL=https://openrouter.ai/api/v1/chat/completions
SERPAPI_URL=https://serpapi.com/search
JINA_BASE_URL=https://r.jina.ai/

DEFAULT_MODEL=mistral-7b-instruct

```


in 
```
touch app/frontend/.env
```
add your api key in the env files:

```
LLM_API_KEY="YOUR_API_KEY"
```
This can be your openAI api or any compatible API with openai 1.0


### Step 4: Run the application

```
python run.py
```

## Usage

Once the application is running, you can access it at `http://127.0.0.1:5000/`.

## Testing

To run the tests, use the following command:

```sh
poetry run pytest
```

