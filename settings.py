from clean_ollama import Tool, Param, ParamType


LOGO = """
 ___   _  _______  ______   _______ 
|   | | ||       ||      | |       |
|   |_| ||   _   ||  _    ||    ___|
|      _||  | |  || | |   ||   |___ 
|     |_ |  |_|  || |_|   ||    ___|
|    _  ||       ||       ||   |___ 
|___| |_||_______||______| |_______|
"""
AUTHOR = "Aiden Jun"
VERSION = "0.0.0"


SYSTEM_PROMPT = """
You are an expert coding assistant with access to the files and shell.
You explain every step you take in detail.
Before taking action, you plan what you will do in detail.

You have the following tools available:
- run_command: run shell commands (ls, grep, pytest, pip, etc.)
- read_file: read a file's contents before editing
- write_file: create new files
- edit_file: make targeted edits to existing files

Rules:
- Always read a file before editing it
- Prefer edit_file over write_file for existing files
- Use run_command for exploration (ls, grep, cat) instead of read_file where possible
- Make small, targeted edits — do not rewrite entire files unless necessary
- Run tests after making changes to verify correctness
- If a task is ambiguous, ask for clarification before making changes
- Never guess at file contents — always read first
- All paths are relative to the current working directory
"""
SYSTEM_PROMPT = SYSTEM_PROMPT.strip()

COMPACT_PROMPT = """
You are a helpful AI assistant tasked with summarizing conversations.

When asked to summarize, provide a detailed but concise summary of the conversation. 
Focus on information that would be helpful for continuing the conversation, including:
- What was done
- What is currently being worked on
- Which files are being modified
- What needs to be done next

Your summary should be comprehensive enough to provide context but concise enough to be quickly understood.
"""
COMPACT_PROMPT = COMPACT_PROMPT.strip()


TOOLS = [
    Tool(
        name="run_command",
        description=(
            "Execute a shell command and get its output. "
            "Use this to run tests, install packages, compile code, or search the environment. "
            "Prefer non destructive commands. Always confirm with the user before running anything that modifies the system."
        ),
        params=[
            Param("command", "The shell command to execute", ParamType.string),
        ],
    ),
    Tool(
        name="read_file",
        description="Read the contents of a file. Use this before editing any file.",
        params=[
            Param("path",       "Path to the file to read",              ParamType.string),
            Param("start_line", "Optional line to start reading from",   ParamType.integer, required=False),
            Param("end_line",   "Optional line to stop reading at",      ParamType.integer, required=False),
        ],
    ),
    Tool(
        name="write_file",
        description="Write content to a file, creating it if it doesn't exist. Overwrites the entire file. Use this for new files only — use edit_file for modifying existing files.",
        params=[
            Param("path",    "Path to the file to write",        ParamType.string),
            Param("content", "Full content to write to the file", ParamType.string),
        ],
    ),
    Tool(
        name="edit_file",
        description="Replace a specific string in a file with new content. Use this for targeted edits instead of rewriting the whole file. The old_str must match exactly.",
        params=[
            Param("path",    "Path to the file to edit",    ParamType.string),
            Param("old_str", "The exact string to replace", ParamType.string),
            Param("new_str", "The string to replace it with", ParamType.string),
        ],
    ),
]