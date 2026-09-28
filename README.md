# Generates-an-HTML-report
### How this script works:
1. **Scans the Directory:** It looks through your `clearme.com` folder and its subfolders.
2. **Reads Files:** It categorizes files by their extension and reads `.txt` files to extract findings (like subdomains, URLs, endpoints).
3. **Smart Filtering:** It ignores massive files (over 50MB) to prevent crashing your computer, but still notes their existence.
4. **Firefox Integration:** It creates clickable links in the HTML report. When you click a link (or a file path), it is configured to open directly in Firefox.
5. **Generates Report:** It creates a clean, dark-themed `Bug_Bounty_Report.html` in your current folder.

### Prerequisites
You need Python installed. You don't need any external libraries (it uses standard built-in modules).

### The Python Script (`generate_report.py`)
### How to use it

1.  Open your terminal.
2.  Navigate to your folder:
    ```bash
    cd /home/hunter69/Desktop/Bug-Hunting/clearme.com/
    ```
3.  Create the script file (you can use `nano` or any text editor):
    ```bash
    nano generate_report.py
    ```
4.  Paste the code above, then press `Ctrl+O` to save and `Ctrl+X` to exit.
5.  Run the script:
    ```bash
    python3 generate_report.py
    ```

### What happens next?
* The script will scan all your files (like `active_subs.txt`, `js_files.txt`, etc.).
* It will create a file called `Bug_Bounty_Report.html`.
* It will automatically attempt to launch **Firefox** and open the report.
* **In the report:**
    * You will see a summary of how many files and lines of data you have.
    * Files are grouped by folder (Root, `assets`, `js_scan_results`, etc.).
    * Click on any file name to expand it and read the contents directly in the browser.
    * Any URLs found inside the text files (like in `wayback_urls.txt` or `live-subs.txt`) are automatically converted into clickable links. Clicking them will open a new tab in Firefox.

### A Note on "Opening URLs in Firefox"
Web browsers have security restrictions. A local HTML file cannot forcefully launch a specific external application (like forcing Firefox) without user interaction. However, this script sets Firefox as the default handler for the report launch and formats all URLs as standard web links. When you click a link in the report, your system will use Firefox to open it.
