from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal

from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor, QGuiApplication
from PyQt6.QtWidgets import QDialog, QComboBox, QLabel, QVBoxLayout, QHBoxLayout, QSpinBox, QLayout, QPushButton, \
    QSlider, QInputDialog

from data.PyWrightGame import CurrentPyWrightGame
from data.SpriteSheet import SpriteSheet
from data import IconThemes

from gui.NewEmotionDialog import NewEmotionDialog

GAME_TICK_RATE = 1000 / 60 # 60 FPS


class CharacterViewerDialog(QDialog):

    # Sends the appropriate command
    command_insert_at_cursor_requested = pyqtSignal(str)

    def __init__(self, parent = None):
        super().__init__(parent)

        self.setWindowTitle("Character Viewer")

        self._add_character_button = QPushButton()
        self._add_character_button.setText("New Character")
        self._add_character_button.clicked.connect(self._handle_new_character)

        self._add_emotion_button = QPushButton()
        self._add_emotion_button.setText("New Emotion")
        self._add_emotion_button.clicked.connect(self._handle_new_emotion)

        self._character_combobox = QComboBox(self)
        self._character_combobox.currentIndexChanged.connect(self._handle_character_combobox_changed)
        self._emotion_combobox = QComboBox(self)
        self._emotion_combobox.currentIndexChanged.connect(self._handle_emotion_combobox_changed)

        self._frame_number_spinbox = QSpinBox()
        self._frame_number_spinbox.valueChanged.connect(self._handle_frame_number_value_changed)
        self._frame_count_label = QLabel("of 1")

        self._image_label = SpriteViewLabel()
        self._current_frame_pixmap = QPixmap()
        self._image_label.resize(768,576)
        self._image_label.setPixmap(self._current_frame_pixmap)

        play_icon_path = IconThemes.icon_path_from_theme(IconThemes.ICON_NAME_AUDIO_PLAY)
        stop_icon_path = IconThemes.icon_path_from_theme(IconThemes.ICON_NAME_AUDIO_STOP)
        self._play_icon = QIcon(play_icon_path)
        self._stop_icon = QIcon(stop_icon_path)

        self._play_button = QPushButton()
        self._play_button.setIcon(self._play_icon)
        self._play_button.setToolTip("Play animation")
        self._play_button.clicked.connect(self._handle_play_button_pressed)

        self._frame_slider = QSlider(Qt.Orientation.Horizontal)
        self._frame_slider.valueChanged.connect(self._handle_slider_value_changed)

        self._copy_to_clipboard_button = QPushButton("Copy to clipboard")
        self._copy_to_clipboard_button.setToolTip("Copy the current character and emotion to clipboard as a command")
        self._copy_to_clipboard_button.clicked.connect(self._handle_copy_to_clipboard_pressed)

        self._close_button = QPushButton("Close")
        self._close_button.clicked.connect(self.accept)

        self._insert_into_current_cursor_position_button = QPushButton("Insert into cursor position")
        self._insert_into_current_cursor_position_button.setToolTip("Insert the command for the current character and emotion into the current cursor position")
        self._insert_into_current_cursor_position_button.clicked.connect(self._handle_insert_to_cursor_button_pressed)

        self._spritesheet : SpriteSheet | None = None

        self._populate_character_combobox()

        self._is_playing_anim = False

        self._next_frame_timer : QTimer | None = None

        main_layout = QVBoxLayout()

        new_button_layout = QHBoxLayout()
        new_button_layout.addWidget(self._add_character_button)
        new_button_layout.addWidget(self._add_emotion_button)

        character_layout = QHBoxLayout()
        character_layout.addWidget(QLabel("Character:"))
        character_layout.addWidget(self._character_combobox)

        emotion_layout = QHBoxLayout()
        emotion_layout.addWidget(QLabel("Emotion:"))
        emotion_layout.addWidget(self._emotion_combobox)

        frame_selector_layout = QHBoxLayout()
        frame_selector_layout.addWidget(self._play_button)
        frame_selector_layout.addWidget(self._frame_slider)
        frame_selector_layout.addWidget(QLabel("Frame: "))
        frame_selector_layout.addWidget(self._frame_number_spinbox)
        frame_selector_layout.addWidget(self._frame_count_label)

        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.addWidget(self._copy_to_clipboard_button)
        bottom_buttons_layout.addWidget(self._insert_into_current_cursor_position_button)
        bottom_buttons_layout.addStretch()
        bottom_buttons_layout.addWidget(self._close_button)

        main_layout.addLayout(new_button_layout)
        main_layout.addLayout(character_layout)
        main_layout.addLayout(emotion_layout)
        main_layout.addLayout(frame_selector_layout)
        main_layout.addWidget(self._image_label)
        main_layout.addLayout(bottom_buttons_layout)

        main_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.setLayout(main_layout)

    def _populate_character_combobox(self):
        port_path = CurrentPyWrightGame().current_game.game_path / "art" / "port"

        self._character_combobox.addItems([x.stem for x in port_path.iterdir() if x.is_dir()])

    def _handle_new_character(self):
        result, ok = QInputDialog.getText(self, "New Character Name", "Enter new character name")
        if ok:
            print(result)

    def _handle_new_emotion(self):
        new_emotion_dialog = NewEmotionDialog(self)
        new_emotion_dialog.show()

    def _handle_character_combobox_changed(self):
        if self._character_combobox.count() == 0:
            return

        self._populate_emotion_combobox()

    def _handle_emotion_combobox_changed(self):
        if self._emotion_combobox.count() == 0:
            return

        character = self._character_combobox.currentText()
        emotion = self._emotion_combobox.currentText() + ".png"
        file_path = CurrentPyWrightGame().current_game.game_path / "art" / "port" / character / emotion

        self._spritesheet = SpriteSheet(file_path)

        self._play_button.setEnabled(self._spritesheet.num_frames > 1)
        self._frame_slider.setEnabled(self._spritesheet.num_frames > 1)
        self._frame_number_spinbox.setEnabled(self._spritesheet.num_frames > 1)

        self._frame_count_label.setText("of {}".format(self._spritesheet.num_frames))
        self._frame_number_spinbox.setRange(1, self._spritesheet.num_frames)
        self._frame_slider.setRange(1, self._spritesheet.num_frames)
        self._frame_number_spinbox.setValue(1) # This will also set the frame_slider's value implicitly

        frame = self._spritesheet.get_frame(0)
        self._current_frame_pixmap = QPixmap.fromImage(frame).scaled(self._image_label.width(), self._image_label.height(), Qt.AspectRatioMode.KeepAspectRatio)
        self._image_label.setPixmap(self._current_frame_pixmap)

    def _populate_emotion_combobox(self):
        self._emotion_combobox.clear()
        character_path = CurrentPyWrightGame().current_game.game_path / "art" / "port" / self._character_combobox.currentText()

        self._emotion_combobox.addItems([x.stem for x in character_path.iterdir() if x.is_file() and x.suffix == ".png"])

    def _handle_frame_number_value_changed(self):
        frame_num = self._frame_number_spinbox.value() - 1

        if self._frame_slider.value() != self._frame_number_spinbox.value():
            self._frame_slider.setValue(self._frame_number_spinbox.value())

        frame = self._spritesheet.get_frame(frame_num)
        self._current_frame_pixmap = QPixmap.fromImage(frame)
        self._image_label.setPixmap(self._current_frame_pixmap)

    def _handle_slider_value_changed(self):
        if self._frame_slider.value() != self._frame_number_spinbox.value():
            self._frame_number_spinbox.setValue(self._frame_slider.value())

    def _handle_insert_to_cursor_button_pressed(self):
        command = "char {} e={}".format(self._character_combobox.currentText(), self._emotion_combobox.currentText())
        self.command_insert_at_cursor_requested.emit(command)

    def _handle_copy_to_clipboard_pressed(self):
        command = "char {} e={}".format(self._character_combobox.currentText(), self._emotion_combobox.currentText())
        clipboard = QGuiApplication.clipboard()

        clipboard.setText(command)

    def _handle_play_button_pressed(self):
        frame_num = self._frame_number_spinbox.value() - 1

        if frame_num >= self._spritesheet.num_frames - 1:
            self._frame_number_spinbox.setValue(1)
            frame_num = 0

        self._is_playing_anim = not self._is_playing_anim

        self._play_button.setIcon(self._stop_icon if self._is_playing_anim else self._play_icon)
        self._play_button.setToolTip("Stop animation" if self._is_playing_anim else "Play animation")

        self._frame_number_spinbox.setEnabled(not self._is_playing_anim)
        self._frame_slider.setEnabled(not self._is_playing_anim)
        self._character_combobox.setEnabled(not self._is_playing_anim)
        self._emotion_combobox.setEnabled(not self._is_playing_anim)

        if not self._is_playing_anim:
            self._next_frame_timer.stop()
            return

        self._next_frame_timer = QTimer()
        self._next_frame_timer.setSingleShot(True)
        self._next_frame_timer.timeout.connect(self._handle_next_frame_timeout)
        self._next_frame_timer.start(0)

    def _handle_next_frame_timeout(self):
        frame_num = self._frame_number_spinbox.value() - 1
        
        if frame_num >= self._spritesheet.num_frames - 1:
            self._frame_number_spinbox.setValue(1)
            frame_num = 0
        else:
            frame_num += 1
            self._frame_number_spinbox.setValue(frame_num + 1)
            
        current_framedelay = self._spritesheet.get_framedelay_for_frame(frame_num)
        self._next_frame_timer.start(int(current_framedelay * GAME_TICK_RATE))


