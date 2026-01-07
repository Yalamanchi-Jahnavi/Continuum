import time
from google.api_core import exceptions
from config import model

# Rate limit: 5 requests per minute = 12 seconds between requests
MIN_DELAY_BETWEEN_REQUESTS = 12.0
last_request_time = 0

# API call tracking
api_call_count = {
    "planning": 0,
    "execution": 0,
    "evaluation": 0,
    "self_correction": 0
}

def get_api_stats():
    """Get current API call statistics"""
    return api_call_count.copy()

def reset_api_stats():
    """Reset API call statistics"""
    global api_call_count
    api_call_count = {
        "planning": 0,
        "execution": 0,
        "evaluation": 0,
        "self_correction": 0
    }

def rate_limited_generate_content(prompt, max_retries=5, call_type="execution"):
    """
    Generate content with rate limiting and retry logic for quota errors.
    call_type: "planning", "execution", "evaluation", "self_correction"
    """
    global last_request_time, api_call_count
    
    for attempt in range(max_retries):
        try:
            # Enforce rate limiting
            current_time = time.time()
            time_since_last_request = current_time - last_request_time
            
            if time_since_last_request < MIN_DELAY_BETWEEN_REQUESTS:
                wait_time = MIN_DELAY_BETWEEN_REQUESTS - time_since_last_request
                print(f"⏳ Rate limiting: waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
            
            # Make the API call
            response = model.generate_content(prompt)
            last_request_time = time.time()
            # Track API call
            if call_type in api_call_count:
                api_call_count[call_type] += 1
            return response
            
        except exceptions.ResourceExhausted as e:
            # Extract retry delay from error if available
            retry_delay = 60.0  # Default to 60 seconds
            error_str = str(e)
            
            # Try to extract from error message (format: "Please retry in X.XXs")
            import re
            # Try multiple patterns to catch different formats
            patterns = [
                r'retry in ([\d.]+)s\.?',  # "retry in 59.37s" or "retry in 59.37s."
                r'retry in ([\d.]+)\s*s\.?',  # "retry in 59.37 s" (with space)
                r'retry_delay.*?seconds?:\s*(\d+)',  # From error details
                r'seconds?:\s*(\d+)',  # Generic seconds pattern
            ]
            
            for pattern in patterns:
                match = re.search(pattern, error_str, re.IGNORECASE | re.DOTALL)
                if match:
                    try:
                        retry_delay = float(match.group(1))
                        break
                    except ValueError:
                        continue
            
            # Add a small buffer to the retry delay to be safe
            retry_delay = retry_delay + 2.0
            
            # Check if it's a daily quota limit (more retries needed)
            is_daily_limit = 'perday' in error_str.lower() or 'daily' in error_str.lower()
            if is_daily_limit and attempt < max_retries - 1:
                print(f"⚠️  Daily quota limit exceeded. Waiting {retry_delay:.1f}s... (attempt {attempt + 1}/{max_retries})")
                print(f"   This may take several minutes. Please be patient...")
            elif attempt < max_retries - 1:
                print(f"⚠️  Rate limit exceeded. Retrying in {retry_delay:.1f}s... (attempt {attempt + 1}/{max_retries})")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise Exception(f"Rate limit exceeded after {max_retries} attempts. Daily quota may be exhausted. Please wait and try again later.")
        
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Error occurred. Retrying in 5s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(5)
            else:
                raise
    
    raise Exception("Failed to generate content after all retries")

