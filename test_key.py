from google import genai
import os

# PASTE YOUR NEW KEY HERE
KEY = "AIzaSyCCRBIKqSqy9rPaw9loct3iWXh43dUoyLE" 

print(f"Testing key starting with: {KEY[:6]}...{KEY[-4:]}")

try:
    client = genai.Client(api_key=KEY)
    response = client.models.generate_content(
        model="gemini-1.5-flash", 
        contents="Say 'Key is working!'"
    )
    print("--- SUCCESS ---")
    print(f"Response: {response.text}")
except Exception as e:
    print("--- FAILED ---")
    print(f"Error details: {e}")