"""Configuration System - Orchestration Layer

This module coordinates the end-to-end configuration validation workflow.
Located at: src/configuration/orchestrator.py:12-89
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from .harness import ConfigurationHarness
from .model import RuleFrontmatter, SkillConfig


class ValidationResult:
    """Result of configuration validation"""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed = True

    def add_error(self, message: str):
        """Add validation error"""
        self.errors.append(message)
        self.passed = False

    def add_warning(self, message: str):
        """Add validation warning"""
        self.warnings.append(message)

    def get_exit_code(self) -> int:
        """Get exit code (0 for pass, 1 for fail)"""
        return 0 if self.passed else 1

    def get_status(self) -> str:
        """Get status string"""
        return "OK" if self.passed else "FAILED"

    def __str__(self) -> str:
        """String representation"""
        lines = []

        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  - {error}")

        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        lines.append(f"\nStatus: {self.get_status()}")
        lines.append(f"Exit Code: {self.get_exit_code()}")

        return '\n'.join(lines)


class ConfigValidator:
    """
    Orchestration layer for configuration validation

    Coordinates validation of CLAUDE.md, rules, skills, and imports.
    Located at: src/configuration/orchestrator.py:12-89
    """

    def __init__(self, project_root: Path):
        """Initialize validator with project root"""
        self.harness = ConfigurationHarness(project_root)
        self.result = ValidationResult()

    def validate_all(self) -> ValidationResult:
        """
        Run complete validation workflow

        Returns:
            ValidationResult with errors/warnings and exit code
        """
        self.result = ValidationResult()

        # Check .claude directory exists
        if not self.harness.claude_dir.exists():
            self.result.add_error(f".claude directory not found at {self.harness.claude_dir}")
            return self.result

        # Validate CLAUDE.md
        self._validate_claude_md()

        # Validate rule files
        self._validate_rule_files()

        # Validate skill files
        self._validate_skill_files()

        return self.result

    def _validate_claude_md(self):
        """Validate main CLAUDE.md file"""
        try:
            config = self.harness.load_claude_md()

            # Check imports
            invalid_imports = self.harness.validate_imports(config)

            if invalid_imports:
                for imp in invalid_imports:
                    self.result.add_error(f"Import path not found: {imp}")

            if not config.imports:
                self.result.add_warning("CLAUDE.md has no @path imports")

        except FileNotFoundError as e:
            self.result.add_error(str(e))
        except Exception as e:
            self.result.add_error(f"Error parsing CLAUDE.md: {e}")

    def _validate_rule_files(self):
        """Validate all rule files"""
        rule_files = self.harness.find_rule_files()

        if not rule_files:
            self.result.add_warning("No rule files found in .claude/rules/")
            return

        for rule_file in rule_files:
            try:
                frontmatter, content = self.harness.load_rule_file(rule_file)

                # Validate glob patterns
                if frontmatter.applies_to:
                    validation = self.harness.validate_glob_patterns(frontmatter.applies_to)

                    for pattern, is_valid in validation.items():
                        if not is_valid:
                            self.result.add_error(
                                f"Invalid glob pattern in {rule_file.name}: {pattern}"
                            )
                else:
                    self.result.add_warning(
                        f"Rule file {rule_file.name} has no applies_to patterns"
                    )

            except Exception as e:
                self.result.add_error(f"Error in {rule_file.name}: {e}")

    def _validate_skill_files(self):
        """Validate all skill files"""
        skill_files = self.harness.find_skill_files()

        if not skill_files:
            self.result.add_warning("No skill files found in .claude/skills/")
            return

        for skill_file in skill_files:
            try:
                skill_config = self.harness.load_skill_config(skill_file)

                # Check for fork context
                if skill_config.context == 'fork':
                    # Check for read-only tools
                    if not self.harness.check_read_only_tools(skill_config):
                        self.result.add_warning(
                            f"Forked skill {skill_config.name} has non-read-only tools"
                        )

                # Validate tools are not empty
                if not skill_config.allowed_tools:
                    self.result.add_warning(
                        f"Skill {skill_config.name} has no allowed_tools"
                    )

            except Exception as e:
                self.result.add_error(f"Error in {skill_file}: {e}")

    def run(self) -> int:
        """
        Run validator and return exit code

        Returns:
            0 if validation passes, 1 if it fails
        """
        result = self.validate_all()
        print(result)
        return result.get_exit_code()


def main(project_root: Optional[Path] = None):
    """Main entry point for configuration validator"""
    if project_root is None:
        project_root = Path.cwd()

    validator = ConfigValidator(project_root)
    exit_code = validator.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
