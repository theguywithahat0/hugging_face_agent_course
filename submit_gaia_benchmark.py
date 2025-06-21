#!/usr/bin/env python3
"""
Official GAIA Benchmark Submission Script
Runs our ultra-minimal agent on all GAIA questions and submits to HF API
"""

import os
import requests
import json
import time
from gaia_agent import GAIAAgent

# API Configuration
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"

def get_huggingface_credentials():
    """Get Hugging Face credentials from user"""
    print("🔐 Hugging Face Authentication Required")
    print("=" * 50)
    
    username = input("Enter your Hugging Face username: ").strip()
    if not username:
        print("❌ Username is required!")
        return None, None
    
    # For the submission, we need the agent code URL
    # This should point to your public repository
    agent_code_url = input("Enter your agent code URL (GitHub/HF repo): ").strip()
    if not agent_code_url:
        # Default to a placeholder - you should replace this with your actual repo
        agent_code_url = "https://github.com/your-username/your-gaia-agent"
        print(f"⚠️  Using placeholder URL: {agent_code_url}")
        print("   Please update this with your actual repository URL")
    
    return username, agent_code_url

def fetch_all_gaia_questions():
    """Fetch all GAIA questions from the API"""
    api_url = DEFAULT_API_URL
    questions_url = f"{api_url}/questions"
    
    print("🔄 Fetching all GAIA questions from official API...")
    print(f"📡 URL: {questions_url}")
    
    try:
        response = requests.get(questions_url, timeout=30)
        response.raise_for_status()
        questions_data = response.json()
        
        if not questions_data:
            print("❌ No questions received from API")
            return []
            
        print(f"✅ Successfully fetched {len(questions_data)} GAIA questions!")
        return questions_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching questions: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON response: {e}")
        return []

