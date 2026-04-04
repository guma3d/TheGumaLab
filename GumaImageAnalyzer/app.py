import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from analyze import analyze_image, process_video

app = Flask(__name__)

# 설정
UPLOAD_FOLDER = 'uploads'
# ... 기존 설정 ...

@app.route('/analyze_video', methods=['POST'])
def analyze_video():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'No URL provided'}), 400
    
    url = data['url']
    try:
        results = process_video(url)
    except Exception as e:
         return jsonify({'error': str(e)}), 500
    
    if isinstance(results, dict) and "error" in results:
        return jsonify(results), 500
        
    return jsonify(results)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 저장된 이미지 분석
        result = analyze_image(filepath)
        
        # 정리 (선택사항: 공간 절약을 위해 분석 후 파일 삭제)
        # os.remove(filepath) 
        
        if "error" in result:
            return jsonify(result), 500
            
        return jsonify(result)
        
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
