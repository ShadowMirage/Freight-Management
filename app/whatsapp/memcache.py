from typing import Dict, Any

# Simple in-memory storage for pending matches to fulfill Phase 7 selection
# { phone: { "type": "truck"|"load", "my_id": "uuid", "matches": [...] } }
PENDING_MATCHES: Dict[str, Any] = {}
