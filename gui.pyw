import sys, json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QFileDialog, QFrame, QStackedWidget, QScrollArea
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from service import Processor

IMAGE_PROCESSOR = Processor()

# ✅ Словарь для русских названий пунктов
COMPARISON_LABELS = {
    "energy_value": "Энергетическая ценность",
    "sodium": "Натрий",
    "total_sugar": "Общий сахар",
    "free_sugar": "Свободный сахар",
    "total_protein": "Белки",
    "total_fat": "Жиры",
    "fruit_content": "Содержание фруктов",
    "age_marking": "Возрастная маркировка",
    "high_sugar_front_packaging": "Высокий сахар на упаковке",
    "labeling": "Маркировка"
}


# ---------- Виджет для превью изображений ----------
class ImagePreview(QFrame):
    def __init__(self, file_path, remove_callback):
        super().__init__()
        self.file_path = file_path
        self.remove_callback = remove_callback

        self.setFixedSize(160, 160)
        self.setStyleSheet("background-color: #2a2a2a; border-radius: 10px;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setFixedSize(160, 130)
        pixmap = QPixmap(file_path).scaled(160, 130, Qt.AspectRatioMode.KeepAspectRatioByExpanding)
        self.image_label.setPixmap(pixmap)
        self.image_label.setStyleSheet("border-top-left-radius: 10px; border-top-right-radius: 10px;")
        layout.addWidget(self.image_label)

        remove_btn = QPushButton("✖")
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff5555;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff7777;
            }
        """)
        remove_btn.clicked.connect(self.remove_image)
        layout.addWidget(remove_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    def remove_image(self):
        self.remove_callback(self.file_path)


# ---------- Виджет загрузки изображений ----------
class ImageUploadWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.images = []

        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #444;
                border-radius: 15px;
                color: #bbb;
                background-color: #222;
            }
        """)
        self.layout = QHBoxLayout()
        self.layout.setSpacing(10)
        self.setLayout(self.layout)

        self.placeholder = QLabel("Перетащите сюда изображения (до 3)")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.placeholder)
    
    def clear_images(self):
        for img_path, preview_widget in self.images:
            preview_widget.deleteLater()
        self.images.clear()
        self.layout.addWidget(self.placeholder)
        self.placeholder.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if len(self.images) < 3:
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.add_image(file_path)

    def add_image(self, file_path):
        if len(self.images) >= 3:
            return
        if self.placeholder in [self.layout.itemAt(i).widget() for i in range(self.layout.count())]:
            self.layout.removeWidget(self.placeholder)
            self.placeholder.hide()

        preview = ImagePreview(file_path, self.remove_image)
        self.layout.addWidget(preview)
        self.images.append((file_path, preview))

    def remove_image(self, file_path):
        for img in self.images:
            if img[0] == file_path:
                widget = img[1]
                self.layout.removeWidget(widget)
                widget.deleteLater()
                self.images.remove(img)
                break
        if not self.images:
            self.layout.addWidget(self.placeholder)
            self.placeholder.show()


