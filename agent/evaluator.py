from agent.rate_limiter import rate_limited_generate_content

def should_evaluate(step, output):
    """Quick check to determine if evaluation is needed"""
    # Skip evaluation if output looks good
    if not output or len(output.strip()) < 10:
        return True  # Empty output needs evaluation
    
    # Skip evaluation for simple definition/explanation tasks if output is substantial
    simple_tasks = ["define", "explain", "describe", "what is", "tell me", "list", "name"]
    is_simple = any(task in step.lower() for task in simple_tasks)
    
    if is_simple and len(output) > 50:
        return False  # Skip evaluation for substantial simple outputs
    
    # Skip evaluation if output doesn't contain error indicators
    error_indicators = ["error", "cannot", "unable", "failed", "please provide", "i need", "i don't know"]
    has_errors = any(indicator in output.lower() for indicator in error_indicators)
    
    return has_errors  # Only evaluate if there might be errors

def evaluate(step, output):
    """Evaluate step output - only called when needed"""
    # Quick validation first
    if not should_evaluate(step, output):
        return "YES - Output appears satisfactory"
    
    # For simple definition/explanation tasks, be more lenient
    simple_tasks = ["define", "explain", "describe", "what is", "tell me"]
    is_simple = any(task in step.lower() for task in simple_tasks)
    
    if is_simple:
        # More lenient evaluation for simple questions
        prompt = f"""
        Step: {step}
        Output: {output[:500]}

        Did this step provide a reasonable answer? Only say NO if completely wrong or empty.
        Answer ONLY YES or NO.
        """
    else:
        prompt = f"""
        Step: {step}
        Output: {output[:500]}

        Did this step fully succeed? Only say NO if there are critical issues.
        Answer ONLY YES or NO.
        """
    
    response = rate_limited_generate_content(prompt, call_type="evaluation")
    return response.text
