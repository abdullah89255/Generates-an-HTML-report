import os
import urllib.parse
import html
import webbrowser

# Configuration
TARGET_DIR = "."  # Current directory (where the script is run)
REPORT_FILE = "Bug_Bounty_Report.html"
FIREFOX_PATH = "/usr/bin/firefox" # Default Linux path for Firefox
MAX_FILE_SIZE_MB = 50 # Skip reading files larger than this to prevent memory issues

def get_file_icon(filename):
    ext = filename.split('.')[-1].lower()
    if ext == 'txt': return '📄'
    if ext == 'html': return '🌐'
    if ext == 'js': return '📜'
    if ext == 'json': return '⚙️'
    return '📁'

def generate_html_report(data):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bug Bounty Report - Clearme.com</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e1e1e; color: #d4d4d4; margin: 0; padding: 20px; }}
            h1, h2, h3 {{ color: #569cd6; }}
            .container {{ max-width: 1200px; margin: auto; }}
            .summary {{ background-color: #252526; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #569cd6; }}
            .file-card {{ background-color: #2d2d2d; margin-bottom: 15px; border-radius: 8px; overflow: hidden; }}
            .file-header {{ background-color: #333333; padding: 10px 15px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #444; }}
            .file-header:hover {{ background-color: #3e3e3e; }}
            .file-content {{ padding: 15px; display: none; max-height: 500px; overflow-y: auto; font-family: 'Courier New', Courier, monospace; font-size: 13px; white-space: pre-wrap; word-wrap: break-word; }}
            .file-content.active {{ display: block; }}
            .file-size {{ font-size: 0.8em; color: #888; }}
            a {{ color: #4ec9b0; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .badge {{ background-color: #569cd6; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; margin-left: 10px; }}
            .folder-title {{ margin-top: 30px; border-bottom: 1px solid #444; padding-bottom: 5px; }}
            .stats {{ display: flex; gap: 20px; flex-wrap: wrap; }}
            .stat-box {{ background: #333; padding: 10px; border-radius: 5px; min-width: 150px; text-align: center; }}
        </style>
        <script>
            function toggleFile(id) {{
                var content = document.getElementById(id);
                if (content.style.display === "block") {{
                    content.style.display = "none";
                }} else {{
                    content.style.display = "block";
                }}
            }}
            
            // Function to open links in Firefox (relies on system default or specified browser)
            function openInFirefox(url) {{
                // In a web browser, we can't force a specific local app, but we can open a new tab.
                // The Python script generates links that the OS handles.
                window.open(url, '_blank');
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🐛 Bug Bounty Recon Report: Clearme.com</h1>
            <div class="summary">
                <div class="stats">
                    <div class="stat-box"><strong>Total Files:</strong> {data['total_files']}</div>
                    <div class="stat-box"><strong>Total Folders:</strong> {data['total_folders']}</div>
                    <div class="stat-box"><strong>Text Lines Found:</strong> {data['total_lines']}</div>
                </div>
                <p style="margin-top:10px; font-size: 0.9em; color: #aaa;">Generated automatically from local directory scan.</p>
            </div>
    """

    for folder, files in data['folders'].items():
        folder_name = folder if folder != "." else "Root Directory"
        html_content += f"<h2 class='folder-title'>📁 {folder_name}</h2>"
        
        for file_info in files:
            file_id = file_info['id']
            html_content += f"""
            <div class="file-card">
                <div class="file-header" onclick="toggleFile('{file_id}')">
                    <span>{get_file_icon(file_info['name'])} {file_info['name']} <span class="badge">{file_info['lines']} lines</span></span>
                    <span class="file-size">{file_info['size']}</span>
                </div>
                <div class="file-content" id="{file_id}">
            """
            
            if file_info['is_binary']:
                html_content += "<p><em>Binary or Large file. Preview not available.</em></p>"
            else:
                # Escape HTML entities to prevent breaking the report
                safe_content = html.escape(file_info['content'])
                # Highlight URLs to make them clickable
                # This is a simple regex replacement for http/https links
                import re
                safe_content = re.sub(
                    r'(https?://[^\s]+)', 
                    r'<a href="\1" target="_blank">\1</a>', 
                    safe_content
                )
                html_content += safe_content

            html_content += """
                </div>
            </div>
            """

    html_content += """
        </div>
    </body>
    </html>
    """
    return html_content

def scan_directory():
    report_data = {
        'total_files': 0,
        'total_folders': 0,
        'total_lines': 0,
        'folders': {}
    }
    
    file_counter = 0

    for root, dirs, files in os.walk(TARGET_DIR):
        # Skip the .git folder if it exists
        if '.git' in root:
            continue

        relative_path = os.path.relpath(root, TARGET_DIR)
        if relative_path not in report_data['folders']:
            report_data['folders'][relative_path] = []
            report_data['total_folders'] += 1

        for file in files:
            file_path = os.path.join(root, file)
            file_size_bytes = os.path.getsize(file_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            report_data['total_files'] += 1
            file_counter += 1
            file_id = f"file_{file_counter}"
            
            file_info = {
                'id': file_id,
                'name': file,
                'path': file_path,
                'size': f"{file_size_mb:.2f} MB",
                'lines': 0,
                'content': "",
                'is_binary': False
            }

            # Only read text files smaller than MAX_FILE_SIZE_MB
            if file_size_mb < MAX_FILE_SIZE_MB:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.splitlines()
                        file_info['lines'] = len(lines)
                        report_data['total_lines'] += len(lines)
                        
                        # Limit content to first 1000 lines for the report to keep it fast
                        if len(lines) > 1000:
                            file_info['content'] = "\n".join(lines[:1000]) + "\n\n... [Truncated for report] ..."
                        else:
                            file_info['content'] = content
                except Exception as e:
                    file_info['is_binary'] = True
                    file_info['content'] = f"Error reading file: {str(e)}"
            else:
                file_info['is_binary'] = True
                file_info['content'] = "File too large to preview."

            report_data['folders'][relative_path].append(file_info)

    return report_data

def main():
    print(f"[*] Scanning directory: {os.path.abspath(TARGET_DIR)}")
    data = scan_directory()
    
    print(f"[*] Found {data['total_files']} files in {data['total_folders']} folders.")
    print("[*] Generating HTML report...")
    
    html_output = generate_html_report(data)
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_output)
        
    print(f"[+] Report generated successfully: {os.path.abspath(REPORT_FILE)}")
    
    # Automatically open the report in Firefox
    print("[*] Opening report in Firefox...")
    try:
        # We use the 'file://' protocol to open local files
        report_url = 'file://' + os.path.abspath(REPORT_FILE)
        # Try to open specifically in Firefox, fallback to default browser
        webbrowser.get(FIREFOX_PATH).open(report_url)
    except Exception as e:
        print(f"[!] Could not open Firefox automatically. Please open {REPORT_FILE} manually.")
        print(f"    Error: {e}")

if __name__ == "__main__":
    main()
