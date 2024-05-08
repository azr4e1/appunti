from appunti.cli.cli import Cli
from appunti.cli.cli_config import _COMMANDS


def run() -> None:
    cli = Cli(prog="appunti", description="Zettelkasten manager", **_COMMANDS)
    cli.run()


if __name__ == "__main__":
    run()
