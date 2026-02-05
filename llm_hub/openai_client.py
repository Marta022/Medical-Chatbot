import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def openai_call(
    messages,
    model="gpt-4.1-mini",
    temperature=0,
    
):
    response = client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=temperature,
    
    )
    print(response.choices[0].message.content)