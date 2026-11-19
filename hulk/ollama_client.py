
import requests

from hulk.config import OLLAMA_URL, OLLAMA_MODEL


def check_ollama():
    """Check whether Ollama is running."""
    try:
        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=5
        )

        if response.status_code != 200:
            return False, "Ollama server is not responding."

        models = response.json().get("models", [])

        model_names = [
            model.get("name", "")
            for model in models
        ]

        model_found = any(
            name == OLLAMA_MODEL
            or name.split(":")[0] == OLLAMA_MODEL.split(":")[0]
            for name in model_names
        )

        if not model_found:
            return False, f"Model {OLLAMA_MODEL} is not installed."

        return True, "Ollama connected successfully."

    except requests.RequestException:
        return False, "Cannot connect to Ollama. Start Ollama first."


def generate_response(prompt, system_prompt=None, stream=False):
    """Generate a response using the local Ollama model."""

    messages = []

    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": 0.4
        }
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=180
        )

        response.raise_for_status()

        data = response.json()

        return data.get("message", {}).get("content", "").strip()

    except requests.ConnectionError:
        return "ERROR: Cannot connect to Ollama. Check whether Ollama is running."

    except requests.Timeout:
        return "ERROR: Ollama took too long to respond."

    except requests.RequestException as error:
        return f"ERROR: Ollama request failed: {error}"

    except (ValueError, KeyError):
        return "ERROR: Invalid response received from Ollama."


def ask_ai(prompt, system_prompt=None):
    """Simple function for getting an AI answer."""
    return generate_response(
        prompt=prompt,
        system_prompt=system_prompt
    )
