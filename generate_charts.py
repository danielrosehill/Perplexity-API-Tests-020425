#!/usr/bin/env python3
"""
Script to generate charts for the README based on test results.
"""

import os
import re
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Path configuration
REPO_ROOT = Path(__file__).parent
OUTPUTS_DIR = REPO_ROOT / "outputs"
DEBUG_DIR = REPO_ROOT / "debug_logs"
CHARTS_DIR = REPO_ROOT / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

# Define model names for display (without API provider prefixes)
MODEL_DISPLAY_NAMES = {
    "perplexity/sonar-deep-research": "Sonar Deep Research",
    "perplexity/sonar-reasoning-pro": "Sonar Reasoning Pro",
    "perplexity/sonar-pro": "Sonar Pro",
    "perplexity/sonar-reasoning": "Sonar Reasoning",
    "perplexity/sonar": "Sonar",
    "google/gemini-2.0-flash-001": "Gemini 2.0 Flash"
}

# Define citation counts from the README table
CITATION_COUNTS = {
    # Data Research prompt
    ("data-research", "google/gemini-2.0-flash-001", "OpenRouter"): 0,
    ("data-research", "perplexity/sonar", "OpenRouter"): 5,
    ("data-research", "perplexity/sonar", "Perplexity"): 5,
    ("data-research", "perplexity/sonar-deep-research", "OpenRouter"): 16,
    ("data-research", "perplexity/sonar-deep-research", "Perplexity"): 16,
    ("data-research", "perplexity/sonar-pro", "OpenRouter"): 10,
    ("data-research", "perplexity/sonar-pro", "Perplexity"): 10,
    ("data-research", "perplexity/sonar-reasoning", "OpenRouter"): 5,
    ("data-research", "perplexity/sonar-reasoning", "Perplexity"): 5,
    ("data-research", "perplexity/sonar-reasoning-pro", "OpenRouter"): 10,
    ("data-research", "perplexity/sonar-reasoning-pro", "Perplexity"): 10,
    
    # Puerto Rico NYE prompt
    ("puerto-rico-nye", "google/gemini-2.0-flash-001", "OpenRouter"): 0,
    ("puerto-rico-nye", "perplexity/sonar", "OpenRouter"): 5,
    ("puerto-rico-nye", "perplexity/sonar", "Perplexity"): 5,
    ("puerto-rico-nye", "perplexity/sonar-deep-research", "OpenRouter"): 15,
    ("puerto-rico-nye", "perplexity/sonar-deep-research", "Perplexity"): 16,
    ("puerto-rico-nye", "perplexity/sonar-pro", "OpenRouter"): 10,
    ("puerto-rico-nye", "perplexity/sonar-pro", "Perplexity"): 10,
    ("puerto-rico-nye", "perplexity/sonar-reasoning", "OpenRouter"): 5,
    ("puerto-rico-nye", "perplexity/sonar-reasoning", "Perplexity"): 5,
    ("puerto-rico-nye", "perplexity/sonar-reasoning-pro", "OpenRouter"): 10,
    ("puerto-rico-nye", "perplexity/sonar-reasoning-pro", "Perplexity"): 10,
}

def extract_data_from_outputs():
    """Extract data from output files for visualization."""
    data = []
    
    # First, get basic metadata from output files
    for file_path in OUTPUTS_DIR.glob("*.md"):
        with open(file_path, 'r') as f:
            content = f.read()
            
            # Extract metadata
            prompt_match = re.search(r'# (.*?) - (.*?)$', content, re.MULTILINE)
            api_match = re.search(r'## API\n(.*?)$', content, re.MULTILINE)
            
            if prompt_match and api_match:
                prompt_name = prompt_match.group(1)
                model_name = prompt_match.group(2)
                api_name = api_match.group(1).strip()
                
                # Extract output text for word count
                output_match = re.search(r'## Output\n(.*?)(?:\n## Citations|\Z)', content, re.MULTILINE | re.DOTALL)
                word_count = 0
                if output_match:
                    output_text = output_match.group(1).strip()
                    word_count = len(output_text.split())
                
                # Get citation count from predefined data
                citation_count = CITATION_COUNTS.get((prompt_name, model_name, api_name), 0)
                has_citations = citation_count > 0
                
                # Add to data
                data.append({
                    "prompt_name": prompt_name,
                    "model_name": model_name,
                    "display_name": MODEL_DISPLAY_NAMES.get(model_name, model_name),
                    "api_name": api_name,
                    "word_count": word_count,
                    "citation_count": citation_count,
                    "has_citations": has_citations
                })
    
    return pd.DataFrame(data)

