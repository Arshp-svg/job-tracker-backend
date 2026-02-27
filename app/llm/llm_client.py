import os
from dotenv import load_dotenv
from groq import Groq


load_dotenv()

USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

def call_llm(prompt: str) -> str:
    if not USE_LLM:
        return "LLM disabled. Using rule-based insight."

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful career AI assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=300,
    )

    return completion.choices[0].message.content
