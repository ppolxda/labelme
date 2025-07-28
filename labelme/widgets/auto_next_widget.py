from PyQt5 import QtCore
from PyQt5 import QtWidgets


class AutoNextWidget(QtWidgets.QWidget):
    def __init__(self, on_submit, default_interval=1, parent=None):
        super().__init__(parent=parent)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setSpacing(0)  # type: ignore[union-attr]

        # 新增：自动切换间隔参数
        self._default_interval = default_interval
        self._interval_widget = _NextIntervalWidget(self._default_interval, parent=self)
        self._interval_widget.setMaximumWidth(400)
        self.layout().addWidget(self._interval_widget)  # type: ignore[union-attr]

        # 按钮事件处理
        self._is_running = False
        self.submit_button = QtWidgets.QPushButton(text="Auto Next Image", parent=self)
        self.submit_button.clicked.connect(self._onSubmitClicked)
        self.submit_button.setDisabled(True)
        self.layout().addWidget(self.submit_button)  # type: ignore[union-attr]
        self._on_submit_callback = on_submit

        # 新增：定时器
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._onTimerTimeout)

    def setDisabled(self, disabled: bool):
        self.submit_button.setDisabled(disabled)

    def setEnabled(self, enabled: bool):
        self.submit_button.setEnabled(enabled)

    def start(self):
        if self._is_running:
            return

        self._is_running = True
        self.submit_button.setText("Stop")
        interval = self.getAutoNextInterval()
        self._timer.start(interval * 1000)
        self._interval_widget.setDisabled(True)

    def stop(self):
        if not self._is_running:
            return

        self._timer.stop()
        self._is_running = False
        self.submit_button.setText("Auto Next Image")
        self._interval_widget.setDisabled(False)

    def _onSubmitClicked(self):
        if self._is_running:
            self.stop()
        else:
            self.start()

    def _onTimerTimeout(self):
        if self._on_submit_callback:
            self._on_submit_callback()

        # # 重新设置定时器间隔（如果用户修改了间隔）
        # interval = self.getAutoNextInterval()
        # self._timer.start(interval * 1000)

    def getAutoNextInterval(self) -> float:
        """获取自动切换间隔（秒）"""
        return int(self._interval_widget.getValue())


class _NextIntervalWidget(QtWidgets.QWidget):
    def __init__(self, default_interval: float = 2.0, parent=None):
        super().__init__(parent=parent)

        self.default_interval = default_interval
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)  # type: ignore[union-attr]

        label = QtWidgets.QLabel(self.tr("Interval(s)"))
        self.layout().addWidget(label)  # type: ignore[union-attr]

        self._interval_spin = QtWidgets.QDoubleSpinBox()
        self._interval_spin.setRange(0.1, 60)
        self._interval_spin.setSingleStep(0.1)
        self._interval_spin.setValue(self.default_interval)
        self.layout().addWidget(self._interval_spin)  # type: ignore[union-attr]

    def getValue(self) -> float:
        return self._interval_spin.value()
