import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, Blueprint
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')  # Get from env or use fallback
app.config['BASE_DIRECTORY'] = os.getenv('BASE_DIRECTORY', '/app/shared')  # Get from env or use fallback
app.config['FOLDER_PREFIXES'] = os.getenv('FOLDER_PREFIXES', 'input,output').split(',')  # Get prefixes from env
app.config['URL_PREFIX'] = os.getenv('URL_PREFIX', '/folders')  # Get URL prefix from env or use fallback

# Create a blueprint for all routes with configurable URL prefix
folders_bp = Blueprint('folders', __name__, url_prefix=app.config['URL_PREFIX'])

@folders_bp.route('/')
def index():
    """List folders with specified prefixes or all folders if no prefixes configured"""
    folders = []
    
    if os.path.exists(app.config['BASE_DIRECTORY']):
        for item in os.listdir(app.config['BASE_DIRECTORY']):
            full_path = os.path.join(app.config['BASE_DIRECTORY'], item)
            # If FOLDER_PREFIXES list is empty or only contains empty strings, show all folders
            if os.path.isdir(full_path) and (not app.config['FOLDER_PREFIXES'] or 
                                            app.config['FOLDER_PREFIXES'] == [''] or
                                            any(item.startswith(prefix) for prefix in app.config['FOLDER_PREFIXES'] if prefix)):
                folders.append(item)
    
    return render_template('index.html', folders=folders)

@folders_bp.route('/folder/<folder_name>')
def show_folder(folder_name):
    """Show contents of a specific folder"""
    # Security check to prevent directory traversal attacks
    if app.config['FOLDER_PREFIXES'] and app.config['FOLDER_PREFIXES'] != [''] and not any(folder_name.startswith(prefix) for prefix in app.config['FOLDER_PREFIXES'] if prefix):
        flash('Access denied', 'danger')
        return redirect(url_for('folders.index'))
    
    folder_path = os.path.join(app.config['BASE_DIRECTORY'], folder_name)
    
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        flash(f'Folder {folder_name} not found', 'danger')
        return redirect(url_for('folders.index'))
    
    files = os.listdir(folder_path)
    return render_template('folder.html', folder_name=folder_name, files=files)

@folders_bp.route('/upload/<folder_name>', methods=['POST'])
def upload_file(folder_name):
    """Upload a file to a specific folder"""
    # Security check to prevent directory traversal attacks
    if app.config['FOLDER_PREFIXES'] and app.config['FOLDER_PREFIXES'] != [''] and not any(folder_name.startswith(prefix) for prefix in app.config['FOLDER_PREFIXES'] if prefix):
        flash('Access denied', 'danger')
        return redirect(url_for('folders.index'))
    
    folder_path = os.path.join(app.config['BASE_DIRECTORY'], folder_name)
    
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        flash(f'Folder {folder_name} not found', 'danger')
        return redirect(url_for('folders.index'))
    
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('folders.show_folder', folder_name=folder_name))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('folders.show_folder', folder_name=folder_name))
    
    filename = secure_filename(file.filename)
    file.save(os.path.join(folder_path, filename))
    flash(f'File {filename} uploaded successfully', 'success')
    return redirect(url_for('folders.show_folder', folder_name=folder_name))

@folders_bp.route('/download/<folder_name>/<filename>')
def download_file(folder_name, filename):
    """Download a file from a specific folder"""
    # Security check to prevent directory traversal attacks
    if app.config['FOLDER_PREFIXES'] and app.config['FOLDER_PREFIXES'] != [''] and not any(folder_name.startswith(prefix) for prefix in app.config['FOLDER_PREFIXES'] if prefix):
        flash('Access denied', 'danger')
        return redirect(url_for('folders.index'))
    
    folder_path = os.path.join(app.config['BASE_DIRECTORY'], folder_name)
    return send_from_directory(folder_path, filename)

# Register the blueprint with the app
app.register_blueprint(folders_bp)

# Add a root redirect to /folders
@app.route('/')
def root_redirect():
    return redirect(url_for('folders.index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 