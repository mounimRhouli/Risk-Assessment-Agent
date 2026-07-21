"""
Interactive chat CLI for the Risk Assessment & Governance Agent.

Usage: python chat.py
"""

import uuid
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from agent import create_risk_agent

load_dotenv()

console = Console()


def main():
    console.print(Panel(
        "[bold cyan]Risk Assessment & Governance Agent[/bold cyan]\n\n"
        "I can help you with risk assessments, compliance reviews, audit preparation,\n"
        "and governance advisory. I have access to the organization's GRC database\n"
        "and can research current regulations and best practices.\n\n"
        "[dim]Type 'quit' or 'exit' to end the session.[/dim]",
        border_style="cyan",
        title="GRC Agent",
    ))
    console.print()

    checkpointer = MemorySaver()
    agent = create_risk_agent(checkpointer=checkpointer)
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            console.print("[dim]Goodbye![/dim]")
            break

        console.print()

        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config,
            )

            final_message = result["messages"][-1]
            content = final_message.content if hasattr(final_message, "content") else str(final_message)

            console.print(Panel(
                Markdown(content),
                border_style="blue",
                title="Agent",
            ))
            console.print()

        except Exception as e:
            console.print(Panel(
                f"[bold red]Error:[/bold red] {str(e)}",
                border_style="red",
            ))
            console.print()


if __name__ == "__main__":
    main()
