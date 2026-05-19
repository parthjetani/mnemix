import sys
import time
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer(help="MNEMIX — Memory-Powered Interview Coach", add_completion=False)
console = Console()

BASE_URL = "http://localhost:8000/api/v1"
CLIENT_TIMEOUT = 30.0


def _client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=CLIENT_TIMEOUT)


def _poll_job(job_id: str) -> dict:
    with _client() as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing...", total=None)
            while True:
                resp = client.get(f"/ingest/status/{job_id}")
                resp.raise_for_status()
                data = resp.json()
                status = data.get("status", "")
                prog = data.get("progress", 0)
                progress.update(task, description=f"Status: {status} ({prog}%)")
                if status in ("complete", "failed"):
                    return data
                time.sleep(2)


@app.command()
def ingest(
    resume: Optional[Path] = typer.Option(None, "--resume", help="Path to resume PDF"),
    chatgpt: Optional[Path] = typer.Option(None, "--chatgpt", help="Path to ChatGPT export (zip or json)"),
    claude: Optional[Path] = typer.Option(None, "--claude", help="Path to Claude export (zip, dir, or md)"),
):
    """Ingest a resume or AI conversation export to extract memories."""
    if not any([resume, chatgpt, claude]):
        console.print("[red]Provide at least one of --resume, --chatgpt, or --claude[/red]")
        raise typer.Exit(1)

    with _client() as client:
        if resume:
            if not resume.exists():
                console.print(f"[red]File not found: {resume}[/red]")
                raise typer.Exit(1)
            console.print(f"[bold]Uploading resume:[/bold] {resume.name}")
            with open(resume, "rb") as f:
                resp = client.post("/ingest/resume", files={"file": (resume.name, f, "application/pdf")})
            resp.raise_for_status()
            job_id = resp.json()["job_id"]
            result = _poll_job(job_id)
            if result["status"] == "complete":
                console.print(f"[green]Resume ingested: {result.get('memories_found', 0)} memories extracted[/green]")
            else:
                console.print(f"[red]Ingestion failed: {result.get('error_message', 'unknown error')}[/red]")

        if chatgpt:
            if not chatgpt.exists():
                console.print(f"[red]File not found: {chatgpt}[/red]")
                raise typer.Exit(1)
            console.print(f"[bold]Uploading ChatGPT export:[/bold] {chatgpt.name}")
            with open(chatgpt, "rb") as f:
                resp = client.post(
                    "/ingest/ai-export",
                    files={"file": (chatgpt.name, f, "application/octet-stream")},
                    data={"source_type": "chatgpt"},
                )
            resp.raise_for_status()
            job_id = resp.json()["job_id"]
            result = _poll_job(job_id)
            if result["status"] == "complete":
                console.print(f"[green]ChatGPT export ingested: {result.get('memories_found', 0)} memories extracted[/green]")
            else:
                console.print(f"[red]Ingestion failed: {result.get('error_message', 'unknown error')}[/red]")

        if claude:
            if not claude.exists():
                console.print(f"[red]File not found: {claude}[/red]")
                raise typer.Exit(1)
            console.print(f"[bold]Uploading Claude export:[/bold] {claude.name}")
            with open(claude, "rb") as f:
                resp = client.post(
                    "/ingest/ai-export",
                    files={"file": (claude.name, f, "application/octet-stream")},
                    data={"source_type": "claude"},
                )
            resp.raise_for_status()
            job_id = resp.json()["job_id"]
            result = _poll_job(job_id)
            if result["status"] == "complete":
                console.print(f"[green]Claude export ingested: {result.get('memories_found', 0)} memories extracted[/green]")
            else:
                console.print(f"[red]Ingestion failed: {result.get('error_message', 'unknown error')}[/red]")


