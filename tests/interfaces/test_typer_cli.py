from typer.testing import CliRunner
from raman_fitting.interfaces.typer_cli import app

runner = CliRunner()


def test_version_callback():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Awesome Typer CLI Version:" in result.stdout


def test_run_command():
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "Selection of models to use for deconvolution." in result.stdout


def test_run_command_with_arguments():
    result = runner.invoke(
        app, ["run", "--models", "model1", "--sample-ids", "sample1"]
    )
    assert result.exit_code == 0
    assert "Index is empty" in result.stdout

    # assert "Starting raman_fitting with CLI run mode:" in result.stdout


def test_make_command():
    result = runner.invoke(app, ["make", "--help"])
    assert result.exit_code == 0
    assert "make_type" in result.stdout


def test_make_example_command():
    result = runner.invoke(app, ["make", "example"])
    assert result.exit_code == 0


def test_make_index_command():
    result = runner.invoke(app, ["make", "index"])
    assert result.exit_code == 0
    assert (
        "initialized  and saved" in result.stdout
    )  # Adjust this based on actual output


def test_make_config_command():
    result = runner.invoke(app, ["make", "config"])
    assert result.exit_code == 0
    assert "config file created" in result.stdout  # Adjust this based on actual output
