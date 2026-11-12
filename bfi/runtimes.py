"""Connection presets, not installers or assertions about model capabilities."""

PRESETS = {
    "custom": {"label": "Custom local endpoint", "base_url": "http://127.0.0.1:8080/v1"},
    "llama_cpp": {"label": "llama.cpp", "base_url": "http://127.0.0.1:8080/v1"},
    "strata": {"label": "Strata", "base_url": "http://127.0.0.1:8080/v1"},
    "lmstudio": {"label": "LM Studio", "base_url": "http://127.0.0.1:1234/v1"},
    "ollama": {"label": "Ollama", "base_url": "http://127.0.0.1:11434/v1"},
}


def preset(name):
    if name not in PRESETS:
        raise ValueError("BFI_RUNTIME must be custom, llama_cpp, strata, lmstudio, or ollama.")
    return PRESETS[name]


def catalog():
    return [
        {"id": name, **value, "installed_by_app": False, "inference_verified": False}
        for name, value in PRESETS.items()
    ]
