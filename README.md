# DigiNotes

<img src="./images/app_icon.png" alt="DigiNotes" width="200" height="200" align="right"/>

A lightweight, glassmorphic digital sticky notes manager built using PySide6 (Qt for Python). 


---

I rarely want to get up and grab a pen and paper just to jot down passwords, quick details to be filled into a form later, or temporary tasks. Also, it is better to have things to do noted in front of you at time. So, I needed something simple to note stuff down while having full use of my screen. I kept seeing people use physical sticky notes plastered around their monitors, and it got me thinking to make this.

As I was finishing up **CS50x**, I decided to work on this.

---

### Features:

* Translucent, rounded-corner sticky note windows with customizable color themes and drop-shadow effects.
* Live Markdown formatting for headers, bold, italics, underlines, highlights, inline code, and LaTeX math blocks.
* Interactive checklists (`- [ ]`) that you can toggle by clicking directly on the checkbox.
* **Auto-Continuation of Lists**:
  * Pressing `Enter` on bullet lists, numbered lists, or checklists automatically spawns the next element (auto-incrementing numbers or resetting checkbox states).
  * Pressing `Enter` on an empty list prefix automatically clears the line and escapes the list.
  * Pressing `Shift+Enter` bypasses continuation to insert a normal newline.
* **Window & Space Management**:
  * Keeps notes above other windows (runs via X11/XCB wrapper on Linux to bypass compositor restrictions).
  * Click the title bar dot to collapse the entire note window into a tiny, unobtrusive colored indicator, then click again to expand it back.
  * Pin notes in place to prevent accidental moves or collapses.
* A standalone dashboard to search notes, create new ones, manage active/inactive states.
* Supports running silently in the system tray. Includes cross-platform autostart settings (Windows registry, macOS plist, Linux desktop autostart) to launch tray-only via the `--startup` flag.
* All notes are saved locally as standard `.md` files accompanied by `.meta` JSON files for window coordinates and state configuration.

---

### Tech Stack & Architecture

* **Framework**: PySide6 (Qt for Python)
* **Highlighter**: Custom `QSyntaxHighlighter` parsing regex patterns for live Markdown styling.
* **Process Lock**: `QLockFile` implementation ensuring single-instance execution per user.
* **Launcher Wrapper**: Auto-virtualenv check and platform platform adjustments in `run.sh` / `run.bat`.

---

### Setup & Run

To run DigiNotes locally, ensure you have Python 3 installed, then run the launcher:

**On Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

**On Windows:**
```cmd
run.bat
```

The script automatically configures a virtual environment, installs PySide6, and starts the manager in the system tray.
