---
name: python-code-reviewer
description: This skill should be used when reviewing Python code for quality,
  correctness, and adherence to best practices. Applies to code reviews,
  PR feedback, refactoring suggestions, and debugging assistance.
---

# Python Code Review Skill

Review Python code systematically for quality, correctness, security, and
maintainability. Provide actionable, specific feedback rather than generic
observations.

## Review Process

Work through the following areas in order:

**1. Correctness**

- Identify logic errors, off-by-one errors, and incorrect assumptions
- Check edge cases: empty inputs, None values, large inputs, concurrent access
- Verify error handling is present and appropriate

**2. Code Quality**

- Flag violations of PEP 8 (naming, spacing, line length)
- Identify overly complex functions that should be decomposed
- Note missing or insufficient docstrings and type hints

**3. Security**

- Check for SQL injection risks if database queries are present
- Flag hardcoded credentials or secrets
- Identify unsafe use of `eval()`, `exec()`, or `pickle`

**4. Performance**

- Note O(n²) or worse patterns where a better approach exists
- Flag unnecessary repeated computation inside loops
- Identify missing use of generators or lazy evaluation for large datasets

**5. Testing**

- Note untested code paths
- Suggest specific test cases for edge cases identified above

## Output Format

Structure feedback as:

- **Critical**: Must fix before merge (bugs, security issues)
- **Suggested**: Strong recommendations (quality, performance)
- **Optional**: Nice to have (style, minor improvements)

For each issue, include: location, problem description, and a corrected code
snippet where helpful.

## Guidelines

- Be specific — reference line numbers or function names
- Prioritize issues that affect correctness over style
- Acknowledge good patterns when present, not just problems
- If the code is generally clean, say so briefly before detailing minor issues
