# Bug Free Pancake

An interactive AI agent system for multi-step query processing and business analysis with intelligent orchestration, conversation memory, and domain-specific reasoning.

## Overview

Bug Free Pancake is a Python-based AI system that processes complex queries through a multi-agent pipeline. It breaks down user requests into manageable tasks, executes them in sequence with real-time feedback, and maintains conversation history for contextual awareness. The system is designed for business analytics, financial analysis, and proposal evaluation.

## Features

- **Multi-Step Query Processing**: Automatically decomposes complex queries into subtasks
- **Real-Time Feedback**: Stream processing events to provide live status updates during execution
- **Conversation Memory**: Maintains chat history across multiple threads and sessions
- **Domain-Aware Configuration**: Configure the system behavior through JSON-based domain configuration
- **Secure Expression Evaluation**: SafeEvaluator prevents code injection while allowing mathematical computations
- **Database Integration**: PostgreSQL support for persistent data storage and retrieval
- **Thread-Based Chat Management**: Create, load, and manage multiple conversation threads

## Architecture

The system consists of several key components:

- **Orchestrator**: Manages the pipeline execution and coordinates agents
- **Agents**: Specialized modules for different task types
- **LLM**: Language model integration for intelligent reasoning
- **Database**: Stores chat history, threads, and application data
- **AI System**: Business logic for financial analysis and proposal comparison

## Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL database running locally or remotely
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/MPK2004/bug-free-pancake.git
cd bug-free-pancake
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials and API keys:
```
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=your_database_name
```

5. Ensure your PostgreSQL database is running and the required tables are created.

## Usage

### Running the Application

Start the interactive chat application:
```bash
python main.py
```

The application will initialize and display the available commands.

### Commands

Once the application is running, you can use the following commands:

- `/new` - Start a new conversation thread
- `/list` - View all your previous chat threads
- `/load <thread_id>` - Load and continue a specific conversation thread
- `/help` - Display available commands
- `/exit` - Exit the application

### Example Interaction

```
=== Domain AI Agent (Interactive Mode) ===
Active Thread: abc123-def456-ghi789

Question > What are the top proposals based on financial metrics?
[*] Analyzing your query...
[PLAN] Identified 3 tasks:
  1. [analysis] Fetch financial data from database
  2. [calculation] Compute financial metrics
  3. [ranking] Identify top proposals

[RUNNING] Step 1: Fetch financial data from database...
[DONE] Step 1 complete.

[RUNNING] Step 2: Compute financial metrics...
[DONE] Step 2 complete.

==================== FINAL ANALYSIS ====================
Top Proposal: Brand X - Fashion Category
Base Value: $150,000
Adjusted Value: $180,000
Trend: Growing
```

## Configuration

### Domain Configuration

The `domain_config.json` file allows you to customize system behavior:

```json
{
  "domain_name": "Your Domain Name",
  "tools": {
    "calculate_adjusted_value": {
      "formula": "expected_yield * demand * priority_weight",
      "priority_weights": {
        "HIGH": 1.5,
        "MEDIUM": 1.0,
        "LOW": 0.8
      },
      "default_priority": "MEDIUM"
    }
  }
}
```

## Project Structure

```
bug-free-pancake/
├── main.py                 # Application entry point
├── ai_system.py           # Core business logic and analysis functions
├── db_connect.py          # Database connection utilities
├── domain_config.json     # System configuration file
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── chat_history.db       # SQLite chat history database
├── agents/               # Agent modules
├── orchestrator/         # Pipeline orchestration logic
├── llm/                  # Language model integration
└── db/                   # Database schema and managers
```

## Core Functions

### Financial Analysis
Calculates annual rent, expected revenue, and total value for a list of proposals:
```python
financial_analysis(proposals_data: list) -> list
```

### Compare Proposals
Compares proposals using market trend factors and identifies the best option:
```python
compare_proposals(proposals_data: list, tenants_data: list) -> dict
```

### Calculate Adjusted Value
Computes adjusted values using customizable formulas and priority weights:
```python
calculate_adjusted_value(proposals_data: list) -> list
```

### Safe Expression Evaluation
Securely evaluates mathematical expressions without using `eval()`:
```python
evaluator = SafeEvaluator()
result = evaluator.evaluate("expected_yield * demand * priority_weight", context)
```

## Dependencies

- `psycopg2-binary`: PostgreSQL database adapter
- `requests`: HTTP library for API calls
- `python-dotenv`: Environment variable management

## Database

The application uses PostgreSQL with the following key tables:
- `chat_threads`: Stores conversation threads
- `messages`: Stores individual chat messages
- `tenants`: Stores business tenant information
- `proposals`: Stores proposal data for analysis

Ensure your database is properly initialized before running the application.

## Troubleshooting

### Connection Issues
- Verify PostgreSQL is running and accessible
- Check `.env` file for correct database credentials
- Ensure the database and required tables exist

### Missing Configuration
- Ensure `domain_config.json` exists in the project root
- Verify the JSON syntax is valid

### Module Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify the Python path includes the project directory

## Development

To extend the system:

1. Add new agents in the `agents/` directory
2. Register tools in the `TOOL_REGISTRY` within `ai_system.py`
3. Update `domain_config.json` with new tool configurations
4. Extend the orchestrator pipeline in `orchestrator/pipeline.py`

## Notes

- Database credentials are stored in environment variables for security
- The SafeEvaluator prevents arbitrary code execution through whitelisting
- All conversation history is preserved in the database for audit trails
- Thread IDs are UUID4 for global uniqueness

## Contributing

Feel free to fork, modify, and improve this project. Report any issues or suggest enhancements through GitHub issues.

## Support

For questions or issues, please open an issue in the repository or review the inline code documentation.
