from api.services.feedback_service import process_time_location_feedback
import json

q_id = "73673ea3-51fa-44d9-9198-30549d562a35"
tp = '["73673ea3-51fa-44d9-9198-30549d562a35", "cc9776d6-68fb-4d87-9eed-35804fadd7a4", "9e1c4a16-6c84-4869-aa57-30e3bb9706ce"]'
process_time_location_feedback(q_id, "2025-01", "Unknown Location", tp)