def create_citation_chart(df, prompt_name=None):
    """Create a chart showing citations per model."""
    # Filter by prompt if specified
    if prompt_name:
        filtered_df = df[df['prompt_name'] == prompt_name]
        title_suffix = f" - {prompt_name} Prompt"
        filename_suffix = f"_{prompt_name.lower().replace(' ', '_')}"
    else:
        filtered_df = df
        title_suffix = ""
        filename_suffix = "_all"
    
    # Create a new DataFrame with unique model names
    models = filtered_df['display_name'].unique()
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Set width of bars
    bar_width = 0.35
    
    # Set positions of the bars on X axis
    r1 = range(len(models))
    r2 = [x + bar_width for x in r1]
    
    # Create bars for OpenRouter and Perplexity
    openrouter_data = []
    perplexity_data = []
    
    for model in models:
        # Get OpenRouter data
        or_row = filtered_df[(filtered_df['display_name'] == model) & (filtered_df['api_name'] == 'OpenRouter')]
        if not or_row.empty:
            openrouter_data.append(or_row['citation_count'].values[0])
        else:
            openrouter_data.append(0)
        
        # Get Perplexity data
        plex_row = filtered_df[(filtered_df['display_name'] == model) & (filtered_df['api_name'] == 'Perplexity')]
        if not plex_row.empty:
            perplexity_data.append(plex_row['citation_count'].values[0])
        else:
            perplexity_data.append(0)
    
    # Create bars
    ax.bar(r1, openrouter_data, width=bar_width, label='OpenRouter', color='skyblue')
    ax.bar(r2, perplexity_data, width=bar_width, label='Perplexity', color='lightcoral')
    
    # Add labels and title
    ax.set_xlabel('Model', fontsize=12)
    ax.set_ylabel('Number of Citations', fontsize=12)
    ax.set_title(f'Citations Per Model{title_suffix}', fontsize=16)
    ax.set_xticks([r + bar_width/2 for r in range(len(models))])
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.legend()
    
    plt.tight_layout()
    
    # Save chart
    plt.savefig(CHARTS_DIR / f"citations_per_model{filename_suffix}.png", dpi=300, bbox_inches='tight')
    plt.close()

def create_word_count_chart(df, prompt_name=None):
    """Create a chart showing word count per model."""
    # Filter by prompt if specified
    if prompt_name:
        filtered_df = df[df['prompt_name'] == prompt_name]
        title_suffix = f" - {prompt_name} Prompt"
        filename_suffix = f"_{prompt_name.lower().replace(' ', '_')}"
    else:
        filtered_df = df
        title_suffix = ""
        filename_suffix = "_all"
    
    # Create a new DataFrame with unique model names
    models = filtered_df['display_name'].unique()
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Set width of bars
    bar_width = 0.35
    
    # Set positions of the bars on X axis
    r1 = range(len(models))
    r2 = [x + bar_width for x in r1]
    
    # Create bars for OpenRouter and Perplexity
    openrouter_data = []
    perplexity_data = []
    
    for model in models:
        # Get OpenRouter data
        or_row = filtered_df[(filtered_df['display_name'] == model) & (filtered_df['api_name'] == 'OpenRouter')]
        if not or_row.empty:
            openrouter_data.append(or_row['word_count'].values[0])
        else:
            openrouter_data.append(0)
        
        # Get Perplexity data
        plex_row = filtered_df[(filtered_df['display_name'] == model) & (filtered_df['api_name'] == 'Perplexity')]
        if not plex_row.empty:
            perplexity_data.append(plex_row['word_count'].values[0])
        else:
            perplexity_data.append(0)
    
    # Create bars
    ax.bar(r1, openrouter_data, width=bar_width, label='OpenRouter', color='skyblue')
    ax.bar(r2, perplexity_data, width=bar_width, label='Perplexity', color='lightcoral')
    
    # Add labels and title
    ax.set_xlabel('Model', fontsize=12)
    ax.set_ylabel('Word Count', fontsize=12)
    ax.set_title(f'Word Count Per Model{title_suffix}', fontsize=16)
    ax.set_xticks([r + bar_width/2 for r in range(len(models))])
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.legend()
    
    plt.tight_layout()
    
    # Save chart
    plt.savefig(CHARTS_DIR / f"word_count_per_model{filename_suffix}.png", dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Main function to generate all charts."""
    # Extract data
    df = extract_data_from_outputs()
    
    # Print the data for verification
    print("Data extracted for visualization:")
    print(df[['prompt_name', 'model_name', 'api_name', 'word_count', 'citation_count', 'has_citations']].to_string())
    
    # Create overall charts
    create_citation_chart(df)
    create_word_count_chart(df)
    
    # Create prompt-specific charts
    for prompt_name in df['prompt_name'].unique():
        create_citation_chart(df, prompt_name)
        create_word_count_chart(df, prompt_name)
    
    print(f"Charts generated in the {CHARTS_DIR} directory.")

if __name__ == "__main__":
    main()
