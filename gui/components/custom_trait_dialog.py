# GameMediaTool/gui/components/custom_trait_dialog.py (New File)

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QDialogButtonBox, 
                               QLabel, QLineEdit)

class CustomTraitDialog(QDialog):
    def __init__(self, initial_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Custom Trait")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        grid_layout = QGridLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Display Name (e.g., Super Strength)")
        grid_layout.addWidget(QLabel("Display Name:"), 0, 0)
        grid_layout.addWidget(self.name_input, 0, 1)

        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Tag Name (e.g., super_strength)")
        grid_layout.addWidget(QLabel("Tag Name:"), 1, 0)
        grid_layout.addWidget(self.tag_input, 1, 1)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("A short description for the trait")
        grid_layout.addWidget(QLabel("Description:"), 2, 0)
        grid_layout.addWidget(self.desc_input, 2, 1)

        self.mod_input = QLineEdit()
        self.mod_input.setPlaceholderText("Stats (e.g., corruption:15, arousal:0.05)")
        grid_layout.addWidget(QLabel("Modifiers:"), 3, 0)
        grid_layout.addWidget(self.mod_input, 3, 1)

        layout.addLayout(grid_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        if initial_data:
            self.name_input.setText(initial_data.get("display_name", ""))
            self.tag_input.setText(initial_data.get("tag_name", ""))
            self.desc_input.setText(initial_data.get("description", ""))
            self.mod_input.setText(initial_data.get("modifiers_str", ""))

    def get_data(self):
        """Returns the entered data as a dictionary."""
        display_name = self.name_input.text().strip()
        tag_name = self.tag_input.text().strip()
        if not display_name or not tag_name:
            return None # Basic validation

        return {
            "display_name": display_name,
            "tag_name": tag_name,
            "description": self.desc_input.text().strip(),
            "modifiers_str": self.mod_input.text().strip()
        }