# src/note_window.py

import os
import re
import uuid
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QStackedWidget, QTextBrowser, QMenu, QGraphicsDropShadowEffect,
    QApplication
)
from PySide6.QtGui import QAction, QColor, QTextCursor, QMouseEvent
from PySide6.QtCore import Qt, QSize, QRect, QPoint, Signal, QUrl, QPropertyAnimation, QEasingCurve

from editor import MarkdownEditor
from styles import get_theme_stylesheet, THEMES
from markdown_it import MarkdownIt

class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(18)  # Thin handle style
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(2)
        
        # Left: Compact Color Dot Button
        self.color_btn = QPushButton(self)
        self.color_btn.setFixedSize(10, 10)
        self.color_btn.setStyleSheet("""
            QPushButton {
                border-radius: 5px;
                border: 1px solid rgba(0, 0, 0, 0.15);
            }
        """)
        layout.addWidget(self.color_btn)
        
        layout.addStretch()
        
        # Right: Action Buttons - Compact
        self.mode_btn = QPushButton("👁", self)
        self.mode_btn.setToolTip("Toggle Preview (Ctrl+P)")
        self.mode_btn.setProperty("class", "TitleBarButton")
        self.mode_btn.setFixedSize(16, 16)
        layout.addWidget(self.mode_btn)
        
        self.pin_btn = QPushButton("📌", self)
        self.pin_btn.setToolTip("Always on Top")
        self.pin_btn.setProperty("class", "TitleBarButton")
        self.pin_btn.setFixedSize(16, 16)
        layout.addWidget(self.pin_btn)
        
        self.collapse_btn = QPushButton("−", self)
        self.collapse_btn.setToolTip("Collapse to Dot")
        self.collapse_btn.setProperty("class", "TitleBarButton")
        self.collapse_btn.setFixedSize(16, 16)
        layout.addWidget(self.collapse_btn)
        
        self.close_btn = QPushButton("×", self)
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setToolTip("Hide Note")
        self.close_btn.setProperty("class", "TitleBarButton")
        self.close_btn.setFixedSize(16, 16)
        layout.addWidget(self.close_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.press_pos = event.globalPosition().toPoint()
            self.drag_triggered = False
            event.accept()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'press_pos') and not self.drag_triggered:
            dist = (event.globalPosition().toPoint() - self.press_pos).manhattanLength()
            if dist > 6:
                self.drag_triggered = True
                window = self.window()
                if window and window.windowHandle():
                    window.windowHandle().startSystemMove()
                else:
                    self.parent().initiate_fallback_drag(event)
                event.accept()


