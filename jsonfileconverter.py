# jsonfileconverter.py
import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_info_from_text(text: str) -> str:
    """Sends extracted text to OpenAI and retrieves structured JSON output as plain text."""
    prompt = f"""
    Extract structured information from the following text and return only a valid JSON object.
    
    Strictly output JSON format only, with no extra text or explanation.

    Text:
    {text}

    Output (strictly JSON format only):
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI that extracts structured data from text. Output must be strictly valid JSON format without any extra text."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    json_output = response['choices'][0]['message']['content'].strip()
    return json_output