@app.command()
def gaps():
    """Show memory coverage gaps and what categories need more stories."""
    with _client() as client:
        resp = client.get("/memory/gaps")
        resp.raise_for_status()
        data = resp.json()

    gap_list = data.get("gaps", [])
    if not gap_list:
        console.print("[green]No gaps detected — all categories have sufficient coverage.[/green]")
        return

    table = Table(title=f"Memory Gaps ({len(gap_list)} categories below minimum)", show_header=True)
    table.add_column("Category", style="bold")
    table.add_column("Have", justify="right")
    table.add_column("Need", justify="right")
    table.add_column("Priority", justify="center")
    table.add_column("Suggested Questions")

    for gap in gap_list:
        priority = gap.get("priority", "low")
        color = {"high": "red", "medium": "yellow", "low": "green"}.get(priority, "white")
        suggested = gap.get("suggested_questions", [])
        sq_text = suggested[0] if suggested else ""
        table.add_row(
            gap.get("category", ""),
            str(gap.get("have", 0)),
            str(gap.get("need", 0)),
            f"[{color}]{priority.upper()}[/{color}]",
            sq_text[:70] + "..." if len(sq_text) > 70 else sq_text,
        )

    console.print(table)


@app.command()
def profile():
    """Show your memory profile — total memories and category breakdown."""
    with _client() as client:
        resp = client.get("/memory/profile")
        resp.raise_for_status()
        data = resp.json()

    total = data.get("total_memories", 0)
    by_cat = data.get("by_category", {})
    top = data.get("top_memories", [])
    prof = data.get("profile")

    console.print(Panel(
        f"[bold]Total Memories:[/bold] {total}",
        title="[bold blue]MNEMIX — Memory Profile[/bold blue]",
        border_style="blue",
    ))

    if prof:
        console.print(f"[dim]Field:[/dim] {prof.get('field', 'N/A')}  |  [dim]Seniority:[/dim] {prof.get('seniority', 'N/A')}")

    if by_cat:
        table = Table(title="Memories by Category", show_header=True)
        table.add_column("Category", style="bold")
        table.add_column("Count", justify="right")
        for cat, cnt in sorted(by_cat.items(), key=lambda x: -x[1]):
            table.add_row(cat, str(cnt))
        console.print(table)

    if top:
        console.print("\n[bold]Most-Accessed Memories:[/bold]")
        for i, m in enumerate(top[:3], 1):
            console.print(f"  {i}. [{m.get('category', '')}] {m.get('content', '')[:100]}...")


@app.command()
def history():
    """Show past interview sessions."""
    with _client() as client:
        resp = client.get("/interview/sessions")
        resp.raise_for_status()
        sessions = resp.json()

    if not sessions:
        console.print("[dim]No sessions yet. Run [bold]python cli.py interview[/bold] to start one.[/dim]")
        return

    table = Table(title="Interview History", show_header=True)
    table.add_column("#", justify="right")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Score", justify="right")
    table.add_column("Started")
    table.add_column("ID (short)")

    for i, s in enumerate(sessions, 1):
        score = s.get("overall_score")
        score_str = f"{score:.0f}/100" if score is not None else "—"
        started = (s.get("started_at") or "")[:16].replace("T", " ")
        short_id = (s.get("id") or "")[:8]
        status = s.get("status", "")
        color = {"complete": "green", "in_progress": "yellow", "evaluating": "blue"}.get(status, "white")
        table.add_row(str(i), s.get("session_type", ""), f"[{color}]{status}[/{color}]", score_str, started, short_id)

    console.print(table)


