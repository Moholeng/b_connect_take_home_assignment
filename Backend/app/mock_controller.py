"""Simulates the third-party Wi-Fi controller API.

In production this module would issue an HTTP request to the real
controller. For the prototype it loads a static JSON payload from disk,
which keeps the demo deterministic and removes an external dependency.
"""

import json
from pathlib import Path

# mock_data.json lives at the backend root, one level above the app package.
_PAYLOAD_PATH = Path(__file__).resolve().parent.parent / "mock_data.json"


class ControllerError(RuntimeError):
    """Raised when the (simulated) controller request fails."""


def fetch_controller_data(simulate_failure: bool = False) -> dict:
    """Return the controller payload, or raise to simulate an outage.

    Args:
        simulate_failure: When True, raise ``ControllerError`` to exercise
            the backend's error-handling and failed-sync logging path.

    Returns:
        The decoded JSON payload as a dictionary.
    """
    if simulate_failure:
        raise ControllerError("Simulated controller timeout (HTTP 504).")

    try:
        with _PAYLOAD_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise ControllerError(f"Mock payload not found at {_PAYLOAD_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise ControllerError(f"Mock payload is not valid JSON: {exc}") from exc