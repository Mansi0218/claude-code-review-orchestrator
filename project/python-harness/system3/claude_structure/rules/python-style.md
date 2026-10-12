---
applies_to:
  - "src/**/*.py"
  - "tests/**/*.py"
priority: high
enabled: true
---

# Python Style Rules

## Code Formatting

- Follow PEP 8 style guide
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use double quotes for strings

## Import Organization

1. Standard library imports
2. Third-party imports
3. Local application imports

Separate each group with a blank line.

## Type Hints

- Use type hints for all function parameters and return values
- Import from typing module (List, Dict, Optional, etc.)
- Use Optional[T] for values that can be None

## Docstrings

- Use triple-quoted docstrings
- Follow Google style for docstrings
- Document all public functions and classes

## Comments

- Use comments to explain WHY, not WHAT
- Keep comments up-to-date with code changes
- Use # for inline comments, separated by 2 spaces from code
