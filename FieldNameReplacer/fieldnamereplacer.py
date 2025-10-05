# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FieldRename
                                 A QGIS plugin
 Batch replace field names in attribute tables
                              -------------------
        begin                : 2025-10-05
        author               : rikuto arita
 ***************************************************************************/
"""
from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QFileDialog, QMessageBox
from qgis.utils import iface
import os
import csv

class FieldNameReplacer:
    def __init__(self, iface):
        self.iface = iface
        self.action_manual = None
        self.action_file = None

    def initGui(self):
        # Create menu actions
        self.action_manual = QAction("Replace Field Name (Manual Input)", self.iface.mainWindow())
        self.action_manual.triggered.connect(self.rename_with_input)
        self.iface.addPluginToMenu("Batch Field Name Replacer", self.action_manual)

        self.action_file = QAction("Replace Field Name (From File)", self.iface.mainWindow())
        self.action_file.triggered.connect(self.rename_with_file)
        self.iface.addPluginToMenu("Batch Field Name Replacer", self.action_file)

    def unload(self):
        self.iface.removePluginMenu("Batch Field Name Replacer", self.action_manual)
        self.iface.removePluginMenu("Batch Field Name Replacer", self.action_file)

    # --- Replace field name via manual input ---
    def rename_with_input(self):
        layer = self.iface.activeLayer()
        if not layer:
            QMessageBox.warning(self.iface.mainWindow(), "Error", "No active layer found.")
            return

        old_name, ok1 = QInputDialog.getText(self.iface.mainWindow(), "Target Field", "Enter the field name to be replaced:")
        if not ok1 or not old_name:
            return

        new_name, ok2 = QInputDialog.getText(self.iface.mainWindow(), "New Field Name", "Enter the new field name:")
        if not ok2 or not new_name:
            return

        if old_name not in [f.name() for f in layer.fields()]:
            QMessageBox.warning(self.iface.mainWindow(), "Error", f"The field '{old_name}' does not exist.")
            return

        layer.startEditing()
        layer.renameAttribute(layer.fields().indexOf(old_name), new_name)
        layer.commitChanges()
        QMessageBox.information(self.iface.mainWindow(), "Done", f"The field '{old_name}' has been renamed to '{new_name}'.")

    # --- Replace field names using a CSV or text file ---
    def rename_with_file(self):
        layer = self.iface.activeLayer()
        if not layer:
            QMessageBox.warning(self.iface.mainWindow(), "Error", "No active layer found.")
            return

        file_path, _ = QFileDialog.getOpenFileName(self.iface.mainWindow(), "Select Replacement Rule File", "", "CSV/Text Files (*.csv *.txt);;All Files (*)")
        if not file_path:
            return

        if not os.path.exists(file_path):
            QMessageBox.warning(self.iface.mainWindow(), "Error", f"The file does not exist: {file_path}")
            return

        replace_rules = {}
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                old, new = row[0].strip(), row[1].strip()
                replace_rules[old] = new

        if not replace_rules:
            QMessageBox.warning(self.iface.mainWindow(), "Error", "The replacement rule file is empty.")
            return

        reply = QMessageBox.question(
            self.iface.mainWindow(),
            "Confirmation",
            f"Do you want to execute {len(replace_rules)} replacement(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        renamed_count = 0
        layer.startEditing()
        for old, new in replace_rules.items():
            if old in [f.name() for f in layer.fields()]:
                idx = layer.fields().indexOf(old)
                layer.renameAttribute(idx, new)
                renamed_count += 1
        layer.commitChanges()

        QMessageBox.information(self.iface.mainWindow(), "Completed", f"{renamed_count} field name(s) have been changed.")
