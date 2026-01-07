from agent.planner import plan
from agent.executor import execute
from agent.evaluator import evaluate
from agent.memory import save, save_execution_stats
from agent.rate_limiter import get_api_stats, reset_api_stats
import time

def run(goal):
    # Reset stats at start
    reset_api_stats()
    
    # Start timing
    start_time = time.time()
    
    steps = plan(goal)
    results = []
    stats = get_api_stats()

    print(f"\n📊 Planning complete: {len(steps)} steps generated")
    print(f"📊 API Calls so far: Planning={stats['planning']}")

    for i, step in enumerate(steps, 1):
        if not step.strip():
            continue

        print(f"\n▶ STEP {i}/{len(steps)}: {step[:60]}...")
        output = execute(step, goal)
        stats = get_api_stats()
        print(f"   📊 Execution calls: {stats['execution']}")
        
        # Smart evaluation - skip if not needed
        from agent.evaluator import evaluate, should_evaluate
        if should_evaluate(step, output):
            review = evaluate(step, output)
            stats = get_api_stats()
            print(f"   📊 Evaluation calls: {stats['evaluation']}")
        else:
            review = "YES - Skipped evaluation (output looks good)"
            print(f"   ⚡ Evaluation skipped (output looks satisfactory)")

        if "NO" in review.upper():
            print("   ↻ Self-correcting...")
            # Re-execute with improvement instruction using executor but track as self-correction
            from agent.rate_limiter import rate_limited_generate_content
            improved_prompt = f"""
            Step: {step}
            Previous output: {output[:200]}...
            
            Improve and fix the previous output. Provide a better, more complete response.
            """
            response = rate_limited_generate_content(improved_prompt, call_type="self_correction")
            output = response.text
            stats = get_api_stats()
            print(f"   📊 Self-correction calls: {stats['self_correction']}")

        save(step, output, goal)
        results.append({"step": step, "output": output})
        print(f"   ✔ Completed")
    
    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    execution_time_formatted = format_time(execution_time)
    
    # Get final stats
    final_stats = get_api_stats()
    print(f"\n📊 Final API Call Statistics:")
    print(f"   Planning: {final_stats['planning']} call(s)")
    print(f"   Execution: {final_stats['execution']} call(s)")
    print(f"   Evaluation: {final_stats['evaluation']} call(s)")
    print(f"   Self-correction: {final_stats['self_correction']} call(s)")
    print(f"   Total: {sum(final_stats.values())} call(s)")
    print(f"\n⏱️  Total Execution Time: {execution_time_formatted}")
    
    # Save execution statistics
    save_execution_stats(goal, final_stats, round(execution_time, 2), execution_time_formatted)
    
    return {
        "results": results,
        "statistics": final_stats,
        "total_steps": len(steps),
        "total_api_calls": sum(final_stats.values()),
        "execution_time_seconds": round(execution_time, 2),
        "execution_time_formatted": execution_time_formatted
    }

def format_time(seconds):
    """Format time in a human-readable way"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.2f} hours"
