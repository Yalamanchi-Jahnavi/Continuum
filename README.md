# Continuum - Autonomous AI Agent System

> **⚠️ IMPORTANT: Before running the application, you MUST replace the API key in `config.py`**
> 
> 1. Open `config.py`
> 2. Replace `"YOUR_GEMINI_API_KEY_HERE"` with your actual Google Gemini API key
> 3. Get your API key from: https://makersuite.google.com/app/apikey
> 
> **Never commit your actual API key to version control!**

---

## Privacy & Data Storage

**Important Privacy Information:**
- **Local Storage**: All your goals, execution results, steps, outputs, and statistics are stored locally in the SQLite database (`db/continuum.db`) on your machine. This data never leaves your local system except when sent to the API.
- **API Calls**: When you submit a goal, it is sent to Google's Gemini API for processing. Google may log these API calls according to their privacy policy. The actual processing happens on Google's servers.
- **No External Storage**: Continuum does not send your data to any other external services. The only external communication is with Google's Gemini API for AI processing.
- **Database Location**: Your execution history is stored in `db/continuum.db` on your local machine. You can delete this file at any time to clear your history.
- **API Key**: Your Gemini API key is stored locally in `config.py` and is never shared or transmitted anywhere except to Google's API for authentication.

1. Goal → sent to Gemini
2. Response ← received from Gemini
3. Full response → stored locally in SQLite
4. Full response is not sent back to Gemini (only a 200-char snippet during self-correction)
**Your complete execution history and results stay on your machine. Only the goal and step prompts are sent to Gemini for processing.**

