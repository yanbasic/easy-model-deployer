import typer
from rich.console import Console
from rich.panel import Panel

from emd.constants import MODEL_DEFAULT_TAG
from typing_extensions import Annotated
from emd.sdk.destroy import destroy as sdk_destroy
from emd.utils.decorators import catch_aws_credential_errors,check_emd_env_exist,load_aws_profile
from emd.utils.logger_utils import make_layout
from emd.revision import convert_version_name_to_stack_name

app = typer.Typer(pretty_exceptions_enable=False)
console = Console()
layout = make_layout()


@app.callback(invoke_without_command=True)
@catch_aws_credential_errors
@check_emd_env_exist
@load_aws_profile
def destroy(
    model_identifier: Annotated[
        str,
        typer.Argument(
            help="Model identifier in format 'model_id/model_tag' (e.g., 'Qwen2.5-0.5B-Instruct/d2')"
        )
    ]
):
    """
    Destroy a model deployment.

    Examples:
        emd destroy Qwen2.5-0.5B-Instruct/d2
        emd destroy Qwen2.5-VL-32B-Instruct/twopath
        emd destroy DeepSeek-R1-0528-Qwen3-8B/dev
    """
    try:
        console.print(f"[yellow]Destroying model deployment: {model_identifier}[/yellow]")

        # Use the new SDK format
        sdk_destroy(model_identifier=model_identifier, waiting_until_complete=True)

        console.print(f"[green]✅ Model deployment '{model_identifier}' has been successfully deleted[/green]")
        console.print("[dim]The model stack and all associated resources have been removed[/dim]")

    except ValueError as e:
        console.print(f"[red]❌ Invalid format: {e}[/red]")
        console.print("[yellow]Expected format: 'model_id/model_tag'[/yellow]")
        console.print("[yellow]Examples:[/yellow]")
        console.print("  [cyan]emd destroy Qwen2.5-0.5B-Instruct/d2[/cyan]")
        console.print("  [cyan]emd destroy Qwen2.5-VL-32B-Instruct/twopath[/cyan]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Failed to destroy model deployment: {e}[/red]")
        raise typer.Exit(1)
