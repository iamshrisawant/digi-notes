# DigiNotes
#### Video Demo: <URL HERE>
#### Description:

<img src="./images/app_icon.png" alt="DigiNotes" width="200" height="200" align="right"/>

A lightweight digital sticky notes manager built using PySide6 (Qt for Python). DigiNotes runs in the system tray and allows users to manage multiple active sticky notes on their desktop. It features a glassmorphic user interface, in-place Markdown highlighting, list auto-continuation, interactive checklists, and a centralized control dashboard. All notes and window coordinates are saved locally to standard Markdown and JSON files.

---

### Core Features
* **Translucent Note Widgets**: Borderless, rounded-corner windows that utilize drop-shadow effects and adjust opacity dynamically based on window hover and focus states.
* **In-Place Markdown Highlighter**: Renders headers, bold, italics, underlines, strikethroughs, highlights, inline code, and LaTeX math blocks directly inside the active editor, hiding syntax tokens unless the cursor is on the active line.
* **Task and List Automation**: Allows task checkboxes (`- [ ]`) to be checked or unchecked by clicking on them. Pressing `Enter` automatically continues bulleted, numbered, or checkbox list lines.
* **Window Actions**: Supports pinning note widgets to lock coordinates, collapsing notes into small colored dot indicators, and drag-and-drop actions to spawn notes from the dashboard.
* **Centralized Dashboard**: A dedicated window to search note contents, create new notes, toggle note visibility, or permanently delete notes.
* **System Integration**: Runs in the system tray and supports system boot autostart configuration for Linux, macOS, and Windows.

---

### Files and Directories
* `src/main.py`: Initial entry point. Instantiates `QApplication`, configures a single-instance lock file (`QLockFile`), creates the tray icon menus, and manages note lifetimes via the `NoteManager` class.
* `src/dashboard.py`: Implements the central dashboard UI (`NotesDashboard`), handling note listings, text search filtering, note toggling, and drag-and-drop activation event filtering.
* `src/note_window.py`: Defines the `StickyNote` window and the custom title bar. Handles dragging behavior, window collapse animations, stays-on-top hints, and coordinates with `MarkdownHelpOverlay` to show formatting guides.
* `src/editor.py`: Houses the `MarkdownEditor` (`QTextEdit`) and `MarkdownLiveHighlighter` (`QSyntaxHighlighter`). Manages regex patterns for in-place text styling, list continuation shortcuts, and checkbox click events.
* `src/settings.py`: Implements the `SettingsDialog`. Provides a tabbed layout to customize application defaults and override layouts for individual active notes in real-time.
* `src/styles.py`: Serves as the application's stylesheet engine. Contains QSS rules for the pastel glassmorphic themes (Sunny Yellow, Ocean Blue, Mint Green, Pastel Orange, Lavender Purple, Rose Pink) and manages hover transparency parameters.
* `src/autostart.py`: A cross-platform utility class (`AutostartManager`) that manages system launch preferences by writing Linux `.desktop` files, Windows registry values, or macOS launch agent plist files.
* `run.sh` / `run.bat`: Shell and batch launcher scripts. They automate Python virtual environment setup, install requirements, set wayland display wrapper workarounds, and run `main.py`.
* `requirements.txt`: Lists project python dependencies (`PySide6-Essentials` and `markdown-it-py`).
* `data/`: Local storage directory. Saves note content to `data/notes/<id>.md`, layout coordinates to `<id>.md.meta` JSON files, and general configuration list to `data/config.json`.

---

### Design Decisions
* **Native Desktop Client**: Sticky notes must persist on the desktop alongside other active application windows. Web applications run inside browser frames and cannot support borderless, translucent overlays or utilize OS-level stays-on-top hints (such as `WindowStaysOnTopHint`), which made a native desktop client necessary.
* **PySide6 UI Framework**: PySide6 (Qt for Python) was selected over alternatives like Tkinter or PyQt5. Tkinter lacks native support for the alpha transparency, frameless windowing, and smooth animation APIs (`QPropertyAnimation`) required to construct a glassmorphic aesthetic. PySide6 was chosen over PyQt5 because it represents the modern Qt 6 standard, offering better high-DPI scaling and long-term library support.
* **Decoupled Markdown and JSON Storage**: Storing note bodies directly in plain Markdown (`.md`) files ensures user data remains readable outside the application. To prevent coordinates, sizes, and theme preferences from cluttering these files, this layout metadata is decoupled into separate `.meta` JSON files, keeping the raw markdown files clean.
* **In-Place Highlight Editor**: Standard markdown editors use a split-pane layout showing raw text alongside a rendered HTML preview window. Because sticky notes have limited screen space, a custom `QSyntaxHighlighter` was built to render styles dynamically within a single text editor, conserving workspace area.
* **Linux Wayland XCB Compatibility Wrapper**: Wayland compositors restrict application control over window coordinates and stays-on-top hints for security. To bypass this and ensure the notes function properly on modern Linux systems, the launcher script forces the application to run via the X11/XCB platform backend (`QT_QPA_PLATFORM="xcb"`), enabling consistent window layering.

---

### Setup and Running Instructions
1. Clone the repository and navigate to the project root.
2. Run the launcher script for your platform:
   * **Linux/macOS**: `chmod +x run.sh && ./run.sh`
   * **Windows**: `run.bat`
3. The script automatically builds a virtual environment, installs dependencies, and starts the manager in the system tray. Use the tray menu or the dashboard to manage your desktop sticky notes.
