from myproject_cli.main import GenesisCLI
from myproject_core.configs import settings
from myproject_core.workflow_engine import WorkflowEngine
from myproject_core.workflow_registry import WorkflowRegistry
from myproject_core.workspace import WorkspaceManager


def start():
    """
    Logic for starting the code
    """

    wm = WorkspaceManager(settings)
    registry = WorkflowRegistry(settings)
    engine = WorkflowEngine(wm)
    cli_app = GenesisCLI(settings, wm, registry, engine)

    cli_app()


if __name__ == "__main__":
    start()
