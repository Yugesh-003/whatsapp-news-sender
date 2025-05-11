from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import re
import subprocess
import threading
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = 'news_sender_secret_key'  # Required for flash messages

# Global variable to track script status
script_status = {
    'running': False,
    'completed': False,
    'error': None
}

@app.route('/', methods=['GET', 'POST'])
def index():
    global script_status
    # Reset script status on new form submission
    script_status = {'running': False, 'completed': False, 'error': None}
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        # Validate phone number (simple validation)
        if not phone or not re.match(r'^\+[0-9]{1,3}[0-9]{6,14}$', phone):
            flash('Please enter a valid phone number with country code (e.g., +919384350120)')
            return redirect(url_for('index'))
        
        # Update the .env file with the new phone number
        try:
            update_env_file(phone)
            flash(f'Thank you, {name}! Your phone number {phone} has been registered successfully.')
            
            # Set script status to running
            script_status['running'] = True
            
            # Run the news_to_audio.py script in a separate thread
            thread = threading.Thread(target=run_news_script)
            thread.daemon = True
            thread.start()
            
            return redirect(url_for('success'))
        except Exception as e:
            flash(f'Error: {str(e)}')
            return redirect(url_for('index'))
    
    return render_template('index.html')

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/check_status')
def check_status():
    """API endpoint to check the status of the news script"""
    return jsonify(script_status)

def update_env_file(phone_number):
    """Update the RECIPIENT_PHONE_NUMBER in the .env file"""
    # Load current .env file
    load_dotenv()
    env_path = os.path.join(os.getcwd(), '.env')
    
    # Read the current content
    with open(env_path, 'r') as file:
        lines = file.readlines()
    
    # Update the RECIPIENT_PHONE_NUMBER line
    updated_lines = []
    for line in lines:
        if line.startswith('RECIPIENT_PHONE_NUMBER='):
            updated_lines.append(f'RECIPIENT_PHONE_NUMBER={phone_number}  # Format: whatsapp:+1234567890\n')
        else:
            updated_lines.append(line)
    
    # Write back to the file
    with open(env_path, 'w') as file:
        file.writelines(updated_lines)

def run_news_script():
    """Run the news_to_audio.py script"""
    global script_status
    try:
        # Get the current directory
        current_dir = os.getcwd()
        script_path = os.path.join(current_dir, 'news_to_audio.py')
        
        # Run the script
        subprocess.run(['python', script_path], check=True)
        
        # Update status when complete
        script_status['running'] = False
        script_status['completed'] = True
    except subprocess.CalledProcessError as e:
        print(f"Error running news_to_audio.py: {e}")
        script_status['running'] = False
        script_status['error'] = str(e)
    except Exception as e:
        print(f"Unexpected error: {e}")
        script_status['running'] = False
        script_status['error'] = str(e)

if __name__ == '__main__':
    app.run(debug=True)