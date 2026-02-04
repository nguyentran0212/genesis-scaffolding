from myproject_cli.main import app as cli_app


def prestart():
    """
    Hook for logic before starting the main part of the code
    """
    pass

def start():
    """
    Logic for starting the code
    """
    prestart()
    cli_app()

if __name__ == "__main__":
    start()