---

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Backend](#backend)
- [Frontend](#frontend)
- [Features](#features)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [File Structure](#file-structure)
- [Usage Guide](#usage-guide)

---

## 🎯 Project Overview

**Continuum** is an autonomous AI agent system that breaks down user goals into actionable steps, executes them using Google's Gemini AI, evaluates the results, and provides comprehensive answers. The system features a modern, responsive web interface with real-time progress tracking and execution history.

### Key Capabilities
- **Intelligent Planning**: Automatically categorizes goals by complexity (simple, moderate, complex)
- **Step-by-Step Execution**: Breaks down goals into manageable steps
- **Self-Correction**: Re-executes steps if evaluation indicates failure
- **Execution History**: Stores and displays all previous executions
- **Performance Metrics**: Tracks API calls, execution time, and statistics

---

## 🏗️ Architecture

### System Components

```
┌─────────────────┐
│   Frontend      │  (HTML/CSS/JavaScript)
│   (React-like)  │
└────────┬────────┘
         │ HTTP/REST
         │
┌────────▼────────┐
│   FastAPI       │  (Python Backend)
│   Backend       │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
┌───▼───┐ ┌──▼──┐  ┌────▼────┐ ┌───▼────┐
│Planner│ │Exec │  │Evaluator│ │ Memory │
└───────┘ └─────┘  └─────────┘ └────────┘
    │         │          │          │
    └─────────┴──────────┴──────────┘
              │
         ┌────▼────┐
         │ Gemini  │
         │   AI    │
         └─────────┘
```

### Technology Stack

**Backend:**
- Python 3.x
- FastAPI (Web Framework)
- Google Generative AI (Gemini API)
- SQLite (Database)
- Uvicorn (ASGI Server)

**Frontend:**
- HTML5
- CSS3 (Modern, Responsive Design)
- Vanilla JavaScript
- Fetch API (HTTP Requests)

---

## 🔧 Backend

### Core Components

#### 1. **Agent Loop** (`agent/loop.py`)
The main orchestrator that coordinates planning, execution, evaluation, and self-correction.

**Key Functions:**
- `run(goal)`: Main execution function
  - Resets API statistics
  - Plans steps based on goal complexity
  - Executes each step
  - Evaluates outputs
  - Self-corrects if needed
  - Returns comprehensive results with statistics

**Complexity Detection:**
- **Simple**: 1-3 steps (e.g., "What is X?")
- **Moderate**: 3-5 steps (e.g., "Create a todo app")
- **Complex**: 5-8 steps (e.g., "Build a complete system")

#### 2. **Planner** (`agent/planner.py`)
Breaks down user goals into actionable steps.

**Features:**
- Complexity detection based on keywords and goal length
- Optimized step counts for speed
- Filters out formatting/meta-instructions
- Special handling for definition questions (single comprehensive step)

**Complexity Indicators:**
- Simple: `["?", "what is", "define", "explain", "describe", "tell me", "what are"]`
- Moderate: `["create", "build", "design", "implement", "develop", "write", "make", "analyze", "compare", "research"]`
- Complex: `["system", "application", "architecture", "framework", "multiple", "several", "comprehensive", "complete solution"]`

#### 3. **Executor** (`agent/executor.py`)
Executes individual steps using Gemini AI.

**Features:**
- Direct answer generation (no notes/suggestions)
- Context-aware execution (uses original goal for better answers)
- Handles both definition questions and complex tasks

#### 4. **Evaluator** (`agent/evaluator.py`)
Evaluates step outputs for quality and completeness.

**Features:**
- Smart evaluation skipping (for satisfactory outputs)
- Lenient evaluation for simple tasks
- Truncates output to 500 chars for faster processing
- Returns YES/NO for self-correction decision

#### 5. **Rate Limiter** (`agent/rate_limiter.py`)
Manages API rate limiting and retry logic.

**Features:**
- 12-second minimum delay between requests
- Automatic retry on quota errors
- Extracts retry delays from error messages
- Tracks API calls by type (planning, execution, evaluation, self_correction)
- Handles daily quota limits gracefully

**API Statistics Tracking:**
```python
api_stats = {
    "planning": 0,
    "execution": 0,
    "evaluation": 0,
    "self_correction": 0
}
```

#### 6. **Memory** (`agent/memory.py`)
Handles database operations for storing agent memory.

**Database Schema:**
- `memory` table: Stores steps, outputs, goals, timestamps
- `execution_stats` table: Stores API statistics and execution times

**Key Functions:**
- `init_db()`: Initializes database with corruption handling
- `save(step, output, goal)`: Saves execution step
- `get_all(goal)`: Retrieves all results for a goal
- `get_all_goals()`: Gets all unique goals with metadata
- `get_execution_stats(goal)`: Retrieves stored statistics
- `save_execution_stats()`: Saves execution statistics

**Database Corruption Handling:**
- Automatic integrity checks
- Backup corrupted databases
- Recreation if needed
- Handles file locks gracefully

### API Server (`app.py`)

**Endpoints:**

1. **POST `/run`**
   - Executes a goal
   - Returns: status, goal, steps, execution_time, api_statistics, results

2. **GET `/results?goal=<goal>`**
   - Retrieves results for a specific goal
   - Returns: goal, count, results, execution_time, api_statistics

3. **GET `/goals`**
   - Gets all unique goals with metadata
   - Returns: count, goals (with execution_time, api_statistics, step_count)

**CORS Configuration:**
- Allows all origins (configurable for production)
- Enables credentials and all methods/headers

---

## 🎨 Frontend

### Structure

#### 1. **HTML** (`frontend/index.html`)
Main structure with sections:
- Header (Logo & Tagline)
- New Goal Input Section
- Progress Section (real-time updates)
- Results Section (with close button)
- Previous Results Section (side-by-side with New Goal)

#### 2. **CSS** (`frontend/styles.css`)
Modern, responsive design with:
- **Color Palette:**
  - Primary: `#4F46E5` (Indigo)
  - Secondary: `#22D3EE` (Cyan)
  - Accent: `#A5B4FC` (Soft Indigo)
  - Background: `#0F172A` (Dark Navy)
  - Card Background: `#1E293B` (Dark Slate)

- **Features:**
  - Glassmorphism effects
  - Smooth animations
  - Responsive design (mobile, tablet, desktop)
  - Hidden scrollbars
  - Markdown rendering styles

#### 3. **JavaScript** (`frontend/app.js`)
Client-side logic:

**Key Functions:**
- `matchSectionHeights()`: Matches New Goal and Previous Results heights
- `displayResults(data)`: Shows execution results
- `displayHistory(data)`: Shows all previous goals
- `displayHistoryResults(data)`: Shows results for a selected goal
- `renderMarkdown(text)`: Converts markdown to HTML
- `copyToClipboard(text, button)`: Copies output to clipboard

**Features:**
- Real-time progress tracking
- API call statistics display
- Execution time tracking
- Combined output display (all steps in one block)
- Copy buttons (above and below output)
- Markdown rendering (headers, bold, tables, lists, code blocks)

### UI Components

#### New Goal Section
- Textarea for goal input
- "Start Agent" button
- Placeholder examples

#### Previous Results Section
- Scrollable list of all goals
- Each item shows:
  - Goal text (wraps based on length)
  - Execution time
  - Step count
- Click to view full results
- Refresh button

#### Results Section
- Close button (top right)
- Execution Time & Total API Calls (left side)
- API Call Statistics (grid of 4 cards)
- Combined output with markdown rendering
- Copy buttons (top and bottom)

---

## ✨ Features

### 1. **Intelligent Complexity Detection**
Automatically categorizes goals and adjusts step counts:
- Simple questions: 1 step (comprehensive answer)
- Moderate tasks: 3-5 steps
- Complex projects: 5-8 steps

### 2. **Smart Evaluation**
- Skips evaluation for satisfactory outputs
- Reduces unnecessary API calls
- Faster execution times

### 3. **Self-Correction**
- Automatically re-executes failed steps
- Improves output quality
- Tracks self-correction calls separately

### 4. **Execution History**
- Stores all goals and results
- Displays execution time and API statistics
- Click any goal to view full results
- Persistent storage in SQLite

### 5. **Performance Metrics**
- Real-time API call tracking
- Execution time measurement
- Statistics breakdown by type:
  - Planning calls
  - Execution calls
  - Evaluation calls
  - Self-correction calls

### 6. **Responsive Design**
- Mobile-friendly layout
- Tablet optimization
- Desktop experience
- Side-by-side layout on larger screens
- Stacked layout on mobile

### 7. **Markdown Support**
- Headers (H1, H2, H3)
- Bold and italic text
- Code blocks and inline code
- Tables (with proper formatting)
- Lists (ordered and unordered)
- Links
- Horizontal rules

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- Google Gemini API Key
- Modern web browser

### Step 1: Clone/Download Project
```bash
cd Continuum
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

**Required Packages:**
- `fastapi`
- `uvicorn`
- `google-generativeai`
- `sqlite-utils`

### Step 3: Configure API Key
Edit `config.py`:
```python
API_KEY = "YOUR_GEMINI_API_KEY_HERE"
```

Get your API key from: https://makersuite.google.com/app/apikey

### Step 4: Initialize Database
The database will be created automatically on first run in `db/continuum.db`

### Step 5: Start Backend Server
```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### Step 6: Start Frontend Server
In a new terminal:
```bash
cd frontend
python serve.py
```

Or specify a port:
```bash
python serve.py 3000
```

The frontend will automatically find an available port (3000, 5000, 8001, 8081, 9000).

### Step 7: Access Application
Open your browser and navigate to:
```
http://localhost:3000
```
(Or the port shown in the terminal)

---

## ⚙️ Configuration

### API Configuration (`config.py`)
```python
import google.generativeai as genai

API_KEY = "YOUR_GEMINI_API_KEY"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-flash-latest")
```

**Available Models:**
- `gemini-flash-latest` (Free tier, recommended)
- `gemini-pro-latest` (May require paid tier)
- `gemini-2.5-pro` (May require paid tier)

### Rate Limiting (`agent/rate_limiter.py`)
```python
MIN_DELAY_BETWEEN_REQUESTS = 12.0  # seconds
max_retries = 5
```

### Database Location
- Default: `db/continuum.db`
- Backups: `db/continuum.db.corrupted.YYYYMMDD_HHMMSS`

---

## 📡 API Endpoints

### POST `/run`
Execute a goal.

**Request:**
```http
POST /run?goal=What is React?
```

**Response:**
```json
{
  "status": "completed",
  "goal": "What is React?",
  "steps": 1,
  "execution_time": {
    "seconds": 24.8,
    "formatted": "24.8 seconds"
  },
  "api_statistics": {
    "planning": 1,
    "execution": 1,
    "evaluation": 0,
    "self_correction": 0,
    "total": 2
  },
  "results": [
    {
      "step": "Provide comprehensive answer about React",
      "output": "React is a JavaScript library..."
    }
  ]
}
```

### GET `/results?goal=<goal>`
Get results for a specific goal.

**Request:**
```http
GET /results?goal=What is React?
```

**Response:**
```json
{
  "goal": "What is React?",
  "count": 1,
  "results": [...],
  "execution_time": {
    "duration_formatted": "24.8 seconds"
  },
  "api_statistics": {
    "planning": 1,
    "execution": 1,
    "evaluation": 0,
    "self_correction": 0,
    "total": 2
  }
}
```

### GET `/goals`
Get all unique goals with metadata.

**Request:**
```http
GET /goals
```

**Response:**
```json
{
  "count": 3,
  "goals": [
    {
      "goal": "What is React?",
      "step_count": 1,
      "execution_time": {
        "duration_formatted": "24.8 seconds"
      },
      "api_statistics": {
        "planning": 1,
        "execution": 1,
        "total": 2
      }
    },
    ...
  ]
}
```

---

## 📁 File Structure

```
Continuum/
├── agent/
│   ├── __init__.py
│   ├── loop.py              # Main orchestrator
│   ├── planner.py            # Step planning
│   ├── executor.py           # Step execution
│   ├── evaluator.py          # Output evaluation
│   ├── rate_limiter.py       # API rate limiting
│   └── memory.py             # Database operations
├── db/
│   └── continuum.db          # SQLite database
├── frontend/
│   ├── index.html            # Main HTML
│   ├── styles.css            # Styling
│   ├── app.js                # JavaScript logic
│   ├── serve.py              # Frontend server
│   └── README.md             # Frontend docs
├── app.py                    # FastAPI server
├── config.py                 # API configuration
├── requirements.txt          # Python dependencies
├── view_db.py               # Database viewer utility
├── README.md                # Project readme
└── Application.md           # This file
```

---

## 📖 Usage Guide

### Basic Usage

1. **Enter a Goal**
   - Type your question or task in the "New Goal" textarea
   - Examples:
     - "What is React?"
     - "Compare REST API vs GraphQL"
     - "Create a todo app architecture"

2. **Start Execution**
   - Click "Start Agent" button
   - Watch real-time progress
   - View complexity and step count

3. **View Results**
   - Results appear automatically when complete
   - See execution time and API statistics
   - View combined output with markdown rendering
   - Use copy buttons to copy output

4. **View History**
   - Scroll through "Previous Results"
   - Click any goal to view its results
   - See execution time and step count for each

5. **Close Results**
   - Click the X button (top right) to close results
   - Return to main view

### Advanced Features

#### Copy Output
- Click "Copy Output" button above or below the results
- Text is copied to clipboard
- Button shows confirmation

#### View Statistics
- Execution Time: Total time taken
- Total API Calls: Sum of all API calls
- Breakdown: Planning, Execution, Evaluation, Self-Correction

#### Responsive Design
- **Desktop**: Side-by-side layout (New Goal | Previous Results)
- **Tablet**: Side-by-side with adjusted spacing
- **Mobile**: Stacked layout, full-width buttons

---

## 🔍 Troubleshooting

### Database Corruption
- System automatically backs up corrupted databases
- Check `db/` folder for backup files
- Database is recreated automatically

### API Rate Limits
- System handles rate limits automatically
- Uses `gemini-flash-latest` (free tier)
- 12-second delay between requests
- Automatic retry with extracted delays

### Port Conflicts
- Frontend server automatically finds available port
- Try: 3000, 5000, 8001, 8081, 9000
- Or specify: `python serve.py <port>`

### CORS Issues
- Backend allows all origins by default
- For production, update `app.py` CORS settings

---

## 🎯 Best Practices

1. **Goal Formulation**
   - Be specific and clear
   - For comparisons, mention both items
   - For complex tasks, break into smaller goals if needed

2. **API Usage**
   - Monitor API call statistics
   - Simple questions use fewer calls
   - Complex tasks may take longer

3. **Performance**
   - System optimizes for speed
   - Evaluation is skipped when not needed
   - Self-correction only when necessary

---

## 📝 Notes

- **Model Selection**: Uses `gemini-flash-latest` for free tier compatibility
- **Database**: SQLite for simplicity and portability
- **No Authentication**: Add authentication for production use
- **CORS**: Currently allows all origins (restrict for production)
- **Error Handling**: Comprehensive error handling with graceful degradation

---

## 🔮 Future Enhancements

- WebSocket support for real-time updates
- User authentication
- Export results (PDF, Markdown)
- Search functionality in history
- Goal templates
- Multi-language support
- Advanced analytics dashboard

---

## 📄 License

[Add your license information here]

---

## 👥 Contributors

[Add contributor information here]

---

**Last Updated**: 2024
**Version**: 1.0.0

