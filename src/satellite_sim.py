"""
Satellite simulator that stages uplink events for offline alerting.
Supports success and failure modes.
"""
import time
from datetime import datetime, timedelta
import random

def send(payload, delay_seconds=1.0, fail=False):
    """
    Simulate satellite uplink with staged events.
    Returns list of events with UTC timestamps and payload.
    
    Args:
        payload (dict/str): Data to uplink
        delay_seconds (float): Base delay multiplier
        fail (bool): If True, simulate a failure instead of success
    """
    stages_success = [
        ("queued", "Queued for uplink", delay_seconds * 0.2),
        ("uplink", "Uplink in progress", delay_seconds * 0.5),
        ("delivered", "Delivered to satellite network", delay_seconds * 0.3),
    ]
    
    stages_failure = [
        ("queued", "Queued for uplink", delay_seconds * 0.2),
        ("uplink", "Uplink in progress", delay_seconds * 0.5),
        ("failed", "Transmission error — uplink dropped", delay_seconds * 0.3),
    ]
    
    stages = stages_failure if fail else stages_success
    
    events = []
    now = datetime.utcnow()
    for i, (status, note, delay) in enumerate(stages):
        time.sleep(delay)
        events.append({
            "time": (now + timedelta(seconds=i)).isoformat(),
            "status": status,
            "note": note,
            "payload": payload
        })
    return events

# Example usage:
# Normal success path
# events = send({"msg":"alert"}, delay_seconds=1.0)
# Failure path
# events = send({"msg":"alert"}, delay_seconds=1.0, fail=True)
