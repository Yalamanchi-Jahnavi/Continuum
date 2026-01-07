from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent.loop import run
from agent.memory import init_db, get_all, get_latest_goal, get_execution_time_for_goal, get_execution_stats, get_all_goals

app = FastAPI(title="Continuum")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

@app.post("/run")
def start(goal: str):
    result = run(goal)
    return {
        "status": "completed",
        "goal": goal,
        "steps": result["total_steps"],
        "execution_time": {
            "seconds": result["execution_time_seconds"],
            "formatted": result["execution_time_formatted"]
        },
        "api_statistics": {
            "planning": result["statistics"]["planning"],
            "execution": result["statistics"]["execution"],
            "evaluation": result["statistics"]["evaluation"],
            "self_correction": result["statistics"]["self_correction"],
            "total": result["total_api_calls"]
        },
        "results": result["results"]
    }

@app.get("/results")
def get_results(goal: str = None):
    """Get all results, optionally filtered by goal"""
    if goal:
        results = get_all(goal)
        target_goal = goal
    else:
        latest_goal = get_latest_goal()
        target_goal = latest_goal
        results = get_all(latest_goal) if latest_goal else get_all()
    
    response = {
        "goal": target_goal,
        "count": len(results),
        "results": results
    }
    
    # Get execution stats (includes time and API statistics)
    if target_goal:
        stats = get_execution_stats(target_goal)
        if stats:
            response["execution_time"] = stats["execution_time"]
            response["api_statistics"] = {
                "planning": stats["planning"],
                "execution": stats["execution"],
                "evaluation": stats["evaluation"],
                "self_correction": stats["self_correction"],
                "total": stats["total"]
            }
        else:
            # Fallback to time calculation if stats not available
            execution_time_info = get_execution_time_for_goal(target_goal)
            if execution_time_info:
                duration = execution_time_info["duration_seconds"]
                if duration < 60:
                    formatted = f"{duration:.1f} seconds"
                elif duration < 3600:
                    formatted = f"{duration/60:.1f} minutes"
                else:
                    formatted = f"{duration/3600:.2f} hours"
                
                response["execution_time"] = {
                    "start_time": execution_time_info["start_time"],
                    "end_time": execution_time_info["end_time"],
                    "duration_seconds": execution_time_info["duration_seconds"],
                    "duration_formatted": formatted,
                    "step_count": execution_time_info["step_count"]
                }
    
    return response

@app.get("/goals")
def get_all_goals_endpoint():
    """Get all unique goals with their metadata"""
    goals = get_all_goals()
    return {
        "count": len(goals),
        "goals": goals
    }
