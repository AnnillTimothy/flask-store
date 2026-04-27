"""
File upload utilities for managing product images and experience media.
"""
import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'ogg', 'wav', 'm4a'}


def _allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def _ensure_dir(directory):
    os.makedirs(directory, exist_ok=True)


def save_uploaded_file(file_storage, subfolder, allowed_extensions=None):
    """
    Save an uploaded file to the uploads directory under the given subfolder.
    Returns the saved filename, or None if the file is invalid.
    """
    if not file_storage or not file_storage.filename:
        return None

    if allowed_extensions is None:
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS

    if not _allowed_file(file_storage.filename, allowed_extensions):
        return None

    original = secure_filename(file_storage.filename)
    ext = original.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    _ensure_dir(upload_dir)

    filepath = os.path.join(upload_dir, unique_name)
    file_storage.save(filepath)
    return unique_name


def delete_uploaded_file(filename, subfolder):
    """Delete an uploaded file from the given subfolder."""
    if not filename:
        return
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