@app.command()
def interview(
    session_type: str = typer.Option("mixed", "--type", "-t", help="behavioral | technical | mixed"),
):
    """Run a full mock interview session."""
    if session_type not in ("behavioral", "technical", "mixed"):
        console.print("[red]--type must be behavioral, technical, or mixed[/red]")
        raise typer.Exit(1)

    console.print(Panel(
        "[bold blue]MNEMIX[/bold blue] — Memory-Powered Interview Coach\n"
        "[dim]Answer each question as you would in a real interview.\n"
        "Press Enter twice to submit your answer.[/dim]",
        border_style="blue",
    ))

    with _client() as client:
        # Start session
        resp = client.post("/interview/start", json={"session_type": session_type})
        if resp.status_code != 200:
            console.print(f"[red]Failed to start session: {resp.text}[/red]")
            raise typer.Exit(1)

        data = resp.json()
        session_id = data["session_id"]
        total = data["total_questions"]
        current_q = data["current_question"]

        console.print(f"\n[dim]Session ID: {session_id[:8]}... | {total} questions | Type: {session_type}[/dim]\n")

        answer_order = 0
        while current_q:
            idx = current_q.get("index", 0) + 1
            q_text = current_q.get("text", "")
            q_id = current_q.get("id", "")
            category = current_q.get("category", "")

            console.print(Panel(
                f"[bold]{q_text}[/bold]\n[dim]Category: {category}[/dim]",
                title=f"[bold]Question {idx} of {total}[/bold]",
                border_style="cyan",
            ))

            # Multi-line input: blank line to submit
            console.print("[dim]Your answer (press Enter twice to submit):[/dim]")
            lines = []
            try:
                while True:
                    line = input()
                    if line == "" and lines and lines[-1] == "":
                        break
                    lines.append(line)
            except (EOFError, KeyboardInterrupt):
                console.print("\n[yellow]Interview cancelled.[/yellow]")
                raise typer.Exit(0)

            answer_text = "\n".join(lines).strip()
            if not answer_text:
                answer_text = "[No answer provided]"

            # Submit answer
            payload = {
                "session_id": session_id,
                "question_id": q_id,
                "question_text": q_text,
                "answer_text": answer_text,
                "answer_order": answer_order,
            }
            answer_order += 1

            resp = client.post("/interview/answer", json=payload)
            if resp.status_code != 200:
                console.print(f"[red]Failed to submit answer: {resp.text}[/red]")
                raise typer.Exit(1)

            result = resp.json()

            if result.get("session_complete"):
                console.print("\n[green]All questions answered. Generating evaluation...[/green]")
                break
            else:
                current_q = result.get("next_question")
                console.print("\n[dim]Moving to next question...[/dim]\n")

        # Poll for evaluation (LLM evaluation takes 30-120s with Groq)
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Evaluating your answers...", total=None)
            attempts = 0
            while attempts < 120:
                resp = client.get(f"/interview/evaluate/{session_id}")
                resp.raise_for_status()
                eval_data = resp.json()
                if eval_data.get("status") == "evaluating":
                    time.sleep(5)
                    attempts += 1
                    progress.update(task, description=f"Evaluating... ({attempts * 5}s elapsed)")
                else:
                    break

    # Display feedback report
    if "report_text" in eval_data:
        score = eval_data.get("overall_score", 0)
        report = eval_data.get("report_text", "")

        score_color = "green" if score >= 70 else "yellow" if score >= 50 else "red"
        console.print(Panel(
            f"[bold {score_color}]Overall Score: {score:.0f}/100[/bold {score_color}]\n\n{report}",
            title="[bold]MNEMIX Interview Feedback[/bold]",
            border_style=score_color,
        ))

        evals = eval_data.get("evaluations", [])
        if evals:
            console.print("\n[bold]Per-Question Breakdown:[/bold]")
            for i, e in enumerate(evals, 1):
                score_q = e.get("total_score", 0)
                feedback = e.get("specific_feedback", "")
                missed = e.get("memory_opportunity_missed")
                console.print(f"\n  [bold]Q{i}:[/bold] [dim]{e.get('question_text', '')[:70]}...[/dim]")
                console.print(f"  Score: [bold]{score_q:.0f}/100[/bold]  |  {feedback}")
                if missed:
                    console.print(f"  [yellow]Memory opportunity missed:[/yellow] {missed}")
    else:
        console.print(f"[yellow]Evaluation result: {eval_data}[/yellow]")


if __name__ == "__main__":
    app()
