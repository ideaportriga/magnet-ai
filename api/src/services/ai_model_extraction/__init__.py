"""Fill AI model settings (description, capabilities, pricing) from pasted text.

Kept import-free: the ai_models controller imports ``.schemas`` at module load,
and ``.service`` pulls in the prompt-template / LLM stack, which is loaded
lazily inside the request handler.
"""
