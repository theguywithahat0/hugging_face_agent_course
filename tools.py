#!/usr/bin/env python3
"""
GAIA Custom Tools Module
Contains all custom tools for the GAIA agent
"""

import requests
from typing import Dict, Any
from smolagents import tool
from PIL import Image
from io import BytesIO

# Global variable for task context (shared with main agent)
current_task_context = {}

@tool
def get_task_context() -> str:
    """Get information about the current GAIA task"""
    global current_task_context
    if not current_task_context:
        return "No task context available"
    
    context_info = f"Task ID: {current_task_context.get('task_id', 'Unknown')}\n"
    context_info += f"Question: {current_task_context.get('Question', 'No question')}\n"
    context_info += f"File: {current_task_context.get('file_name', '')}\n"
    return context_info

@tool
def download_task_file(task_id: str) -> str:
    """Download the file associated with a GAIA task
    
    Args:
        task_id: The ID of the GAIA task to download files for
    """
    global current_task_context
    
    if not current_task_context.get('file_name'):
        return "No file associated with this task"
    
    file_name = current_task_context['file_name']
    
    try:
        # Try to download from GAIA API
        api_url = "https://agents-course-unit4-scoring.hf.space"
        file_url = f"{api_url}/files/{task_id}"
        
        print(f"🔄 Attempting to download file: {file_name}")
        print(f"📡 URL: {file_url}")
        
        response = requests.get(file_url, timeout=30)
        
        if response.status_code == 200:
            # Save file locally
            with open(file_name, 'wb') as f:
                f.write(response.content)
            print(f"✅ Downloaded: {file_name}")
            
            # If it's an image, try to process it
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                return f"Downloaded image file: {file_name}. Use analyze_image() to process it."
            else:
                return f"Downloaded file: {file_name} ({len(response.content)} bytes)"
        else:
            return f"Failed to download file: HTTP {response.status_code}"
            
    except Exception as e:
        return f"Error downloading file: {str(e)}"

@tool
def reverse_text(text: str) -> str:
    """Reverse text to handle backwards questions
    
    Args:
        text: The text to reverse
    """
    reversed_text = text[::-1]
    print(f"🔄 Reversed text: '{text}' -> '{reversed_text}'")
    return reversed_text

@tool
def analyze_image(image_path: str) -> str:
    """Analyze an image file to extract information
    
    Args:
        image_path: Path to the image file to analyze
    """
    try:
        # Load the image
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Basic image analysis
            width, height = img.size
            format_info = img.format if img.format else "Unknown"
            
            # Try to extract text if it's a text-based image
            analysis = f"Image Analysis for {image_path}:\n"
            analysis += f"- Dimensions: {width}x{height} pixels\n"
            analysis += f"- Format: {format_info}\n"
            analysis += f"- Mode: {img.mode}\n"
            
            # Let the LLM analyze the image content contextually
            # No hardcoded domain-specific logic needed
                
            return analysis
            
    except Exception as e:
        return f"Error analyzing image {image_path}: {str(e)}"

@tool
def transcribe_audio(file_path: str) -> str:
    """Transcribe an audio file to text using Hugging Face's ASR model.
    Args:
        file_path: path to the audio file
    """
    try:
        from transformers import pipeline
        transcriber = pipeline("automatic-speech-recognition", model="facebook/wav2vec2-base-960h")
        transcription = transcriber(file_path)
        return transcription["text"]
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"

@tool
def read_excel(file_path: str) -> str:
    """Read an Excel file and return its content as text.
    Args:
        file_path: path to the Excel file
    """
    try:
        import pandas as pd
        df = pd.read_excel(file_path)
        return df.to_string()
    except Exception as e:
        return f"Error reading Excel file: {str(e)}"

@tool
def add(a: int, b: int) -> float:
    """Add two numbers for calculations.
    Args:
        a: first number
        b: second number
    """
    return a + b

@tool
def multiply(a: int, b: int) -> float:
    """Multiply two numbers for calculations.
    Args:
        a: first number
        b: second number
    """
    return a * b

def create_rate_limited_search(search_tool, min_delay: float = 3.0):
    """Create a rate-limited search function to avoid DuckDuckGo blocks
    
    Args:
        search_tool: The base search tool to wrap
        min_delay: Minimum delay between searches in seconds
    """
    import time
    last_search_time = [0]  # Use list to make it mutable in closure
    
    def rate_limited_search(query: str) -> str:
        """Search with rate limiting to avoid DuckDuckGo blocks
        
        Args:
            query: The search query string
        """
        # Enforce delay between searches
        current_time = time.time()
        time_since_last = current_time - last_search_time[0]
        if time_since_last < min_delay:
            sleep_time = min_delay - time_since_last
            print(f"⏳ Waiting {sleep_time:.1f}s to avoid rate limiting...")
            time.sleep(sleep_time)
        
        print(f"🔍 Searching: {query}")
        try:
            result = search_tool(query)
            last_search_time[0] = time.time()
            return result
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return f"Search failed: {str(e)}"
    
    return rate_limited_search

def get_all_custom_tools():
    """Get all custom GAIA tools
    
    Returns:
        List of custom tools for the GAIA agent
    """
    return [
        get_task_context,
        download_task_file,
        reverse_text,
        analyze_image,
        transcribe_audio,
        read_excel,
        add,
        multiply
    ]

def set_task_context(task_context: Dict[str, Any]):
    """Set the global task context for tools to access
    
    Args:
        task_context: The current task context dictionary
    """
    global current_task_context
    current_task_context = task_context

def get_task_context_dict() -> Dict[str, Any]:
    """Get the current task context dictionary
    
    Returns:
        The current task context
    """
    global current_task_context
    return current_task_context 