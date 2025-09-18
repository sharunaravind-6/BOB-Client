import io
import webview  # type: ignore
import threading
import os
from tkinter import filedialog
from client.api.server import app # Import our Flask app
import zipfile
import base64

# This class will hold functions we want to expose to JavaScript
class Api:
    def select_folder(self):
        """
        Opens a native OS dialog to select a folder.
        """
        # We hide the root Tkinter window
        root = filedialog.Tk()
        root.withdraw()
        # The actual dialog
        folder_path = filedialog.askdirectory(initialdir=os.getcwd())
        root.destroy()
        return folder_path
    
    def select_file(self): # Renamed function
        root = filedialog.Tk()
        root.withdraw()
        # Changed to askopenfilename
        file_path = filedialog.askopenfilename(initialdir=os.getcwd())
        root.destroy()
        return file_path
    # Add this function inside the Api class in main.py
    def create_bot_zip(self, bot_file_path):
        """
        Zips the bot's directory and intelligently adds the correct, standardized
        run.sh script for submission.
        """
        if not bot_file_path or "No file selected" in bot_file_path:
            return {"error": "No bot file selected."}

        bot_directory = os.path.dirname(bot_file_path)
        bot_filename = os.path.basename(bot_file_path)

        # 1. Determine the language and find the correct script template
        _, extension = os.path.splitext(bot_filename)
        script_map = {".py": "scripts/python.sh", ".java": "scripts/java.sh", ".c": "scripts/c.sh",".js": "scripts/javascript.sh",".cpp": "scripts/cpp.sh"}
        script_path = script_map.get(extension)

        if not script_path:
            return {"error": f"Cannot create run script for unsupported file type: {extension}"}

        try:
            # 2. Read the content of our standard script template
            with open(script_path, 'r') as f:
                script_content = f.read()
            
            # This line replaces the placeholder '$1' in the script with the actual filename
            final_script_content = script_content.replace('"$1"', f'"{bot_filename}"')

        except FileNotFoundError:
            return {"error": f"Standard script not found at: {script_path}"}

        # 3. Create an in-memory zip file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # --- NEW LOGIC: Add only the single selected file ---
            archive_name = os.path.basename(bot_file_path)
            zipf.write(bot_file_path, archive_name)
            # Add the dynamically generated run.sh script
            zipf.writestr('run.sh', final_script_content)


        # 6. Encode and return the zip file
        zip_buffer.seek(0)
        base64_zip = base64.b64encode(zip_buffer.read()).decode('utf-8')
        
        return {"zip_data": base64_zip}

def run_server():
    """Runs the Flask server."""
    # We don't want the Flask dev server's debug messages in the console
    # as PyWebView will provide its own.
    app.run(debug=False, port=5001)

if __name__ == '__main__':
    # Create an instance of our API class
    api = Api()

    # Start the Flask server in a separate, daemonized thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # Create and start the PyWebView window
    webview.create_window(
        'Big-O-Battle Client',
        'http://127.0.0.1:5001', # The URL of our Flask app
        js_api=api, # Expose the Api class to JavaScript
        width=1400,
        height=800
    )
    # This debug=True flag enables the right-click "Inspect" menu
    webview.start(debug=True)