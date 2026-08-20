import re

# ----------------------------------------------------------------------
# LAYER 1 — Maximum input length
# ----------------------------------------------------------------------
MAX_LENGTH = 500

# ----------------------------------------------------------------------
# LAYER 2 — Regex injection blocklist (checked against user INPUT)
# ----------------------------------------------------------------------
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now",
    r"pretend\s+you\s+are",
    r"act\s+as\s+if\s+you\s+have\s+no",
    r"[A-Za-z0-9+/]{40,}={0,2}",  # base64-like string, 40+ characters
]

_compiled_injection_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def validate_input(user_input: str):
    """
    Returns (is_valid: bool, error_message: str | None)
    """
    if len(user_input) > MAX_LENGTH:
        return False, f"Input exceeds maximum allowed length of {MAX_LENGTH} characters."

    for pattern in _compiled_injection_patterns:
        if pattern.search(user_input):
            return False, "Input blocked: potential prompt injection pattern detected."

    return True, None


# ----------------------------------------------------------------------
# LAYER 3 — Output scanner (checked against MODEL RESPONSE)
# ----------------------------------------------------------------------
OUTPUT_BLOCK_PATTERNS = [
    r"password\s*[:=]",
    r"api[_\s]?key\s*[:=]",
    r"token\s*[:=]",
    r"https?://\S+",
]

_compiled_output_patterns = [re.compile(p, re.IGNORECASE) for p in OUTPUT_BLOCK_PATTERNS]


def scan_output(model_output: str, system_prompt: str = ""):
    """
    Returns (is_safe: bool, error_message: str | None)
    """
    for pattern in _compiled_output_patterns:
        if pattern.search(model_output):
            return False, "Response blocked: potential sensitive data pattern detected in model output."

    if system_prompt:
        marker = system_prompt.strip()[:60]
        if len(marker) > 20 and marker.lower() in model_output.lower():
            return False, "Response blocked: system prompt leakage detected."

    return True, None