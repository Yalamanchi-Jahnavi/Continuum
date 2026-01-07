from agent.rate_limiter import rate_limited_generate_content
import re

def plan(goal):
    goal_lower = goal.lower()
    
    # Categorize complexity
    simple_indicators = ["?", "what is", "define", "explain", "describe", "tell me", "what are"]
    moderate_indicators = ["create", "build", "design", "implement", "develop", "write", "make", "analyze", "compare", "research"]
    complex_indicators = ["system", "application", "architecture", "framework", "multiple", "several", "comprehensive", "complete solution"]
    
    # Check complexity (in order: complex -> moderate -> simple)
    # Optimized for speed: reduced step counts to keep under 5 minutes
    if any(indicator in goal_lower for indicator in complex_indicators) or len(goal.split()) > 15:
        complexity = "complex"
        step_range = "5-8"  # Reduced from 8-12
        instruction = "Break into the most essential steps covering all critical aspects. Be concise."
    elif any(indicator in goal_lower for indicator in moderate_indicators):
        complexity = "moderate"
        step_range = "3-5"  # Reduced from 5-8
        instruction = "Break into the core actionable steps. Focus on essentials only."
    elif any(indicator in goal_lower for indicator in simple_indicators):
        complexity = "simple"
        # For "what is X?" questions, create a single comprehensive answer
        if "what is" in goal_lower or "define" in goal_lower:
            step_range = "1"
            instruction = "Create ONE comprehensive step that directly answers the question with a complete definition, explanation, and key details. Do NOT break it into multiple parts."
        else:
            step_range = "2-3"
            instruction = "Break into minimal steps that directly answer the question."
    else:
        # Default: treat as moderate
        complexity = "moderate"
        step_range = "3-5"
        instruction = "Break into core actionable steps."
    
    prompt = f"""
    {instruction}
    Create exactly {step_range} steps (no more, no less).
    Do NOT create steps for formatting, markdown, or meta-instructions.
    Only create steps that directly contribute to achieving the goal.
    
    Goal: {goal}
    
    Return ONLY the steps, one per line, without numbering or bullets.
    """
    
    response = rate_limited_generate_content(prompt, call_type="planning")
    steps = response.text.split("\n")
    
    # Filter out formatting-only steps
    filtered_steps = []
    for step in steps:
        step = step.strip()
        if not step:
            continue
        # Remove numbering/bullets
        step = re.sub(r'^[\d\.\-\*\#\s]+', '', step).strip()
        # Skip if it's just formatting
        if step and len(step) > 3 and not step.startswith(('---', '===')) and step != '|' and not re.match(r'^[\|\s\-\:]+$', step):
            filtered_steps.append(step)
    
    print(f"📋 Complexity detected: {complexity.upper()} (target: {step_range} steps, got: {len(filtered_steps)} steps)")
    
    return filtered_steps
