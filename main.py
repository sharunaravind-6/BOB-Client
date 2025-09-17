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
        """Zips the contents of the bot's directory and returns it as a base64 string."""
        if not bot_file_path or "No file selected" in bot_file_path:
            return {"error": "No bot file selected."}

        bot_directory = os.path.dirname(bot_file_path)

        # Create an in-memory zip file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(bot_directory):
                for file in files:
                    # Create a clean path inside the zip file
                    file_path = os.path.join(root, file)
                    archive_name = os.path.relpath(file_path, bot_directory)
                    zipf.write(file_path, archive_name)

        # Go back to the start of the buffer and encode it
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