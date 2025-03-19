from graph import build_graph
from dotenv import load_dotenv

import click


@click.group()
def cli():
    pass


@click.command()
@click.argument("topic")
def research(topic: str):
    load_dotenv()
    click.echo(build_graph(topic))


cli.add_command(research)


if __name__ == "__main__":
    cli()
