from settings import *
from lang_engine import LangEngine
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from clean_ollama import Message, Role


console = Console()


def print_info():
    console.print()
    console.print(
        Panel(
            f"[bold]{LOGO}[/bold]\n{VERSION}\n{AUTHOR}",
            title="",
            border_style="",
            expand=False,
        )
    )
    console.print("/help to get started")


def print_help():
    console.print(
        Panel(
            "\n".join([
                "Exit    - /exit",
                "Clear   - /clear",
                "Compact - /compact",
                "Think   - /think",
                "NoThink - /nothink",
                "Help    - /help",
            ]),
            title="Available Commands",
            border_style="white",
            expand=False,
        )
    )


def main_loop():
    ask_model = input("Enter ollama model: ")
    working_dir = input("Enter working directory: ")
    console.print()

    console.print("Loading model...")
    le = LangEngine(working_dir, ask_model)
    le.load()
    console.print("Model loaded!")

    messages = [Message(Role.SYSTEM, SYSTEM_PROMPT)]
    think = False

    while True:
        console.print()
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold red]Exiting.[/bold red]")
            le.unload()
            break

        console.print()

        if not user_input:
            continue

        if user_input == "/exit":
            le.unload()
            break

        elif user_input == "/clear":
            messages = [Message(Role.SYSTEM, SYSTEM_PROMPT)]
            console.print("History cleared")
            continue

        elif user_input == "/compact":
            console.print("Compacting...")
            messages.append(Message(Role.USER, COMPACT_PROMPT))
            thoughts, summary, _ = le.client.generate(messages, think=True)
            if thoughts:
                console.print(Markdown(thoughts))
            if summary:
                console.print(Markdown(summary))
            else:
                console.print("[red]Warning: compact produced an empty summary.[/red]")
            messages = [
                Message(Role.SYSTEM, SYSTEM_PROMPT),
                Message(Role.ASSISTANT, summary or ""),
            ]
            console.print("Compacted")
            continue

        elif user_input == "/help":
            print_help()
            continue

        elif user_input == "/think":
            think = True
            console.print("Thinking enabled")
            continue

        elif user_input == "/nothink":
            think = False
            console.print("Thinking disabled")
            continue

        elif user_input.startswith("/"):
            console.print(f"[red]Unknown command: {user_input}. Type /help for available commands.[/red]")
            continue

        messages.append(Message(Role.USER, user_input))

        try:
            thinking, response = le.run(messages, think)
        except KeyboardInterrupt:
            console.print("\n[red]Stopped.[/red]")
            messages.pop()
            continue

        if response:
            if thinking:
                quoted = "\n".join(f"> {line}" for line in thinking.splitlines())
                console.print(Markdown(quoted))

            console.print(Markdown(response))


if __name__ == "__main__":
    cwd = "/Users/aidenjun/Documents/Projects/testdir"
    print_info()
    main_loop()