def run_agent_on_all_questions(questions):
    """Run our agent on all GAIA questions"""
    print(f"\n🤖 Running Ultra-Minimal GAIA Agent on {len(questions)} questions")
    print("=" * 60)
    
    agent = GAIAAgent()
    results = []
    answers_payload = []
    
    for i, question_data in enumerate(questions):
        task_id = question_data.get("task_id")
        question_text = question_data.get("question")
        file_name = question_data.get("file_name", "")
        
        if not task_id or question_text is None:
            print(f"⚠️  Skipping question {i+1}: Missing task_id or question")
            continue
        
        print(f"\n{'='*60}")
        print(f"🎯 Question {i+1}/{len(questions)}")
        print(f"📋 Task ID: {task_id}")
        print(f"❓ Question: {question_text[:100]}{'...' if len(question_text) > 100 else ''}")
        if file_name:
            print(f"📁 File: {file_name}")
        print(f"{'='*60}")
        
        # Create task in the format our agent expects
        task = {
            "task_id": task_id,
            "Question": question_text,
            "file_name": file_name
        }
        
        start_time = time.time()
        try:
            result = agent.solve_task(task)
            duration = time.time() - start_time
            
            # Add to submission payload
            answers_payload.append({
                "task_id": task_id, 
                "submitted_answer": str(result)
            })
            
            # Add to results log
            results.append({
                "task_id": task_id,
                "question": question_text,
                "result": result,
                "duration": duration,
                "success": True,
                "error": None
            })
            
            print(f"✅ Result: {result}")
            print(f"⏱️  Duration: {duration:.1f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            # Still add to submission payload with error
            answers_payload.append({
                "task_id": task_id,
                "submitted_answer": f"ERROR: {error_msg}"
            })
            
            # Add to results log
            results.append({
                "task_id": task_id,
                "question": question_text,
                "result": None,
                "duration": duration,
                "success": False,
                "error": error_msg
            })
            
            print(f"❌ Error: {error_msg}")
            print(f"⏱️  Duration: {duration:.1f}s")
    
    return results, answers_payload

def submit_results(username, agent_code_url, answers_payload):
    """Submit results to the official GAIA API"""
    api_url = DEFAULT_API_URL
    submit_url = f"{api_url}/submit"
    
    if not answers_payload:
        print("❌ No answers to submit!")
        return False
    
    # Prepare submission data
    submission_data = {
        "username": username,
        "agent_code": agent_code_url,
        "answers": answers_payload
    }
    
    print(f"\n📤 Submitting {len(answers_payload)} answers to official GAIA API")
    print(f"👤 Username: {username}")
    print(f"🔗 Agent Code: {agent_code_url}")
    print(f"📡 Submit URL: {submit_url}")
    print("=" * 60)
    
    try:
        print("⏳ Submitting... (this may take a while)")
        response = requests.post(submit_url, json=submission_data, timeout=120)
        response.raise_for_status()
        result_data = response.json()
        
        print("\n🎉 SUBMISSION SUCCESSFUL!")
        print("=" * 40)
        print(f"👤 User: {result_data.get('username', username)}")
        print(f"📊 Overall Score: {result_data.get('score', 'N/A')}%")
        print(f"✅ Correct: {result_data.get('correct_count', '?')}")
        print(f"📝 Total: {result_data.get('total_attempted', '?')}")
        print(f"💬 Message: {result_data.get('message', 'No message received')}")
        print("=" * 40)
        
        return True
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ SUBMISSION FAILED!")
        print(f"🔴 HTTP Error {e.response.status_code}")
        try:
            error_json = e.response.json()
            print(f"📋 Detail: {error_json.get('detail', 'No details available')}")
        except:
            print(f"📋 Response: {e.response.text[:500]}")
        return False
        
    except requests.exceptions.Timeout:
        print(f"\n❌ SUBMISSION FAILED!")
        print(f"⏰ Request timed out (>2 minutes)")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ SUBMISSION FAILED!")
        print(f"🌐 Network error: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ SUBMISSION FAILED!")
        print(f"💥 Unexpected error: {e}")
        return False

def analyze_local_results(results):
    """Analyze results locally before submission"""
    print(f"\n📊 LOCAL RESULTS ANALYSIS")
    print("=" * 40)
    
    if not results:
        print("No results to analyze")
        return
    
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    success_rate = (successful / total) * 100 if total > 0 else 0
    
    avg_duration = sum(r["duration"] for r in results) / total if total > 0 else 0
    
    print(f"📝 Total Questions: {total}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    print(f"⏱️  Average Duration: {avg_duration:.1f}s")
    
    # Show some successful answers
    successes = [r for r in results if r["success"]][:5]  # First 5
    if successes:
        print(f"\n✅ SAMPLE SUCCESSFUL ANSWERS:")
        print("-" * 30)
        for s in successes:
            task_id = s['task_id'][:8] + "..."  # Truncate for readability
            result = str(s['result'])[:50] + "..." if len(str(s['result'])) > 50 else str(s['result'])
            print(f"• {task_id}: {result}")
    
    # Show some failures
    failures = [r for r in results if not r["success"]][:3]  # First 3
    if failures:
        print(f"\n❌ SAMPLE FAILURES:")
        print("-" * 30)
        for f in failures:
            task_id = f['task_id'][:8] + "..."
            error = f['error'][:50] + "..." if len(f['error']) > 50 else f['error']
            print(f"• {task_id}: {error}")

def main():
    print("🚀 Official GAIA Benchmark Submission")
    print("Ultra-Minimal Agent Performance Evaluation")
    print("=" * 60)
    
    # 1. Get credentials
    username, agent_code_url = get_huggingface_credentials()
    if not username:
        print("❌ Authentication failed. Exiting.")
        return
    
    # 2. Fetch all questions
    questions = fetch_all_gaia_questions()
    if not questions:
        print("❌ Could not fetch questions. Exiting.")
        return
    
    # 3. Run agent on all questions
    results, answers_payload = run_agent_on_all_questions(questions)
    
    # 4. Analyze results locally
    analyze_local_results(results)
    
    # 5. Confirm submission
    print(f"\n🤔 Ready to submit {len(answers_payload)} answers to official GAIA API?")
    confirm = input("Type 'yes' to submit, or anything else to cancel: ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Submission cancelled by user")
        print("💾 Results saved locally for review")
        return
    
    # 6. Submit to official API
    success = submit_results(username, agent_code_url, answers_payload)
    
    if success:
        print("\n🎉 MISSION ACCOMPLISHED!")
        print("Your ultra-minimal GAIA agent has been officially benchmarked!")
    else:
        print("\n😞 Submission failed, but your agent ran successfully locally")
        print("💾 You can review the results above")

if __name__ == "__main__":
    main() 