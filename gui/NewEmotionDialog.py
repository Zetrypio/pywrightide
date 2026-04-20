from PyQt6.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog

class NewEmotionDialog(QDialog):

    def __init__(self, parent = None):
        super().__init__(parent)

        self.setWindowTitle("New Emotion")

        self._emotion_name_entry = QLineEdit()
        
        self._image_path_entry = QLineEdit()

        self._image_browse_button = QPushButton()
        self._image_browse_button.setText("Browse...")
        self._image_browse_button.clicked.connect(self._handle_browse_image)

        self._add_button = QPushButton("Add Emotion")
        self._add_button.clicked.connect(self._handle_create_new_emotion)

        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.clicked.connect(self.accept)

        emotion_name_layout = QHBoxLayout()
        emotion_name_layout.addWidget(QLabel("Emotion Name: "))
        emotion_name_layout.addWidget(self._emotion_name_entry)

        image_path_layout = QHBoxLayout()
        image_path_layout.addWidget(QLabel("Image Path: "))
        image_path_layout.addWidget(self._image_path_entry)
        image_path_layout.addWidget(self._image_browse_button)

        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.addStretch()
        bottom_buttons_layout.addWidget(self._add_button)
        bottom_buttons_layout.addWidget(self._cancel_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(emotion_name_layout)
        main_layout.addLayout(image_path_layout)
        main_layout.addLayout(bottom_buttons_layout)

        self.setLayout(main_layout)

    def _handle_browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image to import", filter="*.png;*.gif;*.webp;")
        self._image_path_entry.setText(path)

    def _handle_create_new_emotion(self):
        print("New Emotion TODO")
    
