from flask import Flask, request, render_template, send_file
from PIL import Image
import io
import os

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_and_resize():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file uploaded'
        
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        
        if file and allowed_file(file.filename):
            # Read the image
            img = Image.open(file)
            
            # Get resize parameters
            width = int(request.form.get('width', img.width))
            height = int(request.form.get('height', img.height))
            
            # Resize image using LANCZOS resampling for better quality
            resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Save to bytes buffer
            img_buffer = io.BytesIO()
            resized_img.save(img_buffer, format=img.format)
            img_buffer.seek(0)
            
            return send_file(
                img_buffer,
                mimetype=f'image/{img.format.lower()}',
                as_attachment=True,
                download_name=f'resized_{file.filename}'
            )
            
    return render_template('upload.html')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
