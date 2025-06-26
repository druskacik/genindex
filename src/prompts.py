from inspect import cleandoc

def build_prompt(post: str) -> str:
    
    prompt = cleandoc(f"""
        Write a concise response to this post. Use grounding to support your response with relevant information.
        
        ```
        {post}
        ```	
    """)
    return prompt