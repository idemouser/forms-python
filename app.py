# app.py

import os
import json
import uuid
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime # Import datetime module

# Initialize the Flask application
app = Flask(__name__)

# --- Configuration ---
# Directory where uploaded files will be stored
UPLOAD_FOLDER = 'uploads'
# File where form responses (metadata) will be stored
RESPONSES_FILE = 'responses.json'

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Ensure the responses JSON file exists and is initialized as an empty list
if not os.path.exists(RESPONSES_FILE):
    with open(RESPONSES_FILE, 'w') as f:
        json.dump([], f)

# --- Helper Functions ---

def load_responses():
    """Loads all existing responses from the JSON file."""
    try:
        with open(RESPONSES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is malformed, return an empty list
        return []

def save_responses(responses):
    """Saves the current list of responses to the JSON file."""
    with open(RESPONSES_FILE, 'w') as f:
        json.dump(responses, f, indent=4)

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles the main form page.
    GET: Displays the form.
    POST: Processes form submission, saves data and file.
    """
    if request.method == 'POST':
        # Generate a unique ID for this response
        response_id = str(uuid.uuid4())

        # Get form data
        question1_answer = request.form.get('question1', '').strip()
        question2_answer = request.form.get('question2', '').strip()
        uploaded_file = request.files.get('file_upload')

        file_path = None
        if uploaded_file and uploaded_file.filename != '':
            # Secure the filename to prevent directory traversal attacks
            filename = secure_filename(uploaded_file.filename)
            # Create a unique filename using the response_id
            unique_filename = f"{response_id}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            uploaded_file.save(file_path)
            print(f"File saved to: {file_path}") # For debugging

        # Prepare the response data to be saved
        response_data = {
            'id': response_id,
            # Use datetime.now() to get the current timestamp reliably
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'question1': question1_answer,
            'question2': question2_answer,
            'uploaded_file': file_path, # Store the path to the saved file
            'original_filename': uploaded_file.filename if uploaded_file else None
        }

        # Load existing responses, add the new one, and save back
        all_responses = load_responses()
        all_responses.append(response_data)
        save_responses(all_responses)

        # Redirect to the responses page after submission
        return redirect(url_for('view_responses'))

    # For GET request, render the form
    return render_template('index.html')

@app.route('/responses')
def view_responses():
    """
    Displays all submitted responses.
    """
    all_responses = load_responses()
    # Pass the UPLOAD_FOLDER to the template to construct file links
    return render_template('responses.html', responses=all_responses, upload_folder=UPLOAD_FOLDER)


@app.route('/clear_responses', methods=['POST'])
def clear_responses():
    """
    Clears all saved responses and uploaded files.
    This route should ideally be accessed via a POST request for security.
    """
    try:
        # 1. Clear the responses.json file
        with open(RESPONSES_FILE, 'w') as f:
            json.dump([], f) # Write an empty list to effectively clear it

        # 2. Delete all files in the UPLOAD_FOLDER
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path) # Remove the file or link
                elif os.path.isdir(file_path):
                    # If there are subdirectories (unlikely for this app, but good practice)
                    # shutil.rmtree(file_path) # Requires 'import shutil'
                    pass # For this simple app, we assume no subdirectories
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
        
        flash('All responses and uploaded files have been cleared!', 'success')
    except Exception as e:
        flash(f'An error occurred while clearing responses: {e}', 'error')
    
    return redirect(url_for('view_responses')) # Redirect back to the responses page


# --- Main Execution ---
if __name__ == '__main__':
    # Run the Flask development server
    # debug=True allows for automatic reloading on code changes and provides a debugger
    app.run(debug=True)
