from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from .backends.ollama_embed import OllamaEmbed
from .backends.ollama_llm import OllamaLLM
from .chat_session import ChatSession
from .config import load_config
from .context_builder import ContextBuilder
from .indexer import Chunker, FileScanner
from .logger import SessionLogger
from .project_manager import ProjectManager
from .retriever import Retriever

app = typer.Typer(help="Java Code Q&A RAG Agent")
console = Console()


def get_services(config_path: str = "config.yaml"):
    config = load_config(config_path)
    pm = ProjectManager(config_dir=config.storage.index_dir)
    return config, pm


@app.command()
def index(
    project: str = typer.Option(..., "--project", "-p", help="Project name"),
    path: str = typer.Option(..., "--path", help="Path to Java project root"),
):
    """Index a Java project."""
    config, pm = get_services()

    project_path = Path(path).expanduser().absolute()
    if not project_path.exists():
        console.print(f"[red]Error: Path {project_path} does not exist.[/red]")
        raise typer.Exit(1)

    # Check Ollama
    llm = OllamaLLM(config.ollama)
    if not llm.check_connection():
        console.print("[red]Error: Cannot connect to Ollama or models not found.[/red]")
        console.print(
            f"Make sure Ollama is running and you have pulled: {config.ollama.model} and {config.ollama.embed_model}"
        )
        console.print(
            f"Commands:\n  ollama pull {config.ollama.model}\n  ollama pull {config.ollama.embed_model}"
        )
        raise typer.Exit(1)

    # Initialize logger for system logs
    logger = SessionLogger(
        config.storage.log_dir, project, enabled=config.storage.save_logs
    )

    pm.register_project(project, str(project_path))

    with console.status(f"[bold green]Scanning files in {project_path}..."):
        scanner = FileScanner(project_path)
        files = scanner.scan()

    if not files:
        console.print("[yellow]No .java files found in src/ directory.[/yellow]")
        raise typer.Exit()

    console.print(f"Found {len(files)} Java files.")

    with console.status("[bold green]Chunking and Embedding..."):
        chunker = Chunker(
            threshold=config.rag.chunk_token_threshold,
            max_chars=config.rag.max_chunk_chars,
        )
        embedder = OllamaEmbed(config.ollama)
        retriever = Retriever(config.storage.index_dir, project)

        # Clear existing index
        retriever.delete_index()

        all_chunks = []
        for f in files:
            content = f.read_text()
            chunks = chunker.chunk(str(f.relative_to(project_path)), content)
            all_chunks.extend(chunks)

        # Batch embedding
        batch_size = 10
        embedded_count = 0
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i : i + batch_size]
            embeddings = embedder.embed_batch([c.content for c in batch])
            
            # Filter out chunks with failed embeddings
            valid_batch = []
            valid_embeddings = []
            for c, e in zip(batch, embeddings):
                if e:
                    valid_batch.append(c)
                    valid_embeddings.append(e)
            
            if valid_batch:
                retriever.add_chunks(valid_batch, valid_embeddings)
                embedded_count += len(valid_batch)
    
    console.print(f"Indexed [bold green]{embedded_count}/{len(all_chunks)}[/bold green] chunks.")

    pm.update_indexed_at(project)
    console.print(
        f"[bold green]Index built successfully for project: {project}[/bold green]"
    )


@app.command()
def chat(project: str = typer.Option(..., "--project", "-p", help="Project name")):
    """Start a chat session for a project."""
    config, pm = get_services()

    try:
        proj_info = pm.get_project(project)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        list_projects()
        raise typer.Exit(1) from e

    if not proj_info.get("indexed_at"):
        console.print(
            f"[yellow]Project {project} is not indexed yet. "
            "Please run index command first.[/yellow]"
        )
        console.print(
            f"Example: java-qa index --project {project} --path {proj_info['path']}"
        )
        raise typer.Exit(1)

    # Check Ollama
    llm = OllamaLLM(config.ollama)
    if not llm.check_connection():
        console.print("[red]Error: Cannot connect to Ollama.[/red]")
        raise typer.Exit(1)

    embedder = OllamaEmbed(config.ollama)
    retriever = Retriever(config.storage.index_dir, project)
    ctx_builder = ContextBuilder(
        java_version=config.java_version, max_tokens=config.rag.max_input_tokens
    )
    session = ChatSession(max_history=config.rag.max_history_turns)
    logger = SessionLogger(
        config.storage.log_dir, project, enabled=config.storage.save_logs
    )

    console.print(
        Panel(
            f"Chatting with [bold cyan]{project}[/bold cyan]\nPath: {proj_info['path']}\nType 'exit' or 'quit' to end.",
            title="Java QA Agent",
        )
    )

    while True:
        try:
            question = console.input("[bold green]You>[/bold green] ")
            if question.lower() in ["exit", "quit"]:
                break
            if not question.strip():
                continue

            with console.status("[bold blue]Thinking..."):
                # RAG Workflow
                q_embedding = embedder.embed_query(question)
                chunks = retriever.query(q_embedding, top_k=config.rag.top_k)
                prompt = ctx_builder.build_prompt(
                    chunks, session.get_history(), question
                )
                answer = llm.generate(prompt)

            console.print(Markdown(answer))
            console.print("-" * 20)

            session.add_message("user", question)
            session.add_message("assistant", answer)
            logger.log_interaction(question, answer)

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command(name="list")
def list_projects():
    """List all registered projects."""
    _, pm = get_services()
    projects = pm.list_projects()

    if not projects:
        console.print("No projects registered.")
        return

    table = Table(title="Registered Projects")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("Indexed At", style="magenta")

    for name, info in projects.items():
        table.add_row(name, info["path"], str(info.get("indexed_at", "Never")))

    console.print(table)


@app.command()
def delete(project: str = typer.Option(..., "--project", "-p", help="Project name")):
    """Delete a project index."""
    _, pm = get_services()
    try:
        pm.delete_project(project)
        console.print(f"[green]Deleted project: {project}[/green]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")


if __name__ == "__main__":
    app()
