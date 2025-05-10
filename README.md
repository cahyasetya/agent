# Python Agents Project

A project for exploring agent-based systems in Python.

## Setup

1. Ensure pyenv is installed
2. Set up the environment:
   ```bash
   # Create virtual environment (if not already created)
   pyenv virtualenv 3.10.0 agents-env
   
   # Activate the environment
   pyenv local agents-env
   
   # Install dependencies
   pip install -r requirements.txt
   ```

## Usage

Run the main agent:
```bash
python agent.py
```

## Environment Variables

Configure the `.env` file to set up your environment variables:
- `DEBUG`: Toggle debug mode
- `API_ENDPOINT`: The API endpoint for external services
- `MODEL_PATH`: Path to the agent model