class StickyNote(QWidget):
    # Signal emitted when a note is updated or closed
    config_changed = Signal()
    note_deleted = Signal(str)

    def __init__(self, note_id=None, manager=None):
        super().__init__()
        self.manager = manager
        self.note_id = note_id or str(uuid.uuid4())
        
        # Storage
        self.data_dir = "./data"
        self.notes_dir = os.path.join(self.data_dir, "notes")
        os.makedirs(self.notes_dir, exist_ok=True)
        self.filepath = os.path.join(self.notes_dir, f"{self.note_id}.md")
        
        # Default Settings
        self.theme_key = "yellow"
        self.is_pinned = True
        self.is_collapsed = False
        self.view_mode = "edit"
        self.expanded_geometry = QRect(200, 200, 240, 200) # Compact sticky sizes
        
        # Animation & Opacity helpers
        self.opacity_anim = None
        self.geom_anim = None
        self.is_focused = False
        
        # Window attributes
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(80, 60)
        
        self.init_ui()
        self.load_note()
        self.apply_theme()
        
        # Apply initial theme stylesheet
        
        # Setup Autosave
        self.editor.textChanged.connect(self.save_note)

    def init_ui(self):
        # Base shadow frame to host glassmorphism styling
        self.main_widget = QWidget(self)
        self.main_widget.setObjectName("NoteWidget")
        
        # Layouts
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)  # Margin space for drop shadow
        self.main_layout.addWidget(self.main_widget)
        
        self.content_layout = QVBoxLayout(self.main_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Title Bar
        self.title_bar = TitleBar(self)
        self.content_layout.addWidget(self.title_bar)
        
        # Content Stack
        self.stack = QStackedWidget(self)
        self.content_layout.addWidget(self.stack)
        
        # Page 1: Editor
        self.editor = MarkdownEditor(self, is_dark_theme=False)
        self.stack.addWidget(self.editor)
        
        # Page 2: Rendered view
        self.viewer = QTextBrowser(self)
        self.viewer.setObjectName("RenderArea")
        self.viewer.setOpenLinks(False)
        self.viewer.anchorClicked.connect(self.handle_link_click)
        self.stack.addWidget(self.viewer)
        
        # Collapsed Dot Widget - Smaller (24x24)
        self.dot_widget = QPushButton(self)
        self.dot_widget.setObjectName("CollapsedDot")
        self.dot_widget.setFixedSize(24, 24)
        self.dot_widget.setToolTip("Click once to expand note")
        self.dot_widget.hide()
        
        # Connect Buttons
        self.title_bar.mode_btn.clicked.connect(self.toggle_view_mode)
        self.title_bar.pin_btn.clicked.connect(self.toggle_pinned)
        self.title_bar.collapse_btn.clicked.connect(self.toggle_collapse)
        self.title_bar.close_btn.clicked.connect(self.deactivate)
        self.title_bar.color_btn.clicked.connect(self.show_color_menu)
        
        # Collapsed Dot drag or click filters
        self.dot_widget.installEventFilter(self)
        
        # Add Drop Shadow effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(10)
        self.shadow.setColor(QColor(0, 0, 0, 50))
        self.shadow.setOffset(0, 3)
        self.main_widget.setGraphicsEffect(self.shadow)

    # Hover & Focus Transitions via Style Engine
    def enterEvent(self, event):
        self.apply_theme_state(is_hovered=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.apply_theme_state(is_hovered=self.is_focused)
        super().leaveEvent(event)

    def set_focused_state(self, is_focused):
        self.is_focused = is_focused
        self.apply_theme_state(self.underMouse() or self.is_focused)

    def apply_theme_state(self, is_hovered):
        if self.is_collapsed:
            # Styled dot opacity
            theme = THEMES.get(self.theme_key, THEMES["yellow"])
            hex_color = theme['accent_color'].lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            alpha = 240 if is_hovered else 90 # 0.94 vs 0.35
            hover_alpha = 240
            
            self.dot_widget.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba({r}, {g}, {b}, {alpha});
                    border: 1px solid rgba(255, 255, 255, 0.75);
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    background-color: rgba({r}, {g}, {b}, {hover_alpha});
                }}
            """)
        else:
            qss = get_theme_stylesheet(self.theme_key, is_hovered=is_hovered)
            self.setStyleSheet(qss)

    def eventFilter(self, watched, event):
        # Handle dragging vs single-clicking of the collapsed dot
        if watched == self.dot_widget:
            if event.type() == QMouseEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.dot_press_pos = event.globalPosition().toPoint()
                    self.dot_drag_triggered = False
                    event.accept()
                    return True
            elif event.type() == QMouseEvent.Type.MouseMove:
                if hasattr(self, 'dot_press_pos') and not self.dot_drag_triggered:
                    dist = (event.globalPosition().toPoint() - self.dot_press_pos).manhattanLength()
                    if dist > 6:
                        self.dot_drag_triggered = True
                        window = self.window()
                        if window and window.windowHandle():
                            window.windowHandle().startSystemMove()
                        else:
                            self.initiate_fallback_drag(event)
                        event.accept()
                        return True
            elif event.type() == QMouseEvent.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton:
                    if hasattr(self, 'dot_drag_triggered') and not self.dot_drag_triggered:
                        # Single-click triggers expand state!
                        self.toggle_collapse()
                    event.accept()
                    return True
        return super().eventFilter(watched, event)

    def initiate_fallback_drag(self, event):
        self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Click hold drags note by background click
            self.press_pos = event.globalPosition().toPoint()
            self.drag_triggered = False
            event.accept()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'press_pos') and not self.drag_triggered:
            dist = (event.globalPosition().toPoint() - self.press_pos).manhattanLength()
            if dist > 6:
                self.drag_triggered = True
                window = self.window()
                if window and window.windowHandle():
                    window.windowHandle().startSystemMove()
                else:
                    self.initiate_fallback_drag(event)
                event.accept()
        elif hasattr(self, 'drag_position'):
            # Fallback manual move
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'drag_position'):
            delattr(self, 'drag_position')
        super().mouseReleaseEvent(event)

    def apply_theme(self):
        self.apply_theme_state(is_hovered=self.underMouse() or self.is_focused)
        
        # Update Editor syntax highlight colors
        is_dark = (self.theme_key == "carbon")
        self.editor.update_theme(is_dark)
        
        # Re-render view
        if self.view_mode == "render":
            self.render_markdown()

    def show_color_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(30, 30, 30, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                color: #F2F2F7;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        
        # Color Themes
        for key, theme in THEMES.items():
            action = QAction(theme["name"], self)
            action.triggered.connect(lambda checked=False, k=key: self.set_theme(k))
            menu.addAction(action)
            
        menu.addSeparator()
        
        # Multipurpose Templates (Standard vs Checklist)
        todo_action = QAction("📋 Convert to Checklist", self)
        todo_action.triggered.connect(self.convert_to_checklist)
        menu.addAction(todo_action)
        
        note_action = QAction("📝 Convert to Standard", self)
        note_action.triggered.connect(self.convert_to_standard)
        menu.addAction(note_action)
        
        menu.exec(self.title_bar.color_btn.mapToGlobal(QPoint(0, self.title_bar.color_btn.height())))

    def set_theme(self, theme_key):
        self.theme_key = theme_key
        self.apply_theme()
        self.config_changed.emit()

    def convert_to_checklist(self):
        content = self.editor.toPlainText().strip()
        # Prepopulate list template if empty or no lists
        if not content or not re.search(r'\[\s\]|\[[xX]\]', content):
            checklist_template = "# Checklist\n- [ ] Task 1\n- [ ] Task 2"
            if content:
                content = content + "\n\n" + checklist_template
            else:
                content = checklist_template
            self.editor.setPlainText(content)
            
        # Swap view mode to preview to display checklist elements
        if self.view_mode == "edit":
            self.toggle_view_mode()
        self.config_changed.emit()

    def convert_to_standard(self):
        content = self.editor.toPlainText()
        # Remove checkbox tags
        cleaned = re.sub(r'^\s*[\-\*]\s+\[[\sxX]\]\s*', '- ', content, flags=re.MULTILINE)
        self.editor.setPlainText(cleaned)
        if self.view_mode == "render":
            self.toggle_view_mode()
        self.config_changed.emit()

    def confirm_delete(self):
        self.note_deleted.emit(self.note_id)

    def toggle_pinned(self):
        self.is_pinned = not self.is_pinned
        self.apply_pinned_state()
        self.config_changed.emit()

    def apply_pinned_state(self):
        flags = self.windowFlags()
        if self.is_pinned:
            flags |= Qt.WindowType.WindowStaysOnTopHint
            self.title_bar.pin_btn.setText("📌")
            self.title_bar.pin_btn.setStyleSheet("background-color: rgba(255, 255, 255, 0.15);")
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
            self.title_bar.pin_btn.setText("📍")
            self.title_bar.pin_btn.setStyleSheet("")
            
        self.setWindowFlags(flags)
        self.show()

    def toggle_view_mode(self):
        if self.view_mode == "edit":
            self.view_mode = "render"
            self.title_bar.mode_btn.setText("✏")
            self.title_bar.mode_btn.setToolTip("Edit Note (Ctrl+P)")
            self.render_markdown()
            self.stack.setCurrentIndex(1)
        else:
            self.view_mode = "edit"
            self.title_bar.mode_btn.setText("👁")
            self.title_bar.mode_btn.setToolTip("Preview Note (Ctrl+P)")
            self.stack.setCurrentIndex(0)
            self.editor.setFocus()
        self.config_changed.emit()

    def render_markdown(self):
        raw_text = self.editor.toPlainText()
        theme = THEMES.get(self.theme_key, THEMES["yellow"])
        html = self.get_rendered_html(raw_text, theme["text_color"], theme["accent_color"])
        self.viewer.setHtml(html)

    # GitHub Markdown spec rendering (Jekyll style)
    def get_rendered_html(self, markdown_text, text_color, accent_color):
        lines = markdown_text.split('\n')
        checkbox_idx = 0
        processed_lines = []
        
        for line in lines:
            match_unchecked = re.match(r'^(\s*[\-\*]\s+)\[\s\](.*)', line)
            match_checked = re.match(r'^(\s*[\-\*]\s+)\[[xX]\](.*)', line)
            
            if match_unchecked:
                prefix, rest = match_unchecked.groups()
                line = f"{prefix}<a href='toggle:{checkbox_idx}' style='text-decoration:none; color:{text_color}; font-family: monospace; font-size: 15px;'>☐</a> {rest}"
                checkbox_idx += 1
            elif match_checked:
                prefix, rest = match_checked.groups()
                line = f"{prefix}<a href='toggle:{checkbox_idx}' style='text-decoration:none; color:{accent_color}; font-family: monospace; font-size: 15px;'>☑</a> <span style='text-decoration: line-through; opacity: 0.55;'>{rest}</span>"
                checkbox_idx += 1
                
            processed_lines.append(line)
            
        processed_md = '\n'.join(processed_lines)
        
        md = MarkdownIt("commonmark")
        html_body = md.render(processed_md)
        
        # Color theme styles matching GitHub Markdown CSS rules
        is_dark = (self.theme_key == "carbon")
        border_color = "rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.06)"
        code_bg = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.04)"
        hr_color = "rgba(255,255,255,0.15)" if is_dark else "rgba(0,0,0,0.08)"
        
        styled_html = f"""
        <html>
        <head>
        <style>
            body {{
                color: {text_color};
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
                font-size: 13px;
                line-height: 1.6;
                margin: 6px 10px;
            }}
            p {{ margin: 0 0 6px 0; }}
            a {{
                color: {accent_color};
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            h1, h2, h3 {{
                margin: 10px 0 4px 0;
                font-weight: 600;
                color: {accent_color};
                line-height: 1.25;
            }}
            h1 {{ font-size: 15px; border-bottom: 1px solid {border_color}; padding-bottom: 2px; }}
            h2 {{ font-size: 13.5px; }}
            h3 {{ font-size: 13px; }}
            hr {{
                height: 1px;
                padding: 0;
                margin: 10px 0;
                background-color: {hr_color};
                border: 0;
            }}
            code {{
                font-family: ui-monospace, SFMono-Regular, SF Pro Mono, Menlo, monospace;
                background-color: {code_bg};
                padding: 1px 4px;
                border-radius: 3px;
                font-size: 11.5px;
            }}
            pre {{
                background-color: {code_bg};
                padding: 6px;
                border-radius: 4px;
                overflow-x: auto;
                margin: 0 0 8px 0;
            }}
            pre code {{
                padding: 0;
                background-color: transparent;
            }}
            ul, ol {{
                margin: 0 0 6px 0;
                padding-left: 18px;
            }}
            li {{ margin-bottom: 2px; }}
            blockquote {{
                margin: 0 0 8px 0;
                padding: 0 8px;
                color: #8E8E93;
                border-left: 3px solid #0A84FF;
            }}
        </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """
        return styled_html

    def handle_link_click(self, url):
        url_str = url.toString()
        if url_str.startswith("toggle:"):
            try:
                idx = int(url_str.split(":")[1])
                self.toggle_checkbox_at_index(idx)
            except Exception as e:
                print("Error toggling checkbox:", e)

    def toggle_checkbox_at_index(self, index_to_toggle):
        markdown_text = self.editor.toPlainText()
        pattern = re.compile(r'(\[\s\]|\[[xX]\])')
        matches = list(pattern.finditer(markdown_text))
        
        if 0 <= index_to_toggle < len(matches):
            match = matches[index_to_toggle]
            start, end = match.span()
            current_val = match.group(1)
            new_val = "[x]" if current_val == "[ ]" else "[ ]"
            new_text = markdown_text[:start] + new_val + markdown_text[end:]
            self.editor.setPlainText(new_text)
            self.render_markdown()

    # Smooth Collapse/Expand Transitions using QPropertyAnimation
    def toggle_collapse(self):
        if self.geom_anim and self.geom_anim.state() == QPropertyAnimation.State.Running:
            return
            
        if not self.is_collapsed:
            # 1. Collapse Note to Dot
            self.expanded_geometry = self.geometry()
            self.is_collapsed = True
            
            # Target geometry is a 24x24 rect centered in current window
            center = self.geometry().center()
            target_rect = QRect(center.x() - 12, center.y() - 12, 24, 24)
            
            # Swap widgets before sizing animation to prevent clipping
            self.main_widget.hide()
            self.main_layout.removeWidget(self.main_widget)
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.main_layout.addWidget(self.dot_widget)
            
            # Apply initial unhovered theme state to the dot
            self.apply_theme_state(is_hovered=False)
            self.dot_widget.show()
            
            # Run transition size animation
            self.animate_transition(target_rect)
        else:
            # 2. Expand Dot to Note window
            self.is_collapsed = False
            
            # Hide dot
            self.dot_widget.hide()
            self.main_layout.removeWidget(self.dot_widget)
            
            # Restore margins for drop shadow
            self.main_layout.setContentsMargins(8, 8, 8, 8)
            self.main_layout.addWidget(self.main_widget)
            self.main_widget.show()
            
            # Set to hovered style instantly on expand since cursor is on it
            self.apply_theme_state(is_hovered=True)
            
            # Run expand size animation
            self.animate_transition(self.expanded_geometry)

    def animate_transition(self, target_rect):
        self.geom_anim = QPropertyAnimation(self, b"geometry")
        self.geom_anim.setDuration(220)
        self.geom_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.geom_anim.setStartValue(self.geometry())
        self.geom_anim.setEndValue(target_rect)
        
        # Enforce always stays on top flag persists through sizing
        self.geom_anim.finished.connect(self.ensure_on_top)
        self.geom_anim.start()

    def ensure_on_top(self):
        # Keep window stays on top flag enforced
        flags = self.windowFlags()
        if not (flags & Qt.WindowType.WindowStaysOnTopHint):
            flags |= Qt.WindowType.WindowStaysOnTopHint
            self.setWindowFlags(flags)
            self.show()

    def deactivate(self):
        # Set note state to inactive (closed) in manager
        self.hide()
        if self.manager:
            self.manager.toggle_note_active(self.note_id, False)

    def load_note(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.editor.setPlainText(content)

    def save_note(self):
        content = self.editor.toPlainText()
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def load_config(self, config_dict):
        self.theme_key = config_dict.get("theme", "yellow")
        self.is_pinned = config_dict.get("pinned", True)
        self.is_collapsed = config_dict.get("collapsed", False)
        self.view_mode = config_dict.get("view_mode", "edit")
        
        x = config_dict.get("x", 200)
        y = config_dict.get("y", 200)
        w = config_dict.get("w", 240)
        h = config_dict.get("h", 200)
        
        self.expanded_geometry = QRect(x, y, w, h)
        
        self.apply_theme()
        self.apply_pinned_state()
        
        if self.view_mode == "render":
            self.view_mode = "edit"
            self.toggle_view_mode()
        else:
            self.stack.setCurrentIndex(0)
            
        if self.is_collapsed:
            self.is_collapsed = False
            self.toggle_collapse()
            center_x = x + w // 2 - 12
            center_y = y + h // 2 - 12
            self.move(center_x, center_y)
        else:
            self.setGeometry(self.expanded_geometry)

    def get_config(self):
        geom = self.expanded_geometry
        current_geom = self.geometry()
        
        if not self.is_collapsed:
            x, y, w, h = current_geom.x(), current_geom.y(), current_geom.width(), current_geom.height()
        else:
            x, y, w, h = geom.x(), geom.y(), geom.width(), geom.height()
            
        # Get active status from parent notes mapping in manager
        is_active = True
        if self.manager:
            is_active = self.note_id in self.manager.notes
            
        return {
            "id": self.note_id,
            "theme": self.theme_key,
            "pinned": self.is_pinned,
            "collapsed": self.is_collapsed,
            "view_mode": self.view_mode,
            "active": is_active,
            "x": x,
            "y": y,
            "w": w,
            "h": h
        }

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_P:
            self.toggle_view_mode()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.save_note()
        self.config_changed.emit()
        super().closeEvent(event)
