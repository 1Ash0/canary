"""ctxcheck CLI — entry point for `ctxcheck run ...`

Not yet implemented beyond the command skeleton (M2).
"""

import typer

app = typer.Typer(
    name="ctxcheck",
    help="Test kit and flight recorder for agent context-compaction policies.",
    no_args_is_help=True,
)


@app.command()
def run(
    scenario: str = typer.Option(..., help="Scenario / canary pack name"),
    policy: str = typer.Option(..., help="Compaction policy name"),
    model: str = typer.Option("claude-3-5-sonnet-20241022", help="Model to test"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print plan without running"),
    max_usd: float = typer.Option(0.0, "--max-usd", help="Hard cost cap (required for live runs)"),
) -> None:
    """Run a canary scenario under a compaction policy."""
    typer.echo(f"scenario={scenario!r} policy={policy!r} model={model!r}")
    if dry_run:
        typer.echo("[dry-run] no API calls will be made")
    else:
        typer.echo("Not yet implemented — coming in M2.")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
