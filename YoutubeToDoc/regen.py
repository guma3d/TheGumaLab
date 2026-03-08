import os
import sys
from Server import app, task_status_path, load_task_status

with app.test_request_context('/admin/regenerate-html', method='POST'):
    from flask import session
    session['admin_logged_in'] = True
    from Server import admin_regenerate_html
    resp = admin_regenerate_html()
    print(resp.get_data(as_text=True))
