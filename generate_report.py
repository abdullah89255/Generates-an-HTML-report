import os
import re
import html
import webbrowser
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TARGET_DIR = "."                      # Directory to scan (relative to CWD)
REPORT_FILE = "Bug_Bounty_Report.html"
MAX_FILE_SIZE_MB = 50                 # Skip reading files larger than this
MAX_PREVIEW_LINES = 1000              # Truncate previews longer than this
SKIP_DIRS = {".git"}                  # Directory names to skip entirely

ICONS = {
    "txt": "📄", "md": "📝", "log": "🧾",
    "html": "🌐", "htm": "🌐", "xml": "📰",
    "js": "📜", "mjs": "📜", "ts": "📜", "py": "🐍",
    "json": "⚙️", "yml": "🧩", "yaml": "🧩", "toml": "🧩", "ini": "🧩",
    "css": "🎨", "scss": "🎨",
    "csv": "📊", "sql": "🗄️", "sh": "⌨️", "bat": "⌨️",
    "png": "🖼️", "jpg": "🖼️", "jpeg": "🖼️", "gif": "🖼️", "svg": "🖼️",
    "zip": "📦", "gz": "📦", "tar": "📦", "rar": "📦", "pdf": "📕",
}


def get_file_icon(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ICONS.get(ext, "📁")


def human_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num_bytes < 1024 or unit == "TB":
            return f"{num_bytes:.0f} {unit}" if unit == "B" else f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"


# ---------------------------------------------------------------------------
# Static HTML shell (plain string -> no f-string brace escaping headaches)
# ---------------------------------------------------------------------------
HTML_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bug Bounty Recon Report</title>
<style>
  :root{
    --bg:#0d1017;
    --panel:#151b26;
    --panel-2:#121826;
    --border:#202939;
    --text:#dbe2ee;
    --muted:#8593a8;
    --accent:#5b9dff;
    --accent-2:#41d1a7;
    --warn:#ffb454;
  }
  *{box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{
    margin:0;
    font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    font-size:15px;
    line-height:1.55;
    color:var(--text);
    background-color:var(--bg);
    background-image:
      radial-gradient(1100px 520px at 8% -12%, rgba(38,72,140,.42), transparent 60%),
      radial-gradient(900px 480px at 102% -6%, rgba(20,110,96,.32), transparent 58%);
    background-attachment:fixed;
    -webkit-font-smoothing:antialiased;
    padding-bottom:60px;
  }
  code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9em;color:#8ab4ff;}

  /* ---------- top bar ---------- */
  .topbar{
    position:sticky; top:0; z-index:50;
    background:rgba(13,16,23,.82);
    backdrop-filter:blur(12px);
    -webkit-backdrop-filter:blur(12px);
    border-bottom:1px solid var(--border);
    padding:12px 20px;
  }
  .topbar-inner{
    max-width:1150px; margin:0 auto;
    display:flex; align-items:center; gap:12px; flex-wrap:wrap;
  }
  .brand{
    display:flex; align-items:center; gap:9px;
    font-weight:700; letter-spacing:.2px; color:#eaf0fb; white-space:nowrap;
  }
  .brand .dot{
    width:9px; height:9px; border-radius:50%;
    background:var(--accent-2); box-shadow:0 0 12px var(--accent-2);
  }
  .search{position:relative; flex:1 1 240px; min-width:180px;}
  .search::before{
    content:"⌕"; position:absolute; left:13px; top:50%;
    transform:translateY(-50%); font-size:16px; color:#5f6d84; pointer-events:none;
  }
  .search input{
    width:100%; padding:9px 14px 9px 34px;
    border-radius:10px; border:1px solid #232c3b;
    background:var(--panel-2); color:var(--text); font-size:14px; outline:none;
    transition:border-color .15s, box-shadow .15s;
  }
  .search input::placeholder{color:#5f6d84;}
  .search input:focus{border-color:var(--accent); box-shadow:0 0 0 3px rgba(91,157,255,.15);}
  .btn{
    padding:9px 13px; border-radius:10px; border:1px solid #232c3b;
    background:var(--panel-2); color:#9fb0c7; font-size:13px; font-weight:600;
    cursor:pointer; white-space:nowrap;
    transition:background .15s, color .15s, border-color .15s;
  }
  .btn:hover{background:#1a2233; color:var(--text); border-color:#2e3a4d;}
  .btn:active{transform:translateY(1px);}

  /* ---------- layout ---------- */
  .wrap{max-width:1150px; margin:0 auto; padding:34px 20px 40px;}
  .hero{margin-bottom:6px;}
  h1{
    margin:0 0 8px;
    font-size:clamp(22px, 3.2vw, 32px);
    letter-spacing:-.6px; line-height:1.2;
    background:linear-gradient(90deg,#8ab4ff,#41d1a7 55%,#8ab4ff);
    -webkit-background-clip:text; background-clip:text; color:transparent;
  }
  .sub{margin:0; color:var(--muted); font-size:13.5px;}

  /* ---------- stats ---------- */
  .stats{
    display:grid; grid-template-columns:repeat(auto-fit, minmax(165px, 1fr));
    gap:14px; margin:26px 0 36px;
  }
  .stat{
    position:relative; overflow:hidden;
    background:linear-gradient(180deg,#161c28,#121722);
    border:1px solid var(--border); border-radius:14px;
    padding:16px 18px;
  }
  .stat::after{
    content:""; position:absolute; top:0; bottom:0; left:0;
    width:3px; background:var(--c, var(--accent));
  }
  .stat .v{font-size:25px; font-weight:700; color:#eaf0fb; line-height:1.15;}
  .stat .l{
    margin-top:3px; font-size:11px; letter-spacing:.09em;
    text-transform:uppercase; color:#7b8aa3;
  }

  /* ---------- folders ---------- */
  .folder{margin-bottom:22px;}
  .folder-head{
    display:flex; align-items:center; gap:10px;
    padding:11px 15px; border-radius:12px; cursor:pointer; user-select:none;
    background:#141a25; border:1px solid var(--border);
    transition:background .15s, border-color .15s;
  }
  .folder-head:hover{background:#182030; border-color:#2b374a;}
  .folder-head .chev{
    font-size:11px; color:#7b8aa3; transition:transform .2s ease;
  }
  .folder.closed .chev{transform:rotate(-90deg);}
  .folder-head .fname{font-weight:650; color:#cfd9ea; word-break:break-all;}
  .folder-head .fcount{
    margin-left:auto; font-size:11px; font-weight:600; color:#7b8aa3;
    background:#1d2534; border:1px solid #26303f;
    padding:2px 9px; border-radius:999px; white-space:nowrap;
  }
  .folder-body{
    margin-top:10px; display:flex; flex-direction:column; gap:10px;
  }
  .folder.closed .folder-body{display:none;}

  /* ---------- file cards ---------- */
  .file{
    background:var(--panel); border:1px solid var(--border); border-radius:12px;
    overflow:hidden;
    transition:border-color .15s, box-shadow .15s;
  }
  .file:hover{border-color:#2f3c52; box-shadow:0 6px 22px rgba(0,0,0,.28);}
  .file-head{
    display:flex; align-items:center; justify-content:space-between; gap:14px;
    padding:11px 15px; cursor:pointer; user-select:none;
  }
  .file-name{
    display:flex; align-items:center; gap:9px;
    font-weight:600; color:#cfd9ea; word-break:break-all; min-width:0;
  }
  .file-name .ico{flex-shrink:0;}
  .file-meta{display:flex; align-items:center; gap:10px; flex-shrink:0;}
  .badge{
    font-size:11px; font-weight:600; padding:2px 8px; border-radius:999px;
    background:rgba(91,157,255,.12); color:#8ab4ff;
    border:1px solid rgba(91,157,255,.25); white-space:nowrap;
  }
  .size{font-size:11.5px; color:#6f7d94; font-variant-numeric:tabular-nums;}
  .file-body{display:none; border-top:1px solid var(--border); background:#0f141d;}
  .file.open .file-body{display:block;}
  pre.code{
    margin:0; padding:16px 18px; max-height:520px; overflow:auto;
    font-family:ui-monospace,SFMono-Regular,"JetBrains Mono",Menlo,Consolas,monospace;
    font-size:12.6px; line-height:1.62; color:#c3cddd;
    white-space:pre-wrap; word-break:break-word;
  }
  pre.code a{
    color:#5eead4; text-decoration:none;
    border-bottom:1px dotted rgba(94,234,212,.45);
  }
  pre.code a:hover{color:#8ab4ff; border-bottom-color:#8ab4ff;}
  .trunc{color:var(--warn); font-style:italic;}
  .binary-note{color:#7b8aa3; font-style:italic;}

  /* ---------- scrollbars ---------- */
  pre.code::-webkit-scrollbar{width:10px; height:10px;}
  pre.code::-webkit-scrollbar-track{background:#0f141d;}
  pre.code::-webkit-scrollbar-thumb{background:#2a3547; border-radius:8px;}
  pre.code::-webkit-scrollbar-thumb:hover{background:#374560;}

  /* ---------- misc ---------- */
  .empty{
    display:none; text-align:center; color:#6f7d94;
    padding:46px 20px; font-size:14px;
    border:1px dashed #26303f; border-radius:14px; margin-top:10px;
  }
  .foot{
    margin-top:56px; padding-top:18px; border-top:1px solid var(--border);
    text-align:center; color:#5c6a80; font-size:12.5px;
  }
  @media (max-width:560px){
    .file-meta .size{display:none;}
    .topbar-inner{gap:8px;}
  }
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-inner">
    <div class="brand"><span class="dot"></span> Recon Report</div>
    <div class="search">
      <input id="search" type="text" placeholder="Filter files by name…" autocomplete="off" spellcheck="false">
    </div>
    <button class="btn" id="expand-all">Expand folders</button>
    <button class="btn" id="collapse-all">Collapse folders</button>
  </div>
</div>

<div class="wrap">
"""

HTML_FOOT = """
  <div class="empty" id="no-results">No files match your filter.</div>

  <div class="foot">
    Generated locally &middot; <span id="gen-time"></span>
  </div>
</div>

<script>
(function () {
  const searchInput = document.getElementById('search');
  const noResults   = document.getElementById('no-results');
  const counter     = document.getElementById('visible-count');
  const allFolders  = () => document.querySelectorAll('.folder');

  /* --- expand / collapse a file or folder ------------------------------- */
  document.addEventListener('click', function (e) {
    const fileHead = e.target.closest('.file-head');
    if (fileHead) { fileHead.parentElement.classList.toggle('open'); return; }

    const folderHead = e.target.closest('.folder-head');
    if (folderHead) { folderHead.parentElement.classList.toggle('closed'); }
  });

  /* --- expand / collapse all -------------------------------------------- */
  document.getElementById('expand-all').addEventListener('click', function () {
    allFolders().forEach(f => f.classList.remove('closed'));
  });
  document.getElementById('collapse-all').addEventListener('click', function () {
    allFolders().forEach(f => f.classList.add('closed'));
  });

  /* --- live filter ------------------------------------------------------- */
  function applyFilter() {
    const q = searchInput.value.trim().toLowerCase();
    let visible = 0;

    allFolders().forEach(function (folder) {
      let folderVisible = 0;

      folder.querySelectorAll('.file').forEach(function (file) {
        const match = !q || file.dataset.name.indexOf(q) !== -1;
        file.style.display = match ? '' : 'none';
        if (match) folderVisible++;
      });

      folder.style.display = folderVisible ? '' : 'none';
      if (q && folderVisible) folder.classList.remove('closed');
      visible += folderVisible;
    });

    counter.textContent = visible;
    noResults.style.display = visible ? 'none' : 'block';
  }

  searchInput.addEventListener('input', applyFilter);

  /* --- timestamp --------------------------------------------------------- */
  document.getElementById('gen-time').textContent = new Date().toLocaleString();
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------
def generate_html_report(data: dict) -> str:
    parts = [HTML_HEAD]

    # --- hero + stats ------------------------------------------------------
    parts.append(f"""
  <div class="hero">
    <h1>🐛 Bug Bounty Recon Report</h1>
    <p class="sub">
      Scanned <code>{html.escape(data['scan_root'])}</code> &middot;
      showing <span id="visible-count">{data['total_files']}</span> of {data['total_files']} files
    </p>
  </div>

  <div class="stats">
    <div class="stat" style="--c:#5b9dff">
      <div class="v">{data['total_files']}</div><div class="l">Files</div>
    </div>
    <div class="stat" style="--c:#41d1a7">
      <div class="v">{data['total_folders']}</div><div class="l">Folders</div>
    </div>
    <div class="stat" style="--c:#ffb454">
      <div class="v">{data['total_lines']:,}</div><div class="l">Lines of text</div>
    </div>
    <div class="stat" style="--c:#c084fc">
      <div class="v">{human_size(data['total_bytes'])}</div><div class="l">Total size</div>
    </div>
  </div>
""")

    # --- folders -----------------------------------------------------------
    for folder in sorted(data["folders"], key=lambda p: (p != ".", p)):
        files = data["folders"][folder]
        label = "Root Directory" if folder == "." else folder
        folder_label = html.escape(label)

        parts.append(f"""
  <section class="folder">
    <div class="folder-head">
      <span class="chev">▼</span>
      <span class="fname">📂 {folder_label}</span>
      <span class="fcount">{len(files)} file{'s' if len(files) != 1 else ''}</span>
    </div>
    <div class="folder-body">
""")

        for fi in files:
            name_attr = html.escape(f"{fi['name']} {fi['path']}".lower(), quote=True)
            icon = get_file_icon(fi["name"])

            if fi["is_binary"]:
                body = f'<pre class="code"><span class="binary-note">{html.escape(fi["content"])}</span></pre>'
            else:
                safe = html.escape(fi["content"])
                # Turn bare URLs into clickable links
                safe = re.sub(
                    r'(https?://[^\s<>"\']+)',
                    r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>',
                    safe,
                )
                if fi["truncated"]:
                    safe += '\n\n<span class="trunc">— preview truncated —</span>'
                body = f'<pre class="code">{safe}</pre>'

            parts.append(f"""
      <article class="file" data-name="{name_attr}">
        <div class="file-head">
          <div class="file-name"><span class="ico">{icon}</span>{html.escape(fi['name'])}</div>
          <div class="file-meta">
            <span class="badge">{fi['lines']:,} lines</span>
            <span class="size">{fi['size']}</span>
          </div>
        </div>
        <div class="file-body">{body}</div>
      </article>
""")

        parts.append("    </div>\n  </section>\n")

    parts.append(HTML_FOOT)
    return "".join(parts)


# ---------------------------------------------------------------------------
# Directory scanning
# ---------------------------------------------------------------------------
def scan_directory() -> dict:
    data = {
        "scan_root": os.path.abspath(TARGET_DIR),
        "total_files": 0,
        "total_folders": 0,
        "total_lines": 0,
        "total_bytes": 0,
        "folders": {},
    }

    report_abs = os.path.abspath(REPORT_FILE)
    file_counter = 0
    size_limit = MAX_FILE_SIZE_MB * 1024 * 1024

    for root, dirs, files in os.walk(TARGET_DIR):
        # Prune unwanted directories in-place so os.walk won't descend
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        rel = os.path.relpath(root, TARGET_DIR)
        if rel not in data["folders"]:
            data["folders"][rel] = []

        for file in files:
            file_path = os.path.join(root, file)

            # Never include the report inside itself
            if os.path.abspath(file_path) == report_abs:
                continue

            try:
                size_bytes = os.path.getsize(file_path)
            except OSError:
                continue

            file_counter += 1
            data["total_files"] += 1
            data["total_bytes"] += size_bytes

            info = {
                "id": f"file_{file_counter}",
                "name": file,
                "path": file_path,
                "size": human_size(size_bytes),
                "lines": 0,
                "content": "",
                "is_binary": False,
                "truncated": False,
            }

            if size_bytes > size_limit:
                info["is_binary"] = True
                info["content"] = f"File too large to preview ({human_size(size_bytes)})."
            else:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()

                    # Treat NUL bytes as a strong binary signal
                    if "\x00" in content:
                        raise ValueError("binary content")

                    lines = content.splitlines()
                    info["lines"] = len(lines)
                    data["total_lines"] += len(lines)

                    if len(lines) > MAX_PREVIEW_LINES:
                        info["content"] = "\n".join(lines[:MAX_PREVIEW_LINES])
                        info["truncated"] = True
                    else:
                        info["content"] = content

                except Exception as exc:
                    info["is_binary"] = True
                    info["content"] = f"Binary file or unreadable — preview not available. ({exc})"

            data["folders"][rel].append(info)

    # Drop folders that ended up empty and recount
    data["folders"] = {k: v for k, v in data["folders"].items() if v}
    data["total_folders"] = len(data["folders"])

    return data


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"[*] Scanning directory: {os.path.abspath(TARGET_DIR)}")
    data = scan_directory()

    print(f"[*] Found {data['total_files']} files in {data['total_folders']} folders.")
    print(f"[*] Total text lines: {data['total_lines']:,}  |  Total size: {human_size(data['total_bytes'])}")
    print("[*] Generating HTML report...")

    html_output = generate_html_report(data)

    with open(REPORT_FILE, "w", encoding="utf-8") as fh:
        fh.write(html_output)

    report_uri = Path(REPORT_FILE).resolve().as_uri()
    print(f"[+] Report generated: {report_uri}")

    print("[*] Opening report in your default browser...")
    try:
        opened = webbrowser.open(report_uri)
        if not opened:
            print(f"[!] Could not open a browser automatically. Open this file manually:\n    {report_uri}")
    except Exception as exc:
        print(f"[!] Could not open a browser automatically ({exc}).")
        print(f"    Open this file manually: {report_uri}")


if __name__ == "__main__":
    main()
