from google.genai import types

from src.prompts import build_prompt

def get_completion(client, text, model="gemini-2.5-flash"):

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )
    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )
    return client.models.generate_content(
        model=model,
        contents=build_prompt(text),
        config=config,
    )