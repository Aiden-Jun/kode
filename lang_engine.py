from settings import *
from clean_ollama import Client, Message, Role, Tool, Param, ParamType
import os
import json
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.columns import Columns
import threading
import subprocess


console = Console()


class LangEngine:
    def __init__(self, working_dir, model):
        self.working_dir = os.path.realpath(working_dir)
        self.client = Client(model)

    def load(self):
        self.client.load()

    def unload(self):
        self.client.unload()

    def _resolve(self, path):
        safe = os.path.realpath(os.path.join(self.working_dir, path))
        if not safe.startswith(self.working_dir):
            raise ValueError(f"Path escapes working directory: {path}")
        return safe

    def run_command(self, command):
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                timeout=60,
                capture_output=True,
                text=True,
                env={**os.environ, "HOME": self.working_dir},
            )

            console.print()
            command_panel = Panel(
                "\n".join([command, "", "Result:", result.stdout.strip()]),
                title_align="left",
                title="Shell Tool",
                expand=False,
            )
            console.print(command_panel)
            console.print()

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out after 60s", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    def read_file(self, path, start_line=None, end_line=None):
        try:
            with open(self._resolve(path)) as f:
                lines = f.readlines()
            if start_line or end_line:
                lines = lines[(start_line or 1) - 1 : end_line]

            console.print()
            console.print(
                Panel(
                    f"Reading file: {path}",
                    title_align="left",
                    title="Read File Tool",
                    expand=False,
                )
            )
            console.print()

            return {"content": "".join(lines), "lines": len(lines)}
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def write_file(self, path, content):
        try:
            full_path = self._resolve(path)
            parent = os.path.dirname(full_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)

            console.print()
            syntax = Syntax.from_path(full_path, theme="dracula", line_numbers=True)
            console.print(
                Panel(
                    syntax,
                    title_align="left",
                    title=f"Write File - {path}",
                    border_style="bold purple",
                )
            )
            console.print()

            return {"success": True, "path": path}
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def edit_file(self, args: dict):
        path = args.get("path")
        old_str = args.get("old_str") or args.get("old_string") or args.get("old")
        new_str = (
            args.get("new_str")
            or args.get("new_string")
            or args.get("new")
            or args.get("replacement", "")
        )

        if not path:
            return {"error": "path is required", "success": False}
        if not old_str:
            return {"error": "old_str is required", "success": False}

        try:
            full_path = self._resolve(path)
            with open(full_path) as f:
                content = f.read()
            count = content.count(old_str)
            if count == 0:
                return {"error": "old_str not found in file", "success": False}
            if count > 1:
                return {
                    "error": f"old_str found {count} times, needs to be unique",
                    "success": False,
                }
            with open(full_path, "w") as f:
                f.write(content.replace(old_str, new_str, 1))

            console.print()
            ext = os.path.splitext(path)[1].lstrip(".")
            console.print(
                Panel(
                    Columns(
                        [
                            Syntax(old_str, ext, theme="dracula", line_numbers=False),
                            Syntax(new_str, ext, theme="dracula", line_numbers=False),
                        ],
                        expand=True,
                    ),
                    title_align="left",
                    title=f"Edit File — {path}",
                    border_style="bold purple",
                )
            )
            console.print()

            return {"success": True}
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def dispatch(self, tool_call) -> dict:
        name = tool_call.function.name
        args = tool_call.function.arguments
        handlers = {
            "run_command": lambda a: self.run_command(**a),
            "read_file":   lambda a: self.read_file(**a),
            "write_file":  lambda a: self.write_file(**a),
            "edit_file":   lambda a: self.edit_file(a),
        }
        if name not in handlers:
            return {"error": f"Unknown tool: {name}"}
        return handlers[name](args)

    def run(self, messages: list[Message], think: bool) -> tuple[str, str]:
        result_holder = {}

        def _generate():
            try:
                thinking, content, tool_calls = self.client.generate(
                    messages, tools=TOOLS, think=think
                )
                result_holder["result"] = (thinking, content, tool_calls)
            except Exception as e:
                result_holder["error"] = str(e)

        while True:
            result_holder.clear()
            thread = threading.Thread(target=_generate, daemon=True)
            thread.start()

            try:
                thread.join()
            except KeyboardInterrupt:
                console.print("\n[bold red]Stopped.[/bold red]")
                return "", ""

            if "error" in result_holder:
                console.print(f"[red]Error: {result_holder['error']}[/red]")
                return "", ""

            thinking, content, tool_calls = result_holder["result"]

            messages.append(Message(Role.ASSISTANT, content or ""))

            if not tool_calls:
                return thinking, content

            if content:
                console.print(Markdown(content))

            for tool_call in tool_calls:
                try:
                    result = self.dispatch(tool_call)
                except KeyboardInterrupt:
                    console.print("\n[bold red]Stopped.[/bold red]")
                    return "", ""

                messages.append(Message(Role.TOOL, json.dumps(result)))