# ---------- Основное окно ----------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Честный знак")
        self.setGeometry(200, 100, 1000, 600)
        self.setStyleSheet("background-color: #121212; color: #fff; font-family: Arial; font-size: 14px;")

        self.stack = QStackedWidget()
        main_screen = self.create_main_screen()
        self.history_screen = self.create_history_screen()

        self.stack.addWidget(main_screen)
        self.stack.addWidget(self.history_screen)

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

    def create_main_screen(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        content_layout = QHBoxLayout()

        header_title = QLabel("Честный знак")
        header_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()

        history_button = QPushButton("История")
        history_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                border: none;
                padding: 8px 16px;
                border-radius: 10px;
                color: #fff;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        history_button.clicked.connect(self.show_history)
        header_layout.addWidget(history_button)

        self.upload_widget = ImageUploadWidget()
        upload_container = QVBoxLayout()
        upload_container.addWidget(self.upload_widget)

        self.upload_button = QPushButton("Загрузить изображение")
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.upload_button.clicked.connect(self.open_file_dialog)
        upload_container.addWidget(self.upload_button)

        self.analyze_button = QPushButton("Проанализировать")
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #6200ea;
                color: white;
                border-radius: 10px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7b1ffa;
            }
        """)
        self.analyze_button.clicked.connect(self.analyze_images)
        upload_container.addWidget(self.analyze_button)

        left_frame = QFrame()
        left_frame.setStyleSheet("background-color: #1e1e1e; border-radius: 15px;")
        left_frame.setLayout(upload_container)

        self.analysis_scroll = QScrollArea()
        self.analysis_scroll.setWidgetResizable(True)
        self.analysis_scroll.setStyleSheet("border: none;")

        self.analysis_container = QWidget()
        self.analysis_layout = QVBoxLayout()
        self.analysis_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.analysis_title = QLabel("Информация о продукте")
        self.analysis_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFD700;")
        self.analysis_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.analysis_layout.addWidget(self.analysis_title)

        self.placeholder_frame = QFrame()
        placeholder_layout = QVBoxLayout()
        placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        '''        placeholder_image = QLabel()
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        placeholder_image.setPixmap(QPixmap("placeholder.png") if QPixmap("placeholder.png") else pixmap)

        placeholder_text = QLabel("Пока тут ничего нет...")
        placeholder_text.setStyleSheet("color: #777; font-size: 14px;")

        placeholder_layout.addWidget(placeholder_image)
        placeholder_layout.addWidget(placeholder_text)
        self.placeholder_frame.setLayout(placeholder_layout)'''
        self.analysis_layout.addWidget(self.placeholder_frame)

        self.analysis_container.setLayout(self.analysis_layout)
        self.analysis_scroll.setWidget(self.analysis_container)

        right_frame = QFrame()
        right_frame.setStyleSheet("background-color: #1e1e1e; border-radius: 15px;")
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.analysis_scroll)
        right_frame.setLayout(right_layout)

        content_layout.addWidget(left_frame, 1)
        content_layout.addWidget(right_frame, 1)

        main_layout.addLayout(header_layout)
        main_layout.addLayout(content_layout)
        main_widget.setLayout(main_layout)
        return main_widget

    def analyze_images(self):
        image_paths = [img[0] for img in self.upload_widget.images]
        if not image_paths:
            return
        
        self.upload_widget.clear_images()
        
        for i in reversed(range(self.analysis_layout.count())):
            widget = self.analysis_layout.itemAt(i).widget()
            if widget and widget != self.analysis_title:
                widget.deleteLater()

        IMAGE_PROCESSOR.initialize_images(image_paths) 
        analysis_data = IMAGE_PROCESSOR.turn_to_llm()

        self.render_analysis(analysis_data)
    
    def render_analysis(self, data):
        # 1. Основная информация
        main_card = self.create_card("Основная информация", [
            f"Название: {data['name'] if data['name'] != 'N/A' else 'Информация не найдена'}",
            f"Категория: {data['category'] if data['category'] != 'N/A' else 'Информация не найдена'}",
        ])
        self.analysis_layout.addWidget(main_card)

        # ✅ 2. Новый блок: Сравнение с требованиями ВОЗ
        comparison_data = data.get("comparison", {})
        if comparison_data:
            comp_frame = QFrame()
            comp_frame.setStyleSheet("background-color: #2d2d2d; border-radius: 12px; padding: 10px;")
            comp_layout = QVBoxLayout()
            comp_title = QLabel("Сравнение с требованиями ВОЗ")
            comp_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFD700; margin-bottom: 8px;")
            comp_layout.addWidget(comp_title)

            for key, value in comparison_data.items():
                title = COMPARISON_LABELS.get(key, key)
                comp_layout.addWidget(self.create_comparison_block(title, value))

            comp_frame.setLayout(comp_layout)
            self.analysis_layout.addWidget(comp_frame)

        # 3. Характеристики
        characteristics = data.get("characteristics", {})
        char_items = [
            f"Энергетическая ценность: {self.check_value(characteristics.get('energy_value'))}",
            f"Натрий: {self.check_value(characteristics.get('sodium'))}",
            f"Общий сахар: {self.check_value(characteristics.get('total_sugar'))}",
            f"Свободный сахар: {self.check_value(characteristics.get('free_sugar'))}",
            f"Белки: {self.check_value(characteristics.get('total_protein'))}",
            f"Жиры: {self.check_value(characteristics.get('total_fat'))}",
            f"Содержание фруктов: {self.check_value(characteristics.get('fruit_content'))}",
            f"Возрастная маркировка: {self.check_value(characteristics.get('age_marking'))}",
            f"Высокий сахар на упаковке: {self.check_value(characteristics.get('high_sugar_front_packaging'))}",
            f"Маркировка: {self.check_value(characteristics.get('labeling'))}",
        ]
        self.analysis_layout.addWidget(self.create_card("Характеристики", char_items))

        # 4. Дополнительно
        additional = data.get("additional_info", {})
        add_items = [
            f"Состав: {self.check_value(additional.get('containings'))}",
            f"Описание: {self.check_value(additional.get('description'))}",
            f"Адрес производителя: {self.check_value(additional.get('manufactuer_address'))}",
            f"Условия хранения: {self.check_value(additional.get('storing_conditions'))}",
        ]
        self.analysis_layout.addWidget(self.create_card("Дополнительно", add_items))

    def create_comparison_block(self, title, value):
        print(value)
        if value == "true" or value is True:
            color = "#3a7d44"
            icon = "✅"
        elif value == "false" or value is False:
            color = "#a94442"
            icon = "❌"
        else:
            color = "#6c757d"
            icon = "⚪"

        block = QFrame()
        block.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 8px;
                margin-bottom: 6px;
            }}
            QLabel {{
                color: white;
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        layout = QHBoxLayout()
        lbl = QLabel(f"{icon}  {title}")
        layout.addWidget(lbl)
        layout.setContentsMargins(6, 6, 6, 6)
        block.setLayout(layout)
        return block

    def check_value(self, value):
        return value if value != "N/A" else "Информация не найдена"
    
    def create_card(self, title, items):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-radius: 12px;
                padding: 10px;
                margin-bottom: 10px;
            }
            QLabel {
                color: white;
                font-size: 13px;
                padding: 2px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFD700;")
        layout.addWidget(title_label)

        for item in items:
            lbl = QLabel(item)
            lbl.setWordWrap(True)
            layout.addWidget(lbl)

        card.setLayout(layout)
        return card

    def create_history_screen(self):
        widget = QWidget()
        layout = QVBoxLayout()

        back_btn = QPushButton("← Назад")
        back_btn.clicked.connect(self.show_main)
        back_btn.setStyleSheet("background-color: #333; border-radius: 8px; padding: 8px; color: white;")
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()

        for i in range(5):
            card = QFrame()
            card.setStyleSheet("background-color: #2a2a2a; border-radius: 15px; padding: 15px;")
            lbl = QLabel(f"Продукт {i+1} - ⭐⭐⭐⭐☆")
            lbl.setStyleSheet("font-size: 18px; color: white;")
            card_layout = QVBoxLayout()
            card_layout.addWidget(lbl)
            card.setLayout(card_layout)
            scroll_layout.addWidget(card)

        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)

        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget

    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите изображения", "", "Images (*.png *.jpg *.jpeg)")
        for file in files:
            self.upload_widget.add_image(file)

    def show_history(self):
        self.animate_transition(self.history_screen)

    def show_main(self):
        self.animate_transition(self.stack.widget(0))

    def animate_transition(self, widget):
        self.stack.setCurrentWidget(widget)
        anim = QPropertyAnimation(widget, b"windowOpacity")
        widget.setWindowOpacity(0)
        anim.setDuration(500)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
