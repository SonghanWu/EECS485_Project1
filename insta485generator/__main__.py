"""Build static HTML site from directory of HTML templates and plain files."""

import json
import pathlib
import shutil
import sys
import jinja2
import click


def read_config(input_path):
    """
    Read and return config list from config.json under input_path.

    :param input_path: Path object to input directory.
    :return: A list of config items (dict) loaded from config.json.
    """
    config_filename = input_path / "config.json"
    try:
        with config_filename.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"insta485generator error: '{config_filename}' not found")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"insta485generator error: '{config_filename}'")
        print(str(exc))
        sys.exit(1)


def init_jinja(template_dir):
    """
    Initialize and return a Jinja2 Environment.

    :param template_dir: Path object to 'templates/' directory.
    :return: A jinja2.Environment instance.
    """
    if not template_dir.is_dir():
        print(f"insta485generator error: '{template_dir}' not found")
        sys.exit(1)

    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
    )


def render_templates(config_list, template_env, output_path, verbose=False):
    """
    Render templates according to config_list and write outputs.

    :param config_list: A list of dict items from config.json
    :param template_env: A jinja2.Environment
    :param output_path: Path object for the output directory
    :param verbose: Bool for printing extra info
    """
    for item in config_list:
        template_name = item["template"]
        context = item["context"]
        url = item["url"].lstrip("/")

        # Render
        try:
            template = template_env.get_template(template_name)
            rendered_html = template.render(context)
        except jinja2.TemplateSyntaxError as exc:
            print(f"insta485generator error: '{exc.name}'")
            print(exc.message)
            sys.exit(1)

        # Write output
        out_file = output_path / url / "index.html"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with out_file.open("w", encoding="utf-8") as outf:
            outf.write(rendered_html)

        if verbose:
            print(f"Rendered {template_name} -> {out_file}")


def copy_static(input_path, output_path, verbose=False):
    """
    Copy static files from 'input_path/static' to 'output_path'.

    :param input_path: Path to the input directory
    :param output_path: Path to output directory
    :param verbose: Bool for printing extra info
    """
    static_dir = input_path / "static"
    if static_dir.is_dir():
        for item in static_dir.iterdir():
            dest = output_path / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
        if verbose:
            print(f"Copied {static_dir} -> {output_path}")


@click.command(help="Templated static website generator.")
@click.argument(
    "input_dir",
    nargs=1,
    type=click.Path(exists=True)
)
@click.option(
    "--output", "-o",
    "output_dir",
    type=click.Path(),
    help="Output directory."
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Print more output."
)
def main(input_dir, output_dir, verbose):
    """
    Generate main entry point for the static site generator.

    :param input_dir: The input directory containing templates/config.json
    :param output_dir: The directory to output rendered HTML
    :param verbose: If True, print more info
    """
    input_path = pathlib.Path(input_dir)
    if output_dir is None:
        output_path = input_path / "html"
    else:
        output_path = pathlib.Path(output_dir)

    # Read config
    config_list = read_config(input_path)

    # Initialize jinja
    template_env = init_jinja(input_path / "templates")

    # Render
    render_templates(config_list, template_env, output_path, verbose=verbose)

    # Copy static
    copy_static(input_path, output_path, verbose=verbose)


if __name__ == "__main__":
    main()