class SpriteViewLabel(QLabel):
    """A custom label that draws a checkerboard pattern as a background and centers pixmaps"""
    def __init__(self, parent = None):
        super().__init__(parent)
        
    def scale_and_pad_pixmap(self, pixmap, target_width, target_height):
        scaled = pixmap.scaledToHeight(target_height)

        result = QPixmap(target_width, target_height)
        result.fill(Qt.GlobalColor.transparent) # correctly sized canvas
        
        painter = QPainter(result)
        # center pixmap
        x_offset = (target_width - scaled.width()) // 2
        painter.drawPixmap(x_offset, 0, scaled)
        painter.end()

        return result
        
    def setPixmap(self, new_pixmap):
        if new_pixmap:
            scaled_pixmap = self.scale_and_pad_pixmap(new_pixmap, self.width(), self.height())
            super().setPixmap(scaled_pixmap)

    def paintEvent(self, event):
        painter = QPainter(self)

        light_gray = QColor(210, 210, 210)
        white = QColor(255, 255, 255)

        for y in range(0, self.height(), 16):
            for x in range(0, self.width(), 16):
                color = light_gray if ((x // 16) + (y // 16)) % 2 else white
                painter.fillRect(x, y, 16, 16, color)

        if self.pixmap() and not self.pixmap().isNull():
            painter.drawPixmap(0, 0, self.pixmap())