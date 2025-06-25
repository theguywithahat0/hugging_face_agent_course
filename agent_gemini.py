#!/usr/bin/env python3
"""
GAIA Agent with Google Gemini 2.5 Flash
High-performance agent using Google's latest Gemini model for superior reasoning
"""

import os
from typing import Dict, Any
from smolagents import CodeAgent, DuckDuckGoSearchTool, VisitWebpageTool, tool
from smolagents import LiteLLMModel
from tools import get_all_custom_tools, set_task_context, create_rate_limited_search

class Agent:
    def __init__(self, api_key=None):
        """Initialize the agent with Gemini 2.5 Flash"""
        print("🚀 Initializing Gemini Agent...")
        
        # Set up Gemini API key
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Please provide a Gemini API key either as parameter or set GEMINI_API_KEY environment variable")
        os.environ["GEMINI_API_KEY"] = api_key
        
        # Initialize Gemini 2.5 Flash model
        try:
            self.model = LiteLLMModel(
                model_id="gemini/gemini-2.5-flash",
                api_key=api_key,
                temperature=0.1,  # Low temperature for consistent reasoning
            )
            print("✅ Gemini 2.5 Flash model initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini model: {e}")
            print("💡 Make sure your API key is valid and you have access to Gemini 2.5 Flash")
            raise
        
        # Create rate-limited search tool
        search_tool = DuckDuckGoSearchTool()
        rate_limited_search_func = create_rate_limited_search(search_tool)
        rate_limited_search_tool = tool(rate_limited_search_func)
        
        # Get all custom tools from dedicated module
        custom_tools = get_all_custom_tools()
        
        # Create agent with custom tools + smolagents default toolbox
        self.agent = CodeAgent(
            tools=custom_tools + [
                rate_limited_search_tool,
                VisitWebpageTool()
            ],
            model=self.model,
            max_steps=8,  # Increased for Gemini's better reasoning
            verbosity_level=1,
            additional_authorized_imports=["pandas", "numpy", "openpyxl", "requests", "json", "csv", "re"]
        )
        
        print("✅ Gemini Agent initialized successfully!")
        print("🔧 Available tools:")
        print("   - Custom: get_task_context, download_task_file, reverse_text, analyze_image")
        print("   - Search: rate_limited_search (DuckDuckGo with delays)")
        print("   - Web: visit_webpage")
        print("   - Math: add, multiply")
        print("   - Audio: transcribe_audio")
        print("   - Excel: read_excel")

    def solve_task(self, task: Dict[str, Any]) -> str:
        """Solve a GAIA task using Gemini 2.5 Flash"""
        print(f"\n🎯 Solving task: {task.get('task_id', 'Unknown')}")
        question = task.get("Question", "")
        file_name = task.get("file_name", "")
        task_id = task.get("task_id", "")
        
        # Set task context for tools
        task_context = {
            "task_id": task_id,
            "Question": question,
            "file_name": file_name
        }
        set_task_context(task_context)
        
        # Prepare file information
        file_info = ""
        if file_name and file_name.strip():
            file_info = f"\nFILE AVAILABLE: {file_name}\n- Use get_task_context() to download and analyze this file\n- File may contain crucial information for answering the question\n"
        
        # Enhanced prompt with Gemini-specific optimizations
        smart_prompt = f"""QUESTION: {question}

You are a GAIA benchmark agent powered by Gemini 2.5 Flash. Use your superior reasoning capabilities to solve this efficiently.

CRITICAL SUCCESS FACTORS:
1. CONCISE ANSWERS ONLY: Single words, numbers, or short phrases
2. VERIFY with multiple sources when possible
3. For reverse text: Use reverse_text() tool, don't manually reverse
4. For counting: Extract exact numbers, not estimates
5. For factual questions: Check Wikipedia first, then search engines

REASONING PATTERNS FOR GEMINI:

REVERSE TEXT (100% accuracy expected):
- Questions with backwards text like ".rewsna eht sa "tfel" drow eht fo etisoppo eht etirw"
- Use reverse_text() tool: reverse_text(".rewsna eht sa \"tfel\" drow eht fo etisoppo eht etirw")
- Extract the forward question, then answer it

COUNTING TASKS (High accuracy expected):
- "How many X did Y do?" → Search for comprehensive lists
- Look for official discographies, filmographies, complete records
- Count discrete items, not mentions

FACTUAL QUESTIONS (High accuracy expected):
- Use Wikipedia for authoritative information
- Cross-reference with official sources
- For dates: Look for birth/death dates, founding dates
- For locations: Check official geography sources

RESEARCH QUESTIONS (Medium accuracy):
- Start with Wikipedia for background
- Use specific search terms
- Look for official sources and primary materials

FILE PROCESSING:
- Always use get_task_context() if file_name is provided
- Files often contain the complete answer
- For Excel: Use read_excel() tool
- For images: Use analyze_image() tool  
- For audio: Use transcribe_audio() tool

GEMINI OPTIMIZATION TIPS:
1. Break complex problems into clear steps
2. Use your reasoning to identify question type first
3. Leverage your knowledge base before searching
4. Cross-validate information when uncertain
5. Be decisive - avoid overthinking simple questions

MANDATORY RESPONSE FORMAT:
1. Write ONLY Python code in ```python blocks
2. NO <think> tags, NO explanations outside code
3. NO verbose text, NO commentary
4. ACTUALLY use the tools, don't just print about them

AVAILABLE TOOLS:
- rate_limited_search(query): Search the web
- visit_webpage(url): Get webpage content  
- get_task_context(): Get task info and download files
- download_task_file(task_id): Download task files
- reverse_text(text): Reverse text
- analyze_image(image_path): Analyze images
- transcribe_audio(file_path): Transcribe audio files
- read_excel(file_path): Read Excel files
- add(a, b): Add numbers
- multiply(a, b): Multiply numbers

EXACT FORMAT TO FOLLOW:

```python
# Step 1: ANALYZE QUESTION TYPE
print("ANALYZE: [brief question type identification]")

# Step 2: PLAN APPROACH
print("PLAN: [which tools/approach to use]")

# Step 3: EXECUTE WITH TOOLS
print("EXECUTE: [action]")
# ACTUALLY call the tools here - don't just print about it
result = rate_limited_search("specific query")  # or other appropriate tool
print(result)

# Step 4: EXTRACT ANSWER
print("ANSWER: [brief extraction logic]")
final_answer("direct_answer_only")
```

ANSWER EXAMPLES:
- "Capital of France?" → final_answer("Paris")
- "How many albums?" → final_answer("5")  
- "Reverse 'hello'?" → final_answer("olleh")
- "What year?" → final_answer("1987")

ABSOLUTELY FORBIDDEN:
- <think> tags or similar
- Long explanations 
- "The answer is..." phrases
- Making up answers without verification
- Verbose responses
- Text outside ```python blocks

{file_info}

GEMINI: Use your advanced reasoning to solve this efficiently and accurately.

RESPOND WITH PYTHON CODE ONLY:"""
        
        try:
            print("🚀 Starting Gemini agent execution...")
            result = self.agent.run(smart_prompt)
            print(f"📝 Final answer: {result}")
            return str(result)
            
        except Exception as e:
            print(f"❌ Error solving task: {e}")
            return f"Error: {str(e)}"

if __name__ == "__main__":
    # Test the agent
    print("🧪 Testing Gemini Agent...")
    
    try:
        agent = Agent()
        
        # Test simple question
        test_task = {
            "task_id": "test_001",
            "Question": "What is the capital of France?", 
            "file_name": ""
        }
        
        result = agent.solve_task(test_task)
        print(f"✅ Test result: {result}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}") 