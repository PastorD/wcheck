"""Tests for the config-list command."""

import yaml
from click.testing import CliRunner

from wcheck.wcheck import cli


class TestConfigListCommand:
    """Tests for the config-list CLI command."""

    def test_config_list_help(self):
        """Test config-list command help displays correctly."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config-list", "--help"])
        assert result.exit_code == 0
        assert "Compare multiple configuration files" in result.output

    def test_config_list_missing_config(self):
        """Test config-list command without any config files."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config-list"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_config_list_single_config(self, config_file):
        """Test config-list command with a single config file."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config-list", "-c", str(config_file)])
        assert result.exit_code == 0

    def test_config_list_two_configs(self, config_file, config_file_alt):
        """Test config-list command with two config files."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["config-list", "-c", str(config_file), "-c", str(config_file_alt)]
        )
        assert result.exit_code == 0
        # Should show differences between configs

    def test_config_list_with_full_flag(self, config_file, config_file_alt):
        """Test config-list command with --full flag."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "config-list",
                "-c",
                str(config_file),
                "-c",
                str(config_file_alt),
                "--full",
            ],
        )
        assert result.exit_code == 0

    def test_config_list_with_full_name_flag(self, config_file, config_file_alt):
        """Test config-list command with --full-name flag."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "config-list",
                "-c",
                str(config_file),
                "-c",
                str(config_file_alt),
                "--full-name",
            ],
        )
        assert result.exit_code == 0

    def test_config_list_with_verbose_flag(self, config_file, config_file_alt):
        """Test config-list command with --verbose flag."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["config-list", "-c", str(config_file), "-c", str(config_file_alt), "-v"],
        )
        assert result.exit_code == 0

    def test_config_list_nonexistent_config(self, config_file, tmp_path):
        """Test config-list command with a nonexistent config file."""
        nonexistent = tmp_path / "nonexistent.yaml"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["config-list", "-c", str(config_file), "-c", str(nonexistent)]
        )
        assert result.exit_code != 0

    def test_config_list_identical_configs(self, tmp_path):
        """Test config-list command with identical config files."""
        config_data = {
            "repositories": {
                "repo_a": {"version": "main"},
                "repo_b": {"version": "main"},
            }
        }

        config1 = tmp_path / "config1.yaml"
        config2 = tmp_path / "config2.yaml"

        with open(config1, "w") as f:
            yaml.dump(config_data, f)
        with open(config2, "w") as f:
            yaml.dump(config_data, f)

        runner = CliRunner()
        result = runner.invoke(
            cli, ["config-list", "-c", str(config1), "-c", str(config2)]
        )
        assert result.exit_code == 0
        assert "identical" in result.output.lower()

    def test_config_list_different_repos(self, tmp_path):
        """Test config-list command with configs having different repos."""
        config1_data = {
            "repositories": {
                "repo_a": {"version": "main"},
                "repo_b": {"version": "main"},
            }
        }
        config2_data = {
            "repositories": {
                "repo_a": {"version": "main"},
                "repo_c": {"version": "develop"},  # Different repo
            }
        }

        config1 = tmp_path / "config1.yaml"
        config2 = tmp_path / "config2.yaml"

        with open(config1, "w") as f:
            yaml.dump(config1_data, f)
        with open(config2, "w") as f:
            yaml.dump(config2_data, f)

        runner = CliRunner()
        result = runner.invoke(
            cli, ["config-list", "-c", str(config1), "-c", str(config2)]
        )
        assert result.exit_code == 0

    def test_config_list_three_configs(self, tmp_path):
        """Test config-list command with three config files."""
        configs = []
        for i in range(3):
            config_data = {
                "repositories": {
                    "repo_a": {"version": f"v{i}.0"},
                    "repo_b": {"version": "main"},
                }
            }
            config_path = tmp_path / f"config{i}.yaml"
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)
            configs.append(config_path)

        runner = CliRunner()
        cmd = ["config-list"]
        for c in configs:
            cmd.extend(["-c", str(c)])
        result = runner.invoke(cli, cmd)
        assert result.exit_code == 0
