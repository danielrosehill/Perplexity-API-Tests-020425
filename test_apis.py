#!/usr/bin/env python3
"""
Script to test various research-capable APIs with test prompts.
"""

import os
import json
import time
import datetime
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get API keys from environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")  # Using the env var name as provided

# Define model endpoints
PERPLEXITY_MODELS = [
    "perplexity/sonar-deep-research",
    "perplexity/sonar-reasoning-pro",
    "perplexity/sonar-pro",
    "perplexity/sonar-reasoning",
    "perplexity/sonar",
    "google/gemini-2.0-flash-001"  # Control model via OpenRouter
]

# Direct Perplexity API model mapping
DIRECT_PERPLEXITY_MODELS = {
    "perplexity/sonar-deep-research": "sonar-deep-research",
    "perplexity/sonar-reasoning-pro": "sonar-reasoning-pro",
    "perplexity/sonar-pro": "sonar-pro",
    "perplexity/sonar-reasoning": "sonar-reasoning",
    "perplexity/sonar": "sonar"
}

# Path configuration
REPO_ROOT = Path(__file__).parent
PROMPTS_DIR = REPO_ROOT / "test-prompts"
OUTPUTS_DIR = REPO_ROOT / "outputs"
DEBUG_DIR = REPO_ROOT / "debug_logs"

# Ensure directories exist
OUTPUTS_DIR.mkdir(exist_ok=True)
DEBUG_DIR.mkdir(exist_ok=True)

def load_prompt(prompt_file):
    """Load prompt content from file."""
    with open(PROMPTS_DIR / prompt_file, 'r') as f:
        return f.read().strip()

def get_prompt_name(prompt_file):
    """Extract prompt name from filename."""
    return Path(prompt_file).stem

def save_debug_info(prompt_name, model_name, api_name, response_data):
    """Save raw API response for debugging."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_model_name = model_name.replace('/', '-')
    
    debug_filename = f"{prompt_name}_{clean_model_name}_{api_name.lower()}_{timestamp}_debug.json"
    
    # Remove identifiable information before saving
    if isinstance(response_data, dict):
        # Remove id and created timestamp if they exist
        if "id" in response_data:
            del response_data["id"]
        if "created" in response_data:
            del response_data["created"]
    
    with open(DEBUG_DIR / debug_filename, 'w') as f:
        json.dump(response_data, f, indent=2, default=str)
    
    print(f"Saved debug info to {debug_filename}")

def extract_citations_from_text(text):
    """Attempt to extract citations from text if they're included inline."""
    # This is a simple extraction method - might need refinement based on actual response formats
    citations = []
    citation_section = False
    
    lines = text.split('\n')
    for line in lines:
        # Check if we've reached a citations/references section
        if any(header in line.lower() for header in ['## citations', '## references', '# citations', '# references']):
            citation_section = True
            continue
        
        if citation_section and line.strip():
            # Skip section headers
            if line.startswith('#'):
                continue
            citations.append(line.strip())
    
    return citations if citations else None

def save_output(prompt_name, model_name, api_name, endpoint, prompt_text, output_text, citations=None):
    """Save output to markdown file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Clean model name for filename
    clean_model_name = model_name.replace('/', '-')
    
    # Create filename
    filename = f"{prompt_name}_{clean_model_name}_{api_name.lower()}.md"
    
    # Format content
    content = f"""# {prompt_name} - {model_name}

## API
{api_name}

## Endpoint
{endpoint}

## Timestamp
{timestamp}

## Prompt
{prompt_text}

