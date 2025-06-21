#!/usr/bin/env python3
"""
Ultra Minimal GAIA Agent - Standalone
Uses smolagents default toolbox with smart prompting instead of custom tools
"""

import requests
from typing import Dict, Any
from smolagents import CodeAgent, tool
from ollama_model import OllamaModel

# Current task context (global for tool access)
current_task_context = {}

@tool
def get_task_context() -> str:
    """Get information about the current GAIA task"""
    global current_task_context
    if not current_task_context:
        return "No task context available"
    
    context_info = f"Task ID: {current_task_context.get('task_id', 'Unknown')}\n"
    context_info += f"Question: {current_task_context.get('Question', 'No question')}\n"
    context_info += f"File: {current_task_context.get('file_name', 'No file')}"
    return context_info

@tool
def download_task_file(task_id: str) -> str:
    """Download file associated with GAIA task (placeholder - implement as needed)
    
    Args:
        task_id: The ID of the GAIA task to download files for
    """
    return f"File download for task {task_id} not implemented yet"

class GAIAAgent:
    """Ultra minimal GAIA agent using smolagents default toolbox + smart prompting"""
    
    def __init__(self):
        print("🤖 Initializing Ultra Minimal GAIA Agent...")
        
        # Initialize Ollama model with auto-detection
        from ollama_model import find_best_model
        best_model = find_best_model(["qwen2.5-coder:32b", "qwen2.5-coder:7b", "llama3.1:8b"])
        print(f"✅ Found preferred model: {best_model}")
        self.model = OllamaModel(model_name=best_model)
        
        # Create agent with minimal custom tools + smolagents default toolbox
        from smolagents import DuckDuckGoSearchTool, VisitWebpageTool
        
        self.agent = CodeAgent(
            tools=[
                get_task_context, 
                download_task_file,
                DuckDuckGoSearchTool(),
                VisitWebpageTool()
            ],
            model=self.model,
            max_steps=15,  # Enough steps for complex research
            verbosity_level=1
        )
        
        print("✅ Ultra minimal GAIA Agent initialized!")
        print("🔧 Available tools:")
        print("   - PythonInterpreterTool: Data analysis, file processing")
        print("   - DuckDuckGoSearchTool/GoogleSearchTool: Web search")
        print("   - VisitWebpageTool: Web content extraction")
        print("   - get_task_context: Get task info")
        print("   - download_task_file: Download GAIA files")
    
    def solve_task(self, task: Dict[str, Any]) -> str:
        """Solve a GAIA task using smart prompting + default toolbox"""
        global current_task_context
        current_task_context = task
        
        task_id = task.get("task_id", "unknown")
        question = task.get("Question", "")
        file_name = task.get("file_name", "")
        
        print(f"\n{'='*60}")
        print(f"🎯 Solving GAIA Task: {task_id}")
        print(f"❓ Question: {question}")
        print(f"{'='*60}")
        
        # Smart prompt that teaches the agent common patterns
        smart_prompt = f"""You are solving a GAIA benchmark question. Use the available tools effectively:

QUESTION: {question}

AVAILABLE TOOLS:
1. **web_search(query)**: Search the web for information using DuckDuckGo
2. **visit_webpage(url)**: Extract content from web pages
3. **get_task_context()**: Get task info and download associated files if needed
4. **download_task_file(task_id)**: Download files associated with this task
5. **final_answer(answer)**: Provide the final answer

IMPORTANT: Use tools by calling them as functions in your code:
- web_search("your search query")
- visit_webpage("https://example.com")
- get_task_context()
- download_task_file("task_id")

SMART PATTERNS FOR COMMON TASKS:

🔍 **URL EXTRACTION FROM SEARCH RESULTS**:
Search results are in markdown format like [Title](URL). Extract URLs like this:
```python
import re
# Extract URLs from markdown links: [Title](URL)
urls = re.findall(r'\\[([^\\]]+)\\]\\(([^)]+)\\)', search_results)
relevant_urls = []
for title, url in urls:
    if 'relevant_keyword' in title.lower():  # Filter by relevance
        relevant_urls.append(url)
```

📊 **COUNTING/DISCOGRAPHY QUESTIONS**:
For "how many X between Y and Z" questions:
```python
# 1. Search for comprehensive sources
search_results = web_search("Artist Name complete discography albums")

# 2. Visit multiple sources for cross-validation
sources_data = []
for title, url in urls[:3]:  # Top 3 sources
    if 'discography' in title.lower() or 'albums' in title.lower():
        content = visit_webpage(url)
        
                 # 3. Find years in content  
         years = re.findall(r'\\b(19\\d{{2}}|20\\d{{2}})\\b', content)
        
        # 4. Find items in date range
        items_in_range = []
        for year in years:
            year_int = int(year)
            if {2000} <= year_int <= {2009}:  # Example range
                # Look for album context around this year
                # This is where human reasoning beats hardcoded patterns
                items_in_range.append(year_int)
        
        sources_data.append({{'url': url, 'years': items_in_range}})

# 5. Cross-validate between sources
final_count = len(set(all_years_found))  # Your reasoning here
```

🧮 **NUMERICAL/CALCULATION QUESTIONS**:
Use Python for any calculations:
```python
# Extract numbers and calculate
numbers = re.findall(r'\\d+(?:\\.\\d+)?', text)
result = sum(float(n) for n in numbers)
```

📁 **FILE-BASED QUESTIONS**:
If there's a file, always download it first:
```python
if file_name:
    file_content = download_task_file(task_id)
    # Process file content...
```

APPROACH:
1. If there's a file associated with this task, download it first
2. Use web_search() to find comprehensive information
3. Use visit_webpage() to extract content from multiple relevant sources
4. Use Python code to process, filter, and analyze data
5. Cross-validate findings from multiple sources when possible
6. Provide a clear, factual answer using final_answer()

FILE INFO: {f"File: {file_name}" if file_name else "No file associated with this task"}

Think step by step, use multiple sources for validation, and rely on your reasoning rather than hardcoded patterns.
"""
        
        try:
            print("🚀 Starting agent execution...")
            result = self.agent.run(smart_prompt)
            print(f"📝 Result: {result}")
            return str(result)
            
        except Exception as e:
            error_msg = f"Error solving task: {e}"
            print(f"❌ {error_msg}")
            return error_msg

if __name__ == "__main__":
    # Simple test when run directly
    agent = GAIAAgent()
    
    test_task = {
        "task_id": "standalone_test",
        "Question": "What is the capital of France?",
        "file_name": ""
    }
    
    result = agent.solve_task(test_task)
    print(f"\n🎯 Final Result: {result}") 