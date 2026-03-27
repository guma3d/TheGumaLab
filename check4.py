from api.services.feedback_service import process_time_location_feedback
import json
import traceback

def test_json(tp_str):
    print("Received string:", repr(tp_str))
    try:
        if tp_str:
            t = json.loads(tp_str)
            print("Loaded OK, len:", len(t))
    except Exception as e:
        print("JSON parse failed:", e)
        traceback.print_exc()

test_json('["73673ea3-51fa-44d9-9198-30549d562a35", "cc9776d6-68fb-4d87-9eed-35804fadd7a4", "9e1c4a16-6c84-4869-aa57-30e3bb9706ce"]')
