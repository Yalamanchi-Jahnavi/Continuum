import google.generativeai as genai

API_KEY = "AIzaSyB5rMt2lZOAmE6kfC7nnLXEXwBnCyG1GVU"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-flash-latest")
