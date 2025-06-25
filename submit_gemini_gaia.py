#!/usr/bin/env python3
"""
GAIA Benchmark Submission - Gemini Agent
Runs Gemini-powered agent on all GAIA questions and submits to official API for scoring
"""

import os
import sys
import requests
import json
import time

# Import the Gemini agent
from agent_gemini import Agent

# API Configuration
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"

# Stored credentials - no need to enter each time
HF_USERNAME = "theguywithahat0"
AGENT_CODE_URL = "https://github.com/theguywithahat0/hugging_face_agent_course"

def get_huggingface_credentials():
    """Get Hugging Face credentials (now stored as constants)"""
    print("🔐 Using Stored Credentials")
    print("=" * 50)
    print(f"👤 Username: {HF_USERNAME}")
    print(f"🔗 Agent Code: {AGENT_CODE_URL}")
    
    return HF_USERNAME, AGENT_CODE_URL

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
    """Run our Gemini agent on all GAIA questions"""
    print(f"\n🤖 Running Gemini GAIA Agent on {len(questions)} questions")
    print("=" * 60)
    
    agent = Agent()
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

def analyze_local_results(results):
    """Analyze results before submission"""
    print(f"\n📊 LOCAL RESULTS ANALYSIS")
    print("=" * 50)
    
    total_questions = len(results)
    successful_answers = len([r for r in results if r["success"]])
    error_count = total_questions - successful_answers
    
    print(f"📝 Total Questions: {total_questions}")
    print(f"✅ Successful Answers: {successful_answers}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Success Rate: {(successful_answers/total_questions)*100:.1f}%")
    
    # Analyze answer lengths (shorter is usually better for GAIA)
    answer_lengths = []
    for result in results:
        if result["success"] and result["result"]:
            answer_lengths.append(len(str(result["result"])))
    
    if answer_lengths:
        avg_length = sum(answer_lengths) / len(answer_lengths)
        print(f"📏 Average Answer Length: {avg_length:.1f} characters")
        print(f"📏 Answer Length Range: {min(answer_lengths)} - {max(answer_lengths)}")
        
        # Count concise answers (good sign)
        concise_answers = len([l for l in answer_lengths if l <= 20])
        print(f"✅ Concise Answers (≤20 chars): {concise_answers}/{len(answer_lengths)} ({(concise_answers/len(answer_lengths)*100):.1f}%)")
    
    # Show some example answers
    print(f"\n📋 SAMPLE ANSWERS:")
    for i, result in enumerate(results[:5]):
        if result["success"]:
            answer = str(result["result"])[:50] + "..." if len(str(result["result"])) > 50 else str(result["result"])
            print(f"   Q{i+1}: {answer}")
        else:
            print(f"   Q{i+1}: ERROR - {result['error']}")

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

def main():
    """Main submission function"""
    print("🚀 GAIA Benchmark Submission - Gemini 2.5 Flash Agent")
    print("🧠 Powered by Google's latest Gemini model for superior reasoning")
    print("=" * 60)
    
    # Get credentials
    username, agent_code_url = get_huggingface_credentials()
    
    # Fetch questions
    questions = fetch_all_gaia_questions()
    if not questions:
        print("❌ Cannot proceed without questions. Exiting.")
        return
    
    # Run agent on all questions
    results, answers_payload = run_agent_on_all_questions(questions)
    
    # Analyze local results
    analyze_local_results(results)
    
    # Auto-submit (no confirmation needed for testing)
    print(f"\n🚀 Auto-submitting {len(answers_payload)} answers to official GAIA API...")
    print("⚡ (Auto-submit enabled for faster testing)")
    
    # Submit to API
    success = submit_results(username, agent_code_url, answers_payload)
    
    if success:
        print("\n🎉 MISSION ACCOMPLISHED!")
        print("Your Gemini-powered GAIA agent has been officially benchmarked!")
        print("🧠 Expected significant improvement over local Ollama models!")
    else:
        print("\n😞 Submission failed, but your agent ran successfully locally")
        print("💾 You can review the results above")

if __name__ == "__main__":
    main() 