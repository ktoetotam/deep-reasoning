# LLM API Frontend

# LLM API Frontend

This project is a Flask application with separated frontend and backend (API) blueprints.

## Installation

To set up the project, follow these steps:

### Prerequisites

- Python 3.11 or higher
- Poetry (for dependency management)

### Step 1: Clone the repository

curl -sSL https://install.python-poetry.org | python3 -
```
m https://github.com/mariasukhareva/llm-api-frontend.git
```
### Step 2: Install dependencies

Navigate to the project directory and install the dependencies using Poetry:

```sh
cd llm-api-frontend
poetry install
```

### Step 3: Set up environment variables

Create a `.env` file in the project root and add the necessary environment variables:

in llm-api-frontend/llm-api-frontend/app/frontend/.env
```
touch llm-api-frontend/llm-api-frontend/app/frontend/.env
```
add your api key in the env files:

```
LLM_API_KEY="YOUR_API_KEY"
```


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

