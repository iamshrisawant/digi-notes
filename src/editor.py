# src/editor.py

import re
from PySide6.QtWidgets import QTextEdit, QMenu, QApplication
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QTextCursor, QAction
from PySide6.QtCore import Qt, QPoint, QRect, Signal
from styles import THEMES

class MarkdownLiveHighlighter(QSyntaxHighlighter):
    def __init__(self, editor):
        super().__init__(editor.document())
        self.editor = editor
        
        # Color palettes for high-contrast light pastel backgrounds
        self.color_header = QColor("#000000")      # Black
        self.color_bold = QColor("#1C1C1E")        # Solid dark text
        self.color_italic = QColor("#1C1C1E")      # Solid dark text
        self.color_code = QColor("#C2410C")        # Pastel Orange/Brown
        self.color_checkbox = QColor("#30D158")    # Success Green
        self.color_syntax_dim = QColor(142, 142, 147, 100) # Soft gray syntax character
        self.color_syntax_hide = QColor(0, 0, 0, 0) # Transparent

    def highlightBlock(self, text):
        cursor_block = self.editor.textCursor().blockNumber()
        current_block = self.currentBlock().blockNumber()
        is_cursor_line = (current_block == cursor_block)
        
        # 1. Heading Styles H1-H5
        hdr_match = re.match(r'^(#{1,5})\s+(.*)', text)
        if hdr_match:
            hashes, content = hdr_match.groups()
            prefix_len = len(hashes) + 1
            sizes = {1: 16, 2: 14, 3: 12, 4: 11, 5: 10}
            font_size = sizes.get(len(hashes), 10)
            self.apply_header_format(text, font_size, is_cursor_line, prefix_len)
            return

        # 2. Blockquotes (> text)
        bq_match = re.match(r'^(\s*>\s*)(.*)', text)
        if bq_match:
            prefix, content = bq_match.groups()
            prefix_len = len(prefix)
            
            fmt_syntax = QTextCharFormat()
            if is_cursor_line:
                fmt_syntax.setForeground(self.color_syntax_dim)
            else:
                fmt_syntax.setForeground(self.color_syntax_hide)
                fmt_syntax.setFontPointSize(1)
            self.setFormat(0, prefix_len, fmt_syntax)
            
            fmt_text = QTextCharFormat()
            fmt_text.setFontItalic(True)
            fmt_text.setForeground(QColor("#8E8E93"))
            self.setFormat(prefix_len, len(text) - prefix_len, fmt_text)
            
            self.highlight_inline_styles(text, is_cursor_line, prefix_len)
            return

        # 3. Horizontal Divider Rules (--- or ***)
        hr_match = re.match(r'^(\s*[\-\*_]{3,}\s*)$', text)
        if hr_match:
            fmt_hr = QTextCharFormat()
            fmt_hr.setForeground(QColor("#C7C7CC"))
            fmt_hr.setFontWeight(QFont.Weight.Bold)
            fmt_hr.setFontStrikeOut(True)
            self.setFormat(0, len(text), fmt_hr)
            return

        # 4. Checklist items (Checked or Unchecked)
        chk_checked = re.match(r'^(\s*[\-\*]\s+\[)([xX])(\]\s*)(.*)', text)
        chk_unchecked = re.match(r'^(\s*[\-\*]\s+\[)(\s)(\]\s*)(.*)', text)
        
        if chk_checked:
            prefix1, val, prefix2, rest = chk_checked.groups()
            prefix_len = len(prefix1) + len(val) + len(prefix2)
            
            fmt_syntax = QTextCharFormat()
            fmt_syntax.setForeground(self.color_checkbox if not is_cursor_line else self.color_syntax_dim)
            fmt_syntax.setFontWeight(QFont.Weight.Bold)
            self.setFormat(0, prefix_len, fmt_syntax)
            
            fmt_text = QTextCharFormat()
            fmt_text.setFontStrikeOut(True)
            fmt_text.setForeground(QColor("#8E8E93"))
            self.setFormat(prefix_len, len(text) - prefix_len, fmt_text)
            
            self.highlight_inline_styles(text, is_cursor_line, prefix_len)
            return
            
        elif chk_unchecked:
            prefix1, val, prefix2, rest = chk_unchecked.groups()
            prefix_len = len(prefix1) + len(val) + len(prefix2)
            
            fmt_syntax = QTextCharFormat()
            fmt_syntax.setForeground(self.color_checkbox if not is_cursor_line else self.color_syntax_dim)
            fmt_syntax.setFontWeight(QFont.Weight.Bold)
            self.setFormat(0, prefix_len, fmt_syntax)
            
            self.highlight_inline_styles(text, is_cursor_line, prefix_len)
            return

        # 5. Bullet & Numbered List Items
        bullet_match = re.match(r'^(\s*[\-\*\+]\s+)(.*)', text)
        if bullet_match:
            prefix, rest = bullet_match.groups()
            prefix_len = len(prefix)
            
            fmt_prefix = QTextCharFormat()
            note_window = self.editor.window()
            theme_key = getattr(note_window, "theme_key", "yellow")
            theme = THEMES.get(theme_key, THEMES["yellow"])
            accent_color = QColor(theme["accent_color"])
            
            fmt_prefix.setForeground(accent_color)
            fmt_prefix.setFontWeight(QFont.Weight.Bold)
            self.setFormat(0, prefix_len, fmt_prefix)
            
            self.highlight_inline_styles(text, is_cursor_line, prefix_len)
            return

        num_match = re.match(r'^(\s*\d+\.\s+)(.*)', text)
        if num_match:
            prefix, rest = num_match.groups()
            prefix_len = len(prefix)
            
            fmt_prefix = QTextCharFormat()
            note_window = self.editor.window()
            theme_key = getattr(note_window, "theme_key", "yellow")
            theme = THEMES.get(theme_key, THEMES["yellow"])
            accent_color = QColor(theme["accent_color"])
            
            fmt_prefix.setForeground(accent_color)
            fmt_prefix.setFontWeight(QFont.Weight.Bold)
            self.setFormat(0, prefix_len, fmt_prefix)
            
            self.highlight_inline_styles(text, is_cursor_line, prefix_len)
            return

        # 6. Standard lines
        self.highlight_inline_styles(text, is_cursor_line, 0)

    def apply_header_format(self, text, font_size, is_cursor_line, prefix_len):
        fmt_header = QTextCharFormat()
        fmt_header.setFontWeight(QFont.Weight.Bold)
        fmt_header.setFontPointSize(font_size)
        fmt_header.setForeground(self.color_header)
        self.setFormat(prefix_len, len(text) - prefix_len, fmt_header)
        
        fmt_prefix = QTextCharFormat()
        if is_cursor_line:
            fmt_prefix.setForeground(self.color_syntax_dim)
            fmt_prefix.setFontPointSize(font_size)
            self.setFormat(0, prefix_len, fmt_prefix)
        else:
            fmt_prefix.setForeground(self.color_syntax_hide)
            fmt_prefix.setFontPointSize(1)
            self.setFormat(0, prefix_len, fmt_prefix)

    def highlight_inline_styles(self, text, is_cursor_line, start_offset):
        # Bold **bold** & __bold__
        self.apply_regex_format(text, re.compile(r'\*\*([^\*]+)\*\*'), is_cursor_line, start_offset, border_len=2, font_weight=QFont.Weight.Bold, color=self.color_bold)
        self.apply_regex_format(text, re.compile(r'__([^_]+)__'), is_cursor_line, start_offset, border_len=2, font_weight=QFont.Weight.Bold, color=self.color_bold)

        # Italic *italic* & _italic_
        self.apply_regex_format(text, re.compile(r'(?<!\*)\*([^\*]+)\*(?!\*)'), is_cursor_line, start_offset, border_len=1, font_italic=True, color=self.color_italic)
        self.apply_regex_format(text, re.compile(r'(?<!_)_([^_]+)_(?!_)'), is_cursor_line, start_offset, border_len=1, font_italic=True, color=self.color_italic)

        # Underline <u>text</u>
        self.apply_regex_format(text, re.compile(r'<u>([^<]+)</u>'), is_cursor_line, start_offset, border_len=3, end_border_len=4, font_underline=True)

        # Strike-through ~~text~~
        self.apply_regex_format(text, re.compile(r'~~([^~]+)~~'), is_cursor_line, start_offset, border_len=2, font_strikeout=True, color=QColor("#8E8E93"))

        # Highlight ==text==
        self.apply_regex_format(text, re.compile(r'==([^=]+)=='), is_cursor_line, start_offset, border_len=2, bg_color=QColor("rgba(253, 224, 71, 0.40)"))

        # Inline Code `code`
        self.apply_regex_format(text, re.compile(r'`([^`]+)`'), is_cursor_line, start_offset, border_len=1, font_family="Courier New", color=self.color_code, bg_color=QColor("rgba(0, 0, 0, 0.05)"))

        # LaTeX $$latex$$
        self.apply_regex_format(text, re.compile(r'\$\$([^\$]+)\$\$'), is_cursor_line, start_offset, border_len=2, font_italic=True, color=QColor("#7E22CE"))

        # Links [label](url)
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        for m in link_pattern.finditer(text, start_offset):
            start, end = m.span()
            label, url = m.groups()
            label_start = start + 1
            label_len = len(label)
            url_part_start = label_start + label_len + 1 
            url_part_len = len(url) + 2 
            
            fmt_syntax = QTextCharFormat()
            if is_cursor_line:
                fmt_syntax.setForeground(self.color_syntax_dim)
            else:
                fmt_syntax.setForeground(self.color_syntax_hide)
                fmt_syntax.setFontPointSize(1)
            self.setFormat(start, 1, fmt_syntax)
            self.setFormat(label_start + label_len, url_part_len, fmt_syntax)
            
            fmt_text = QTextCharFormat()
            fmt_text.setFontUnderline(True)
            fmt_text.setForeground(QColor("#0A84FF"))
            self.setFormat(label_start, label_len, fmt_text)

    def apply_regex_format(self, text, pattern, is_cursor_line, start_offset, border_len, end_border_len=None, font_weight=None, font_italic=None, font_underline=None, font_strikeout=None, font_family=None, color=None, bg_color=None):
        if end_border_len is None:
            end_border_len = border_len
            
        for m in pattern.finditer(text, start_offset):
            start, end = m.span()
            length = end - start
            text_len = length - border_len - end_border_len
            
            # Borders
            fmt_syntax = QTextCharFormat()
            if is_cursor_line:
                fmt_syntax.setForeground(self.color_syntax_dim)
            else:
                fmt_syntax.setForeground(self.color_syntax_hide)
                fmt_syntax.setFontPointSize(1)
            self.setFormat(start, border_len, fmt_syntax)
            self.setFormat(end - end_border_len, end_border_len, fmt_syntax)
            
            # Text inside
            fmt_text = QTextCharFormat()
            if font_weight is not None:
                fmt_text.setFontWeight(font_weight)
            if font_italic is not None:
                fmt_text.setFontItalic(font_italic)
            if font_underline is not None:
                fmt_text.setFontUnderline(font_underline)
            if font_strikeout is not None:
                fmt_text.setFontStrikeOut(font_strikeout)
            if font_family is not None:
                fmt_text.setFontFamily(font_family)
            if color is not None:
                fmt_text.setForeground(color)
            if bg_color is not None:
                fmt_text.setBackground(bg_color)
                
            self.setFormat(start + border_len, text_len, fmt_text)


class MarkdownEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EditorArea")
        self.setAcceptRichText(False)
        self.setPlaceholderText("Type note here... (right-click for tools)")

        # Highlighter
        self.highlighter = MarkdownLiveHighlighter(self)
        self.prev_cursor_block = 0
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)

    def update_theme(self, is_dark_theme):
        self.highlighter.rehighlight()

    def on_cursor_position_changed(self):
        curr_block = self.textCursor().blockNumber()
        if curr_block != self.prev_cursor_block:
            doc = self.document()
            p_block = doc.findBlockByNumber(self.prev_cursor_block)
            c_block = doc.findBlockByNumber(curr_block)
            if p_block.isValid():
                self.highlighter.rehighlightBlock(p_block)
            if c_block.isValid():
                self.highlighter.rehighlightBlock(c_block)
            self.prev_cursor_block = curr_block

    def mousePressEvent(self, event):
        # Checkbox click-toggle detection
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.position().toPoint())
            block = cursor.block()
            text = block.text()
            
            # Match checked or unchecked task prefix
            match = re.match(r'^(\s*[\-\*]\s+\[)([\sxX\s])(\].*)', text)
            if match:
                col = cursor.positionInBlock()
                # If click falls inside the checkbox "[ ]" (typically characters 0-6)
                if 0 <= col <= 6:
                    prefix, val, suffix = match.groups()
                    new_val = " " if val.strip() else "x"
                    
                    cursor.beginEditBlock()
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    cursor.movePosition(QTextCursor.MoveOperation.KeepAnchor, QTextCursor.MoveOperation.EndOfBlock)
                    cursor.insertText(f"{prefix}{new_val}{suffix}")
                    cursor.endEditBlock()
                    
                    event.accept()
                    return

        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        # Custom right-click context menu
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
        
        copy_action = QAction("📋 Copy Content", self)
        copy_action.triggered.connect(self.copy_content)
        menu.addAction(copy_action)
        
        clear_action = QAction("🧹 Clear Content", self)
        clear_action.triggered.connect(self.clear_content)
        menu.addAction(clear_action)
        
        select_action = QAction("Select All", self)
        select_action.triggered.connect(self.selectAll)
        menu.addAction(select_action)
        
        menu.addSeparator()
        
        help_action = QAction("❓ Markdown Help Guide", self)
        help_action.triggered.connect(self.show_help_overlay)
        menu.addAction(help_action)
        
        menu.exec(event.globalPos())

    def copy_content(self):
        text = self.toPlainText()
        QApplication.clipboard().setText(text)

    def clear_content(self):
        self.clear()

    def show_help_overlay(self):
        note_window = self.window()
        if hasattr(note_window, 'show_help_overlay'):
            note_window.show_help_overlay()
