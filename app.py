from flask import Flask, request, render_template, send_file, flash
from PIL import Image
import io
import os
from dotenv import load_dotenv
import secrets

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(16)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(image, target_size_kb):
    img_buffer = io.BytesIO()
    
    if target_size_kb:
        current_size = 0
        quality = 95
        
        # First try with maximum quality
        image.save(img_buffer, format='JPEG', quality=100)
        current_size = img_buffer.tell() / 1024  # Convert to KB
        
        if current_size < target_size_kb:
            # If current size is smaller than target, use padding
            img_buffer = io.BytesIO()
            # Add metadata and padding to increase file size
            image.info['comment'] = 'x' * int((target_size_kb - current_size) * 1024)
            image.save(img_buffer, format='JPEG', quality=100)
        else:
            # If need to reduce size
            while quality > 5:
                img_buffer.seek(0)
                img_buffer.truncate(0)
                image.save(img_buffer, format='JPEG', quality=quality, optimize=True)
                if img_buffer.tell() / 1024 <= target_size_kb:
                    break
                quality -= 5
    else:
        # If no target size, save with high quality
        image.save(img_buffer, format='JPEG', quality=95)
    
    img_buffer.seek(0)
    return img_buffer

@app.route('/', methods=['GET', 'POST'])
def upload_and_resize():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return render_template('upload.html')
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return render_template('upload.html')
        
        if file and allowed_file(file.filename):
            try:
                # Read the image
                img = Image.open(file)
                original_size = file.tell() / 1024  # Original size in KB
                
                # Get parameters
                width = request.form.get('width', '')
                height = request.form.get('height', '')
                target_size_kb = request.form.get('size', '')
                
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if dimensions provided
                if width and height:
                    try:
                        width = int(width)
                        height = int(height)
                        img = img.resize((width, height), Image.Resampling.LANCZOS)
                    except ValueError:
                        flash('Invalid dimensions provided', 'error')
                        return render_template('upload.html')
                
                # Process image size
                if target_size_kb:
                    try:
                        target_size_kb = float(target_size_kb)
                        img_buffer = process_image(img, target_size_kb)
                    except ValueError:
                        flash('Invalid target size provided', 'error')
                        return render_template('upload.html')
                else:
                    img_buffer = process_image(img, None)
                
                flash(f'Original size: {original_size:.1f}KB', 'info')
                flash(f'New size: {img_buffer.tell()/1024:.1f}KB', 'info')
                
                return send_file(
                    img_buffer,
                    mimetype='image/jpeg',
                    as_attachment=True,
                    download_name=f'processed_{os.path.splitext(file.filename)[0]}.jpg'
                )
            except Exception as e:
                flash(f'Error processing image: {str(e)}', 'error')
                return render_template('upload.html')
            
    return render_template('upload.html')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