## Output
{output_text}
"""

    # Add citations if available
    if citations:
        content += "\n## Citations\n"
        for i, citation in enumerate(citations, 1):
            content += f"[{i}] {citation}\n"
    
    # Save to file
    with open(OUTPUTS_DIR / filename, 'w') as f:
        f.write(content)
    
    print(f"Saved output to {filename}")

def test_openrouter(prompt_text, prompt_name, model):
    """Test OpenRouter API with the given prompt and model."""
    if not OPENROUTER_API_KEY:
        print("OpenRouter API key not found. Skipping OpenRouter test.")
        return
    
    print(f"Testing OpenRouter with model: {model}")
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        # Save raw response for debugging
        save_debug_info(prompt_name, model, "OpenRouter", response.model_dump())
        
        output_text = response.choices[0].message.content
        
        # Try to extract citations from the response object if available
        citations = None
        if hasattr(response, 'citations') and response.citations:
            citations = response.citations
        else:
            # Try to extract citations from the text content
            citations = extract_citations_from_text(output_text)
        
        save_output(
            prompt_name=prompt_name,
            model_name=model,
            api_name="OpenRouter",
            endpoint=f"https://openrouter.ai/api/v1/chat/completions",
            prompt_text=prompt_text,
            output_text=output_text,
            citations=citations
        )
        
    except Exception as e:
        print(f"Error testing OpenRouter with model {model}: {e}")

def test_perplexity_direct(prompt_text, prompt_name, model):
    """Test Perplexity API directly with the given prompt and model."""
    if not PERPLEXITY_API_KEY:
        print("Perplexity API key not found. Skipping direct Perplexity test.")
        return
    
    # Skip if not a Perplexity model
    if model not in DIRECT_PERPLEXITY_MODELS:
        print(f"Skipping direct Perplexity test for non-Perplexity model: {model}")
        return
    
    direct_model = DIRECT_PERPLEXITY_MODELS[model]
    print(f"Testing Perplexity API directly with model: {direct_model}")
    
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": direct_model,
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=data
        )
        
        response_data = response.json()
        
        # Save raw response for debugging
        save_debug_info(prompt_name, model, "Perplexity", response_data)
        
        if 'error' in response_data:
            print(f"Error from Perplexity API: {response_data['error']}")
            return
        
        output_text = response_data['choices'][0]['message']['content']
        
        # Try to extract citations if available in the response
        citations = None
        if 'citations' in response_data:
            citations = response_data['citations']
        elif 'links' in response_data:
            citations = response_data['links']
        else:
            # Try to extract citations from the text content
            citations = extract_citations_from_text(output_text)
        
        save_output(
            prompt_name=prompt_name,
            model_name=model,
            api_name="Perplexity",
            endpoint="https://api.perplexity.ai/chat/completions",
            prompt_text=prompt_text,
            output_text=output_text,
            citations=citations
        )
        
    except Exception as e:
        print(f"Error testing Perplexity API with model {direct_model}: {e}")

def main():
    """Main function to run all tests."""
    parser = argparse.ArgumentParser(description='Test research-capable APIs with test prompts')
    parser.add_argument('--openrouter', action='store_true', help='Test models via OpenRouter')
    parser.add_argument('--perplexity', action='store_true', help='Test models via Perplexity API directly')
    parser.add_argument('--include-control', action='store_true', help='Include control models (e.g., Google Gemini)')
    parser.add_argument('--model', help='Test only a specific model (e.g., perplexity/sonar-deep-research)')
    parser.add_argument('--prompt', help='Test only a specific prompt file (e.g., data-research.md)')
    
    args = parser.parse_args()
    
    # If neither API is specified, test both
    if not args.openrouter and not args.perplexity:
        args.openrouter = True
        args.perplexity = True
    
    # Get test prompt files
    if args.prompt:
        prompt_files = [args.prompt]
        if not (PROMPTS_DIR / args.prompt).exists():
            print(f"Error: Prompt file {args.prompt} not found in {PROMPTS_DIR}")
            return
    else:
        prompt_files = [f for f in os.listdir(PROMPTS_DIR) if f.endswith('.md')]
    
    if not prompt_files:
        print("No test prompts found.")
        return
    
    print(f"Found {len(prompt_files)} test prompts: {prompt_files}")
    
    # Determine which models to test
    models_to_test = []
    if args.model:
        if args.model in PERPLEXITY_MODELS or (args.include_control and args.model in ["google/gemini-2.0-flash-001"]):
            models_to_test.append(args.model)
        else:
            print(f"Error: Model {args.model} not found in available models")
            return
    else:
        models_to_test.extend(PERPLEXITY_MODELS)
        if args.include_control:
            models_to_test.append("google/gemini-2.0-flash-001")
    
    # Test each prompt with each model
    for prompt_file in prompt_files:
        prompt_text = load_prompt(prompt_file)
        prompt_name = get_prompt_name(prompt_file)
        
        print(f"\nTesting prompt: {prompt_name}")
        
        for model in models_to_test:
            # Test via OpenRouter if specified
            if args.openrouter:
                test_openrouter(prompt_text, prompt_name, model)
            
            # Test via Perplexity API directly if specified and it's a Perplexity model
            if args.perplexity and "perplexity" in model:
                test_perplexity_direct(prompt_text, prompt_name, model)
            
            # Add a small delay between API calls to avoid rate limits
            time.sleep(2)

if __name__ == "__main__":
    main()
