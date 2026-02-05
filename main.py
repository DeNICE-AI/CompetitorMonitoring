import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from PyQt6 import QtCore, QtGui, QtWidgets

APP_ROOT = Path(__file__).resolve().parent


def _sanitize_sys_path() -> None:
    app_root = str(APP_ROOT)
    sanitized = []
    for entry in sys.path:
        if not entry:
            continue
        if "Проект fastapi" in entry and entry != app_root:
            continue
        sanitized.append(entry)
    if app_root not in sanitized:
        sanitized.insert(0, app_root)
    sys.path = sanitized


_sanitize_sys_path()

from desktop_app.backend import BackendServer


@dataclass
class AnalyzeSelection:
    text: bool
    image: bool
    pdf: bool


class AnalyzeWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal(dict)
    error = QtCore.pyqtSignal(str)

    def __init__(
        self,
        base_url: str,
        selection: AnalyzeSelection,
        text: str,
        image_path: Optional[str],
        pdf_path: Optional[str],
    ) -> None:
        super().__init__()
        self._base_url = base_url
        self._selection = selection
        self._text = text
        self._image_path = image_path
        self._pdf_path = pdf_path

    def run(self) -> None:
        responses: Dict[str, Any] = {}
        try:
            if self._selection.text:
                responses["text"] = self._analyze_text(self._text)
            if self._selection.image:
                responses["image"] = self._analyze_image(self._image_path)
            if self._selection.pdf:
                responses["pdf"] = self._ocr_pdf(self._pdf_path)
            self.finished.emit(responses)
        except Exception as exc:
            self.error.emit(str(exc))

    def _analyze_text(self, text: str) -> Dict[str, Any]:
        resp = requests.post(
            f"{self._base_url}/analyze_text",
            json={"text": text},
            timeout=60,
        )
        data = resp.json()
        if not resp.ok:
            raise RuntimeError(data.get("detail") or "Ошибка анализа текста")
        return data

    def _analyze_image(self, path: Optional[str]) -> Dict[str, Any]:
        if not path:
            raise RuntimeError("Не выбрано изображение")
        with open(path, "rb") as handle:
            resp = requests.post(
                f"{self._base_url}/analyze_image",
                files={"file": handle},
                timeout=120,
            )
        data = resp.json()
        if not resp.ok:
            raise RuntimeError(data.get("detail") or "Ошибка анализа изображения")
        return data

    def _ocr_pdf(self, path: Optional[str]) -> Dict[str, Any]:
        if not path:
            raise RuntimeError("Не выбран PDF")
        with open(path, "rb") as handle:
            resp = requests.post(
                f"{self._base_url}/ocr_pdf",
                files={"file": handle},
                timeout=120,
            )
        data = resp.json()
        if not resp.ok:
            raise RuntimeError(data.get("detail") or "Ошибка OCR PDF")
        return data


class ParseWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal(dict)
    error = QtCore.pyqtSignal(str)

    def __init__(self, base_url: str, url: str) -> None:
        super().__init__()
        self._base_url = base_url
        self._url = url

    def run(self) -> None:
        try:
            resp = requests.post(
                f"{self._base_url}/parse_demo",
                json={"url": self._url},
                timeout=120,
            )
            data = resp.json()
            if not resp.ok:
                raise RuntimeError(data.get("detail") or "Ошибка парсинга")
            self.finished.emit({"parse_demo": data})
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, backend: BackendServer) -> None:
        super().__init__()
        self._backend = backend
        self._threads: List[QtCore.QThread] = []
        self._workers: List[QtCore.QObject] = []
        self.setWindowTitle("Competitor Monitoring Assistant")
        self.setMinimumSize(960, 720)
        self._init_ui()

    def _init_ui(self) -> None:
        root = QtWidgets.QWidget()
        root_layout = QtWidgets.QVBoxLayout(root)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        header = QtWidgets.QLabel("Ассистент “Мониторинг конкурентов”")
        header.setObjectName("HeaderTitle")
        subtitle = QtWidgets.QLabel("Выберите тип анализа и загрузите данные.")
        subtitle.setObjectName("HeaderSubtitle")
        root_layout.addWidget(header)
        root_layout.addWidget(subtitle)

        selection_panel = self._build_selection_panel()
        root_layout.addWidget(selection_panel)

        parse_panel = self._build_parse_panel()
        root_layout.addWidget(parse_panel)

        result_panel = self._build_result_panel()
        root_layout.addWidget(result_panel, 1)

        self.setCentralWidget(root)
        self._apply_styles()

    def _build_selection_panel(self) -> QtWidgets.QWidget:
        panel = self._card_container()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        toggles = QtWidgets.QHBoxLayout()
        self.toggle_text = QtWidgets.QCheckBox("Текст")
        self.toggle_text.setChecked(True)
        self.toggle_image = QtWidgets.QCheckBox("Изображение")
        self.toggle_pdf = QtWidgets.QCheckBox("PDF (OCR)")
        toggles.addWidget(self.toggle_text)
        toggles.addWidget(self.toggle_image)
        toggles.addWidget(self.toggle_pdf)
        toggles.addStretch(1)
        layout.addLayout(toggles)

        self.text_group = self._build_text_group()
        self.image_group = self._build_image_input_group()
        self.pdf_group = self._build_pdf_group()
        layout.addWidget(self.text_group)
        layout.addWidget(self.image_group)
        layout.addWidget(self.pdf_group)

        self.toggle_text.toggled.connect(self._update_visibility)
        self.toggle_image.toggled.connect(self._update_visibility)
        self.toggle_pdf.toggled.connect(self._update_visibility)
        self._update_visibility()

        self.analyze_btn = QtWidgets.QPushButton("Запустить анализ")
        self.analyze_btn.clicked.connect(self._start_analysis)
        layout.addWidget(self.analyze_btn)
        return panel

    def _build_text_group(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        label = QtWidgets.QLabel("Текст конкурента")
        self.text_input = QtWidgets.QTextEdit()
        self.text_input.setPlaceholderText("Введите текст")
        self.text_input.setMinimumHeight(120)
        layout.addWidget(label)
        layout.addWidget(self.text_input)
        return widget

    def _build_image_input_group(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        label = QtWidgets.QLabel("Изображение")
        self.image_path = QtWidgets.QLineEdit()
        self.image_path.setReadOnly(True)
        btn = QtWidgets.QPushButton("Выбрать")
        btn.clicked.connect(self._pick_image)
        layout.addWidget(label)
        layout.addWidget(self.image_path, 1)
        layout.addWidget(btn)
        return widget

    def _build_pdf_group(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        label = QtWidgets.QLabel("PDF документ (OCR)")
        self.pdf_path = QtWidgets.QLineEdit()
        self.pdf_path.setReadOnly(True)
        btn = QtWidgets.QPushButton("Выбрать")
        btn.clicked.connect(self._pick_pdf)
        layout.addWidget(label)
        layout.addWidget(self.pdf_path, 1)
        layout.addWidget(btn)
        return widget

    def _build_parse_panel(self) -> QtWidgets.QWidget:
        panel = self._card_container()
        layout = QtWidgets.QHBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("URL для демо‑парсинга")
        self.parse_btn = QtWidgets.QPushButton("Разобрать URL")
        self.parse_btn.clicked.connect(self._start_parse)
        layout.addWidget(self.url_input, 1)
        layout.addWidget(self.parse_btn)
        return panel

    def _build_result_panel(self) -> QtWidgets.QWidget:
        panel = self._card_container()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        title = QtWidgets.QLabel("Результаты")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.result_scroll = QtWidgets.QScrollArea()
        self.result_scroll.setWidgetResizable(True)
        self.result_container = QtWidgets.QWidget()
        self.result_layout = QtWidgets.QVBoxLayout(self.result_container)
        self.result_layout.setSpacing(12)
        self.result_layout.addWidget(QtWidgets.QLabel("Ожидаю запрос..."))
        self.result_scroll.setWidget(self.result_container)
        layout.addWidget(self.result_scroll, 1)
        return panel

    def _card_container(self) -> QtWidgets.QFrame:
        panel = QtWidgets.QFrame()
        panel.setObjectName("Card")
        panel.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        return panel

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget { font-size: 13px; color: #e9edf5; }
            QMainWindow { background: #0f1115; }
            #Card { background: #171b22; border: 1px solid #262b36; border-radius: 16px; }
            QLineEdit, QTextEdit {
                background: #0f131b; border: 1px solid #2d3442; border-radius: 10px; padding: 8px;
            }
            QPushButton { background: #4f6ef7; border-radius: 10px; padding: 8px 16px; }
            QPushButton:disabled { background: #2a3242; }
            #HeaderTitle { font-size: 24px; font-weight: 600; }
            #HeaderSubtitle { color: #9aa4b2; margin-bottom: 8px; }
            #SectionTitle { font-size: 16px; font-weight: 600; }
            #ResultTitle { font-size: 15px; font-weight: 600; }
            #ResultSectionTitle { font-size: 13px; font-weight: 600; color: #c7cfdb; }
            #ResultBlock { background: #151a22; border: 1px solid #242a36; border-radius: 12px; padding: 10px; }
            """
        )

    def _update_visibility(self) -> None:
        self.text_group.setVisible(self.toggle_text.isChecked())
        self.image_group.setVisible(self.toggle_image.isChecked())
        self.pdf_group.setVisible(self.toggle_pdf.isChecked())

    def _pick_image(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg *.webp *.gif)"
        )
        if path:
            self.image_path.setText(path)

    def _pick_pdf(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Выберите PDF", "", "PDF (*.pdf)"
        )
        if path:
            self.pdf_path.setText(path)

    def _clear_results(self) -> None:
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _set_status(self, message: str) -> None:
        self._clear_results()
        self.result_layout.addWidget(QtWidgets.QLabel(message))

    def _start_analysis(self) -> None:
        selection = AnalyzeSelection(
            text=self.toggle_text.isChecked(),
            image=self.toggle_image.isChecked(),
            pdf=self.toggle_pdf.isChecked(),
        )
        if not (selection.text or selection.image or selection.pdf):
            self._show_error("Выберите хотя бы один тип анализа.")
            return

        text = self.text_input.toPlainText().strip()
        image_path = self.image_path.text().strip() or None
        pdf_path = self.pdf_path.text().strip() or None

        if selection.text and not text:
            self._show_error("Введите текст для анализа.")
            return
        if selection.image and not image_path:
            self._show_error("Загрузите изображение.")
            return
        if selection.pdf and not pdf_path:
            self._show_error("Загрузите PDF.")
            return

        self.analyze_btn.setDisabled(True)
        self._set_status("Выполняю анализ...")

        worker = AnalyzeWorker(
            self._backend.base_url,
            selection,
            text,
            image_path,
            pdf_path,
        )
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._show_analysis_result)
        worker.error.connect(self._show_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(lambda: self._forget_worker(worker))
        worker.error.connect(thread.quit)
        worker.error.connect(worker.deleteLater)
        worker.error.connect(lambda: self._forget_worker(worker))
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self.analyze_btn.setDisabled(False))
        thread.finished.connect(lambda: self._forget_thread(thread))
        self._workers.append(worker)
        self._threads.append(thread)
        thread.start()

    def _start_parse(self) -> None:
        url = self.url_input.text().strip()
        if not url:
            self._show_error("Введите URL.")
            return
        self.parse_btn.setDisabled(True)
        self._set_status("Собираю данные...")

        worker = ParseWorker(self._backend.base_url, url)
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._show_parse_result)
        worker.error.connect(self._show_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(lambda: self._forget_worker(worker))
        worker.error.connect(thread.quit)
        worker.error.connect(worker.deleteLater)
        worker.error.connect(lambda: self._forget_worker(worker))
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self.parse_btn.setDisabled(False))
        thread.finished.connect(lambda: self._forget_thread(thread))
        self._workers.append(worker)
        self._threads.append(thread)
        thread.start()

    def _forget_thread(self, thread: QtCore.QThread) -> None:
        if thread in self._threads:
            self._threads.remove(thread)

    def _forget_worker(self, worker: QtCore.QObject) -> None:
        if worker in self._workers:
            self._workers.remove(worker)

    def _show_error(self, message: str) -> None:
        self.analyze_btn.setDisabled(False)
        self.parse_btn.setDisabled(False)
        self._set_status(f"Ошибка: {message}")

    def _show_analysis_result(self, data: Dict[str, Any]) -> None:
        self._clear_results()

        if "text" in data:
            analysis = data["text"].get("analysis", {})
            self.result_layout.addWidget(self._build_category_group("Анализ текста", analysis))
        if "image" in data:
            analysis = data["image"].get("analysis", {})
            self.result_layout.addWidget(self._build_image_group("Анализ изображения", analysis))
        if "pdf" in data:
            text = data["pdf"].get("text", "")
            self.result_layout.addWidget(self._build_ocr_group("OCR PDF", text))

        self.result_layout.addStretch(1)

    def _show_parse_result(self, data: Dict[str, Any]) -> None:
        self._clear_results()
        parse = data.get("parse_demo", {})
        title = parse.get("title") or "Без названия"
        analysis = parse.get("analysis", {})
        group = self._build_category_group(title, analysis)
        self.result_layout.addWidget(group)
        self.result_layout.addStretch(1)

    def _build_category_group(self, title: str, analysis: Dict[str, Any]) -> QtWidgets.QWidget:
        wrapper = QtWidgets.QFrame()
        wrapper.setObjectName("ResultGroup")
        layout = QtWidgets.QVBoxLayout(wrapper)
        title_label = QtWidgets.QLabel(title)
        title_label.setObjectName("ResultTitle")
        layout.addWidget(title_label)

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        layout.addLayout(grid)

        categories = [
            ("strengths", "Сильные стороны"),
            ("weaknesses", "Слабые стороны"),
            ("unique_offers", "Уникальные предложения"),
            ("recommendations", "Рекомендации"),
        ]
        row = 0
        col = 0
        for key, label in categories:
            items = analysis.get(key) if isinstance(analysis, dict) else None
            if not isinstance(items, list) or not items:
                continue
            block = self._build_list_block(label, items)
            grid.addWidget(block, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
        return wrapper

    def _build_image_group(self, title: str, analysis: Dict[str, Any]) -> QtWidgets.QWidget:
        wrapper = QtWidgets.QFrame()
        wrapper.setObjectName("ResultGroup")
        layout = QtWidgets.QVBoxLayout(wrapper)
        title_label = QtWidgets.QLabel(title)
        title_label.setObjectName("ResultTitle")
        layout.addWidget(title_label)

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        layout.addLayout(grid)

        if isinstance(analysis, dict):
            if analysis.get("description"):
                grid.addWidget(
                    self._build_text_block("Описание", analysis["description"]), 0, 0
                )
            if analysis.get("insights"):
                grid.addWidget(
                    self._build_list_block("Инсайты", analysis["insights"]), 0, 1
                )
            if analysis.get("style_score") is not None:
                grid.addWidget(
                    self._build_text_block("Оценка стиля", str(analysis["style_score"])), 1, 0
                )
        return wrapper

    def _build_ocr_group(self, title: str, text: str) -> QtWidgets.QWidget:
        wrapper = QtWidgets.QFrame()
        wrapper.setObjectName("ResultGroup")
        layout = QtWidgets.QVBoxLayout(wrapper)
        title_label = QtWidgets.QLabel(title)
        title_label.setObjectName("ResultTitle")
        layout.addWidget(title_label)
        text_edit = QtWidgets.QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(text)
        text_edit.setMinimumHeight(160)
        layout.addWidget(text_edit)
        return wrapper

    def _build_list_block(self, title: str, items: List[str]) -> QtWidgets.QWidget:
        block = QtWidgets.QFrame()
        block.setObjectName("ResultBlock")
        layout = QtWidgets.QVBoxLayout(block)
        label = QtWidgets.QLabel(title)
        label.setObjectName("ResultSectionTitle")
        layout.addWidget(label)
        for item in items:
            item_label = QtWidgets.QLabel(f"• {item}")
            item_label.setWordWrap(True)
            layout.addWidget(item_label)
        return block

    def _build_text_block(self, title: str, text: str) -> QtWidgets.QWidget:
        block = QtWidgets.QFrame()
        block.setObjectName("ResultBlock")
        layout = QtWidgets.QVBoxLayout(block)
        label = QtWidgets.QLabel(title)
        label.setObjectName("ResultSectionTitle")
        layout.addWidget(label)
        text_label = QtWidgets.QLabel(text)
        text_label.setWordWrap(True)
        layout.addWidget(text_label)
        return block

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self._backend.stop()
        super().closeEvent(event)


def main() -> None:
    backend = BackendServer()
    backend.start()

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(backend)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
