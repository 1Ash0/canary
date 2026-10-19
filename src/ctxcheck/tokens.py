"""Token counting — local estimates only.

Provider-reported usage is always in the trace (`model_call.usage`).
This module gives cheap local estimates for budget checks before a call.
The difference between local estimate and provider count is itself a thing
worth understanding (U0 in docs/LEARNING.md).
"""

# Not yet implemented — built in U0.
