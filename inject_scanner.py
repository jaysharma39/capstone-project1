#!/usr/bin/env python3
"""
inject_scanner.py

Custom static scanner for Project 5 (Gate 4 of security.yml).

Searches every .py file in the repository for:
  1. Hardcoded system-prompt-style assignments (SYSTEM_PROMPT_PATTERNS)
  2. Common prompt-injection bypass phrasing (INJECTION_PHRASES)

Exits with code 1 if any match is found (fails the pipeline gate).
Exits with code 0 if the repository is clean.
"""

import os
import re
import sys

# ---------------------------------------------------------------------------
# Patterns that indicate a hardcoded system prompt / role message in source
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_PATTERNS = [
    r"SYSTEM_PROMPT\s*=",
    r"system_message\s*=",
    r"[\"']role[\"']\s*:\s*[\"']system[\"']",
]

# ---------------------------------------------------------------------------
# Phrases commonly used in prompt-injection / jailbreak payloads that should
# never appear hardcoded inside application source (e.g. left over from
# testing, or embedded as "defaults" that a poisoned resource could echo).
# ---------------------------------------------------------------------------
INJECTION_PHRASES = [
    "ignore previous instructions",
    "you are now",
    "pretend you are",
    "act as if you have no restrictions",
]

# Directories we never want to scan (keeps CI fast and avoids false
# positives from dependencies / virtual environments / git internals).
EXCLUDED_DIRS = {
    ".git",
    ".github",
    "venv",
    "ai-lab",
    "redteam-env",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
}


def iter_python_files(root="."):
    """Yield paths to every .py file under root, skipping excluded dirs."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            if filename.endswith(".py") and filename != os.path.basename(__file__):
                yield os.path.join(dirpath, filename)


def scan_file(path):
    """
    Scan a single file for system-prompt patterns and injection phrases.
    Returns a list of (line_number, matched_text, category) tuples.
    """
    findings = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except OSError as e:
        print(f"  [WARN] Could not read {path}: {e}")
        return findings

    for line_number, line in enumerate(lines, start=1):
        for pattern in SYSTEM_PROMPT_PATTERNS:
            match = re.search(pattern, line)
            if match:
                # Only flag this as a finding if the assignment's right-hand
                # side is a hardcoded literal, not a safe environment-variable
                # lookup (e.g. os.environ.get(...) / os.getenv(...)).
                after_match = line[match.end():]
                is_env_lookup = bool(
                    re.search(r"^\s*os\.(environ\.get|getenv)\s*\(", after_match)
                )
                if not is_env_lookup:
                    findings.append((line_number, line.strip(), f"system-prompt pattern: {pattern}"))

        lowered = line.lower()
        for phrase in INJECTION_PHRASES:
            if phrase in lowered:
                findings.append((line_number, line.strip(), f"injection phrase: '{phrase}'"))

    return findings


def main():
    print("=" * 70)
    print("inject_scanner.py — Custom Prompt Injection / System Prompt Scanner")
    print("=" * 70)

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    total_findings = 0

    for filepath in iter_python_files(root):
        findings = scan_file(filepath)
        if findings:
            print(f"\n[FOUND] {filepath}")
            for line_number, text, category in findings:
                print(f"  Line {line_number}: {category}")
                print(f"    -> {text}")
            total_findings += len(findings)

    print("\n" + "-" * 70)
    if total_findings > 0:
        print(f"RESULT: {total_findings} issue(s) found. Gate 4 FAILED.")
        print("-" * 70)
        sys.exit(1)
    else:
        print("RESULT: No hardcoded system prompts or injection phrases found. Gate 4 PASSED.")
        print("-" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()
