import google.generativeai as genai

API_KEY = "YOUR_GEMINI_API_KEY_HERE"

if API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    print("⚠️  Warning: Please set your GEMINI_API_KEY environment variable or update config.py")
    print("   Get your API key from: https://makersuite.google.com/app/apikey")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-flash-latest")
