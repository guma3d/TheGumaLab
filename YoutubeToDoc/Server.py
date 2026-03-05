from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url', '')
    
    if not url:
        return jsonify({'success': False, 'message': 'URL is required'})
    
    # 여기서 URL 파싱, 유튜브 스크립트 추출, Whisper 연동 등의 업그레이드 로직이 들어갈 예정입니다.
    print(f"Received URL: {url}")
    
    return jsonify({
        'success': True, 
        'message': 'Analysis request received successfully',
        'video_id': 'placeholder_id_123'
    })

if __name__ == '__main__':
    print("=" * 50)
    print("YoutubeToDoc Server Started")
    print("Listening on http://0.0.0.0:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
