from agent.rate_limiter import rate_limited_generate_content

def execute(step, goal=None):
    # Detect if this is a definition question
    is_definition = goal and any(word in goal.lower() for word in ["what is", "define", "explain"])
    
    if is_definition:
        # For definition questions, provide comprehensive answer
        prompt = f"""
        Provide a comprehensive, detailed answer to the following question.
        
        Question: {goal}
        Step: {step}
        
        Your answer should include:
        1. A clear, direct definition
        2. Key features and characteristics
        3. Important context or background
        4. Practical examples or use cases (if relevant)
        
        IMPORTANT: Provide ONLY the direct answer. Do NOT include:
        - Notes about missing information
        - Disclaimers or placeholders
        - Suggestions about what could be added
        - Meta-commentary about the response format
        
        Write in a clear, informative style. Be thorough but well-organized. Answer directly.
        """
    else:
        prompt = f"""
        Execute the following step carefully and provide the result.
        Be concise but complete. Focus on delivering the requested information.
        
        IMPORTANT: Provide ONLY the direct answer. Do NOT include:
        - Notes about missing information
        - Disclaimers or placeholders
        - Suggestions about what could be added
        - Meta-commentary about the response format
        
        Step: {step}
        """
    
    response = rate_limited_generate_content(prompt, call_type="execution")
    return response.text
