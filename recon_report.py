import os
import re
from datetime import datetime
from pathlib import Path

# --- CONFIGURATION ---
OUTPUT_FILE = "bugbounty_report.html"
# Files to scan for URLs/Subdomains (adjust as needed)
FILES_TO_SCAN = [
    "active_subs.txt", "all_subs.txt", "allsubs.txt", "amass_Domain_results.txt",
    "amass_sub_results.txt", "assetfinder_subs.txt", "clean_subs.txt", "Domain-details.txt",
    "interesting_found.txt", "interestingEXT.txt", "js_files.txt", "live-subs.txt",
    "login_endpoints.txt", "only_ips.txt", "resolved_subs.txt", "reverse_dns.txt",
    "subfinder_subs.txt", "wayback_results.txt"
]

def read_file(filepath):
    """Reads a text file and returns a list of stripped lines."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def categorize_data(items):
    """Categorizes found strings into URLs, Subdomains, IPs, and JS files."""
    categories = {'urls': set(), 'subdomains': set(), 'ips': set(), 'js_files': set(), 'sensitive': set()}
    
    # Simple regexes
    url_pattern = re.compile(r'^https?://')
    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    sub_pattern = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    for item in items:
        if url_pattern.match(item):
            categories['urls'].add(item)
            if item.endswith('.js') or '.js?' in item:
                categories['js_files'].add(item)
            # Flag interesting URLs
            if any(keyword in item.lower() for keyword in ['login', 'admin', 'config', 'api', 'upload', 'debug']):
                categories['sensitive'].add(item)
        elif ip_pattern.match(item):
            categories['ips'].add(item)
        elif sub_pattern.match(item):
            categories['subdomains'].add(item)
    
    # Convert sets back to sorted lists for display
    for key in categories:
        categories[key] = sorted(list(categories[key]))
    return categories

def generate_html(data):
    """Generates an HTML report string."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # CSS Styling
    css = """
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f4f6f8; color: #333; margin: 0; padding: 20px; }
    .container { max-width: 1200px; margin: 0 auto; background: #fff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 30px; }
    h1 { color: #1a202c; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
    h2 { color: #2d3748; margin-top: 30px; border-left: 5px solid #3182ce; padding-left: 10px; }
    h3 { color: #4a5568; margin-bottom: 10px; }
    .meta { color: #718096; font-size: 0.9em; margin-bottom: 20px; }
    .card { background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 15px; margin-bottom: 15px; }
    .card ul { margin: 5px 0; padding-left: 20px; max-height: 300px; overflow-y: auto; }
    .card li { font-family: monospace; font-size: 0.9em; word-break: break-all; margin-bottom: 4px; }
    .badge { display: inline-block; background: #3182ce; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-left: 10px; }
    .checklist { list-style: none; padding-left: 0; }
    .checklist li { margin-bottom: 8px; padding: 10px; background: #edf2f7; border-radius: 4px; border-left: 4px solid #48bb78; }
    .checklist input[type="checkbox"] { margin-right: 10px; }
    .highlight { color: #e53e3e; font-weight: bold; }
    .empty { color: #a0aec0; font-style: italic; }
    """
    
    # Build HTML Body
    html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bug Bounty Recon Report</title>
        <style>{css}</style>
    </head>
    <body>
    <div class="container">
        <h1>🔍 Reconnaissance Report &amp; Manual Testing Guide</h1>
        <div class="meta">Generated on: {now}</div>
        
        <h2>📊 Recon Data Summary</h2>
    """
    
    # Display counts
    html += "<div class='card'><ul style='list-style: none; padding: 0;'>"
    html += f"<li>🌐 Total Subdomains: <strong>{len(data['subdomains'])}</strong></li>"
    html += f"<li>🔗 Total URLs: <strong>{len(data['urls'])}</strong></li>"
    html += f"<li>📜 JS Files: <strong>{len(data['js_files'])}</strong></li>"
    html += f"<li>🔢 IPs: <strong>{len(data['ips'])}</strong></li>"
    html += "</ul></div>"

    # Sensitive Endpoints
    html += "<h3>⚠️ High-Priority / Sensitive URLs</h3><div class='card'>"
    if data['sensitive']:
        html += "<ul>"
        for item in data['sensitive'][:50]:  # Limit display
            html += f"<li>{item}</li>"
        html += "</ul>"
        if len(data['sensitive']) > 50: html += f"<p><em>...and {len(data['sensitive'])-50} more.</em></p>"
    else:
        html += "<p class='empty'>No sensitive URLs found.</p>"
    html += "</div>"

    # JS Files
    html += "<h3>📜 JavaScript Files</h3><div class='card'>"
    if data['js_files']:
        html += "<ul>"
        for item in data['js_files'][:50]:
            html += f"<li>{item}</li>"
        html += "</ul>"
        if len(data['js_files']) > 50: html += f"<p><em>...and {len(data['js_files'])-50} more.</em></p>"
    else:
        html += "<p class='empty'>No JS files found.</p>"
    html += "</div>"

    # --- NEXT STEPS ---
    html += """
        <h2>🛠️ Next Steps: Manual Actions</h2>
        <div class="card">
            <h3>Phase 1: Deep Analysis (Immediate Actions)</h3>
            <ul class="checklist">
                <li><input type="checkbox"> <strong>Analyze JS Files:</strong> Run <code>LinkFinder</code> or <code>SecretFinder</code> on the JS files listed above to extract hidden API endpoints, keys, and tokens.</li>
                <li><input type="checkbox"> <strong>Review Sensitive URLs:</strong> Check URLs containing "login", "admin", "api", or "config". Try accessing them directly and observe the response (200 OK? Redirect?).</li>
                <li><input type="checkbox"> <strong>Parameter Discovery:</strong> Take the top unique URLs and use tools like <code>Arjun</code> or <code>ParamSpider</code> to find hidden GET/POST parameters.</li>
                <li><input type="checkbox"> <strong>Wayback Analysis:</strong> If you haven't yet, sort <code>wayback_results.txt</code> for unique extensions (e.g., .bak, .env, .sql, .xls) and try to download them.</li>
            </ul>
        </div>
        
        <div class="card">
            <h3>Phase 2: Vulnerability Hunting (Manual Testing)</h3>
            <ul class="checklist">
                <li><input type="checkbox"> <strong>IDOR Testing:</strong> For any URL with an ID (e.g., <code>?id=123</code>), try changing the ID to see if you can access other users' data.</li>
                <li><input type="checkbox"> <strong>XSS/SQLi:</strong> Fuzz the sensitive endpoints identified above using payloads. Focus on login forms and search functionality.</li>
                <li><input type="checkbox"> <strong>Subdomain Takeover:</strong> Check the subdomains list for dangling CNAMEs (using <code>subzy</code> or <code>nuclei -t takeovers</code>).</li>
                <li><input type="checkbox"> <strong>API Auth Checks:</strong> Look at the JS extracted endpoints. Can you access them without authentication? Do they leak data?</li>
            </ul>
        </div>
        
        <div class="card">
            <h3>Phase 3: Advanced Checks</h3>
            <ul class="checklist">
                <li><input type="checkbox"> <strong>Login Brute Force/Rate Limiting:</strong> Check if you can perform unlimited login attempts without a CAPTCHA or lockout.</li>
                <li><input type="checkbox"> <strong>CSRF:</strong> Check for anti-CSRF tokens in state-changing requests (password change, email change).</li>
                <li><input type="checkbox"> <strong>Business Logic:</strong> Test the checkout process, coupon codes, or money transfers if applicable.</li>
                <li><input type="checkbox"> <strong>SSL/TLS:</strong> Check <code>testSSL.txt</code> or <code>TLS_nmap.txt</code> for weak ciphers or expired certificates.</li>
            </ul>
        </div>
    </div>
    </body>
    </html>
    """
    return html

def main():
    print("[*] Reading recon files...")
    all_items = []
    for filename in FILES_TO_SCAN:
        items = read_file(filename)
        if items:
            print(f"    - Read {len(items)} lines from {filename}")
            all_items.extend(items)
    
    print(f"[*] Total raw items: {len(all_items)}")
    print("[*] Categorizing data...")
    categorized_data = categorize_data(all_items)
    
    print("[*] Generating HTML report...")
    html_content = generate_html(categorized_data)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[+] Success! Report saved to: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    main()
