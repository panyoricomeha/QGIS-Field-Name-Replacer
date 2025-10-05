# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FieldNameReplacer
                                 A QGIS plugin
 Batch and manual renaming of field names and aliases (display names)
                              -------------------
        begin                : 2025-10-05
        author               : rikuto arita
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QObject, QTranslator, QCoreApplication, QSettings, QLocale
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox, QInputDialog
from qgis.PyQt.QtCore import QCoreApplication
import csv
import os


class FieldNameReplacer:
    def __init__(self, iface):
        self.iface = iface
        self.actions = []
        self.translator = None
        self.load_translation()

    def tr(self, message):
        """翻訳ヘルパー"""
        return QCoreApplication.translate("FieldNameReplacer", message)

    def load_translation(self):
        import os
        from qgis.PyQt.QtCore import QTranslator, QLocale
        locale = QLocale.system().name()
        plugin_dir = os.path.dirname(__file__)
        i18n_path = os.path.join(plugin_dir, "i18n", f"FieldNameReplacer_{locale}.qm")
        if os.path.exists(i18n_path):
            self.translator = QTranslator()
            self.translator.load(i18n_path)
            QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        self.add_action(self.tr("Set alias manually"), self.set_alias_manually)
        self.add_action(self.tr("Batch set aliases (CSV)"), self.set_alias_from_file)
        self.add_action(self.tr("Rename field manually"), self.rename_field_manually)
        self.add_action(self.tr("Batch rename fields (CSV)"), self.rename_field_from_file)

    def add_action(self, text, callback):
        action = QAction(text, self.iface.mainWindow())
        action.triggered.connect(callback)
        self.iface.addPluginToMenu(self.tr("Field Tools"), action)
        self.actions.append(action)

    def unload(self):
        for act in self.actions:
            self.iface.removePluginMenu(self.tr("Field Tools"), act)

    def set_alias_from_file(self):
        layer = self.iface.activeLayer()
        if not layer:
            QMessageBox.warning(self.iface.mainWindow(), self.tr("Error"), self.tr("No active layer found."))
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(),
            self.tr("Select CSV file for alias settings"),
            "",
            "CSV Files (*.csv *.txt);;All Files (*)"
        )
        if not file_path:
            return

        alias_rules = self.read_csv_rules(file_path)
        if not alias_rules:
            return

        updated_count = 0
        field_names = [f.name() for f in layer.fields()]

        for old_name, alias in alias_rules.items():
            if old_name in field_names:
                idx = layer.fields().indexOf(old_name)
                layer.setFieldAlias(idx, alias)
                updated_count += 1

        layer.triggerRepaint()
        QMessageBox.information(
            self.iface.mainWindow(),
            self.tr("Completed"),
            self.tr("{} field aliases have been set.").format(updated_count)
        )

    def set_alias_manually(self):
        layer = self.iface.activeLayer()
        if not layer:
            QMessageBox.warning(self.iface.mainWindow(), self.tr("Error"), self.tr("No active layer found."))
            return

        fields = [f.name() for f in layer.fields()]
        if not fields:
            QMessageBox.warning(self.iface.mainWindow(), self.tr("Error"), self.tr("This layer has no fields."))
            return

        old_name, ok = QInputDialog.getItem(
            self.iface.mainWindow(),
            self.tr("Select Field"),
            self.tr("Select the field to set an alias for:"),
            fields, 0, False
        )
        if not ok or not old_name:
            return

        new_alias, ok2 = QInputDialog.getText(
            self.iface.mainWindow(),
            self.tr("Enter Alias"),
            self.tr("Enter the new alias for the field '{}':").format(old_name)
        )
        if not ok2:
            return

        idx = layer.fields().indexOf(old_name)
        layer.setFieldAlias(idx, new_alias)
        layer.triggerRepaint()
        QMessageBox.information(
            self.iface.mainWindow(),
            self.tr("Completed"),
            self.tr("Alias for '{}' set to '{}'.").format(old_name, new_alias)
        )

    def rename_field_manually(self):
        layer = self.iface.activeLayer()
        if not layer:
            QMessageBox.warning(self.iface.mainWindow(), self.tr("Error"), self.tr("No active layer found."))
            return

        fields = [f.name() for f in layer.fields()]
        if not fields:
            QMessageBox.warning(self.iface.mainWindow(), self.tr("Error"), self.tr("This layer has no fields."))
            return

        old_name, ok = QInputDialog.getItem(
            self.iface.mainWindow(),
            self.tr("Select Field"),
            self.tr("Select the field to rename:"),
            fields, 0, False
        )
        if not ok or not old_name:
            return

        new_name, ok2 = QInputDialog.getText(
            self.iface.mainWindow(),
            self.tr("Enter New Field Name"),
            self.tr("Enter a new name for the field '{}':").format(old_name)
        )
        if not ok2 or not new_name:
            return

        try:
            layer.startEditing()
            idx = layer.fields().indexOf(old_name)
            layer.renameAttribute(idx, new_name)
            layer.commitChanges()
            layer.triggerRepaint()
            QMessageBox.information(
                self.iface.mainWindow(),
                self.tr("Completed"),
                self.tr("'{}' → '{}' renamed successfully.").format(old_name, new_name)
            )
        except Exception as e:
            layer.rollBack()
            QMessageBox.critical(
                self.iface.mainWindow(),
                self.tr("Error"),
                self.tr("Failed to rename field:\n{}").format(e)
            )

    def rename_field_from_file(self):
        layer = self.iface.activeLayer()
        if not layer:
            QMessageBox.warning(self.iface.mainWindow(), self.tr("Error"), self.tr("No active layer found."))
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(),
            self.tr("Select CSV file for field name replacements (format: old,new)"),
            "",
            "CSV Files (*.csv *.txt);;All Files (*)"
        )
        if not file_path:
            return

        replace_rules = self.read_csv_rules(file_path)
        if not replace_rules:
            return

        field_names = [f.name() for f in layer.fields()]
        changed = 0

        layer.startEditing()
        for old, new in replace_rules.items():
            if old in field_names:
                idx = layer.fields().indexOf(old)
                layer.renameAttribute(idx, new)
                changed += 1
        layer.commitChanges()
        layer.triggerRepaint()

        QMessageBox.information(
            self.iface.mainWindow(),
            self.tr("Completed"),
            self.tr("{} field names were renamed.").format(changed)
        )

    def read_csv_rules(self, file_path):
        if not os.path.exists(file_path):
            QMessageBox.warning(self.iface.mainWindow(), self.tr("Error"),
                                self.tr("File does not exist:\n{}").format(file_path))
            return None

        rules = {}
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        rules[row[0].strip()] = row[1].strip()
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), self.tr("Read Error"),
                                 self.tr("Failed to read CSV file.\n{}").format(e))
            return None

        if not rules:
            QMessageBox.warning(self.iface.mainWindow(), self.tr("Error"),
                                self.tr("No valid data found in CSV file."))
            return None

        return rules
