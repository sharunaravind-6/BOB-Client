import webview  # type: ignore
import threading
import os
from tkinter import filedialog
from client.api.server import app # Import our Flask app

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

def run_server():
    """Runs the Flask server."""
    # We don't want the Flask dev server's debug messages in the console
    # as PyWebView will provide its own.
    app.run(debug=False, port=5000)

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
        'http://127.0.0.1:5000', # The URL of our Flask app
        js_api=api, # Expose the Api class to JavaScript
        width=1400,
        height=800
    )
    # This debug=True flag enables the right-click "Inspect" menu
    webview.start(debug=True)