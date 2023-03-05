# -*- coding: utf-8 -*-
# author:yangtao
# time: 2022/03/21

import collections
import os
import pprint

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui

import maya.cmds as cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

import config


class MessageBox(QtWidgets.QMessageBox):
    def __init__(self, parent=None):
        super(MessageBox, self).__init__(parent=parent)


class ListDialog(QtWidgets.QDialog):
    selection_changed = QtCore.Signal(list)

    def __init__(self, parent):
        super(ListDialog, self).__init__(parent=parent)
        self.__init_ui()
        self.__init_connect()

    def __init_ui(self):
        self.setWindowTitle(u"Object List")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)  # 隐藏帮助标识

        self.objects_list = QtWidgets.QListWidget()
        self.objects_list.setMinimumSize(300, 300)
        self.objects_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.objects_list)

    def __init_connect(self):
        self.objects_list.itemSelectionChanged.connect(lambda: self.selection_changed.emit(self.get_selection_list()))

    def get_selection_list(self):
        selectedItems = self.objects_list.selectedItems()
        if selectedItems:
            return [item.name for item in selectedItems]
        else:
            return []

    def clear(self):
        self.objects_list.clear()

    def add_items(self, name_list):
        self.objects_list.clear()

        for name in name_list:
            list_item = QtWidgets.QListWidgetItem()
            list_item.setText(name.split("|")[-1])
            list_item.name = name
            self.objects_list.addItem(list_item)


class FixButton(QtWidgets.QPushButton):
    button_clicked = QtCore.Signal(QtWidgets.QPushButton)

    def __init__(self, **kwargs):
        super(FixButton, self).__init__()

        self.__init_attr(kwargs)
        self.__init_ui()
        self.__init_connect()

    def __init_attr(self, attr_map):
        for k, v in attr_map.items():
            setattr(self, k, v)

    def __init_ui(self):
        if self.fix_type == "prefix":
            self.setText("%s_" % self.code)
        elif self.fix_type == "suffix":
            self.setText("_%s" % self.code)

        # if self.name == "group":
        #     self.setStyleSheet("QPushButton{background: CornflowerBlue;font-weight:bold;font-size:15px}")
        # else:
        #     self.setStyleSheet("QPushButton{font-weight:bold;font-size:15px}")
        self.setStyleSheet("QPushButton{font-weight:bold;font-size:15px}")
        self.setMinimumWidth(40)

        self.setToolTip(self.description)

    def __init_connect(self):
        self.clicked.connect(lambda: self.button_clicked.emit(self))


class FixTabWidget(QtWidgets.QWidget):
    fix_button_clicked = QtCore.Signal(FixButton)

    def __init__(self):
        super(FixTabWidget, self).__init__()
        self.__init_ui()
        self.__init_style()

    def __init_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)

        # 将后缀前缀添加到主UI里
        group_items = collections.OrderedDict()  # 根据 group 项将项目分类
        for item in config.FIX_ITEMS:
            group_name = u"%s" % item.get("group")
            if group_name in group_items:
                group_items[group_name].append(item)
            else:
                group_items[group_name] = [item]

        # group_items 值类似
        # {u'方位标识': [{'code': 'geo',
        #             'description': 几何体,
        #             'name': 'geometry',
        #             'type': 'suffix'}],
        #  u'类型标识': [{'code': 'l',
        #             'description': u'左',
        #             'group': u'方位标识',
        #             'name': 'left',
        #             'type': 'suffix'},
        #            {'code': 'c',
        #             'description': u'中',
        #             'group': u'方位标识',
        #             'name': 'right',
        #             'type': 'suffix'}]}

        for group_name, items_list in group_items.items():
            button_group_layout = QtWidgets.QGridLayout()  # 按钮布局

            col = 1
            row = 1
            for item_value in items_list:
                # 添加到按钮布局
                fix_button = FixButton(**item_value)
                button_group_layout.addWidget(fix_button, row, col)
                # 连接信号
                fix_button.button_clicked.connect(self.fix_button_clicked)

                if col > 4:
                    row += 1
                    col = 1
                else:
                    col += 1

            # 布局分隔
            group_box = QtWidgets.QGroupBox(group_name)
            group_box.setLayout(button_group_layout)
            self.main_layout.addWidget(group_box)


        # 删除按钮
        self.remove_prefix_button = QtWidgets.QPushButton(u"删除 前缀_")
        self.remove_suffix_button = QtWidgets.QPushButton(u"删除 _后缀")
        self.revoke_button = QtWidgets.QPushButton(u"<< 撤销")
        # 删除按钮横向布局
        self.remove_button_layout = QtWidgets.QHBoxLayout()
        self.remove_button_layout.addWidget(self.remove_prefix_button)
        self.remove_button_layout.addWidget(self.remove_suffix_button)
        self.remove_button_layout.addWidget(self.revoke_button)

        # 智能添加前后缀
        self.smart_fix_button = QtWidgets.QPushButton(u"智能添加前后缀")

        self.main_layout.addLayout(self.remove_button_layout)
        self.main_layout.addWidget(self.smart_fix_button)
        self.main_layout.addStretch()

    def __init_style(self):
        purple_button_style = "QPushButton{background:MediumPurple;font-weight:bold;font-size:12px}"
        self.remove_prefix_button.setStyleSheet(purple_button_style)
        self.remove_suffix_button.setStyleSheet(purple_button_style)

        self.smart_fix_button.setStyleSheet("QPushButton{background:DodgerBlue;font-weight:bold;font-size:12px}")
        self.revoke_button.setStyleSheet("QPushButton{background:MediumSeaGreen;font-weight:bold;font-size:18px}")


class ReanmeTabWidget(QtWidgets.QWidget):
    def __init__(self):
        super(ReanmeTabWidget, self).__init__()
        self.__init_ui()
        self.__init_style()

    def __init_ui(self):
        # 查重
        self.find_duplicates_button = QtWidgets.QPushButton(u"查找重复命名")

        # 名称修改
        self.rename_line_edit = QtWidgets.QLineEdit()
        self.rename_line_edit.setPlaceholderText(u"重命名选中项")
        # 重命名执行按钮
        self.go_rename_button = QtWidgets.QPushButton(u"重命名")
        # rename layout
        self.rename_layout = QtWidgets.QHBoxLayout()
        self.rename_layout.addWidget(self.rename_line_edit)
        self.rename_layout.addWidget(self.go_rename_button)
        self.rename_layout.setSpacing(5)

        # 字段替换
        self.replace_line_edit = QtWidgets.QLineEdit()
        self.replace_line_edit.setPlaceholderText(u"替换选中项字段")
        self.replace_with_line_edit = QtWidgets.QLineEdit()
        self.replace_with_line_edit.setPlaceholderText(u"替换为")
        # 重命名执行按钮
        self.go_replace_button = QtWidgets.QPushButton(u"执行\n替换")
        self.go_replace_button.setMinimumSize(56, 68)
        # line edit layout
        self.line_edit_layout = QtWidgets.QVBoxLayout()
        self.line_edit_layout.addWidget(self.replace_line_edit)
        self.line_edit_layout.addWidget(self.replace_with_line_edit)
        # rename layout
        self.replace_layout = QtWidgets.QHBoxLayout()
        self.replace_layout.addLayout(self.line_edit_layout)
        self.replace_layout.addWidget(self.go_replace_button)
        self.replace_layout.setSpacing(5)

        self.revoke_button = QtWidgets.QPushButton(u"<< 撤销")

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.find_duplicates_button)
        self.main_layout.addLayout(self.rename_layout)
        self.main_layout.addLayout(self.replace_layout)
        self.main_layout.addWidget(self.revoke_button)
        self.main_layout.addStretch()

    def __init_style(self):
        line_edit_font = QtWidgets.QLineEdit().font()
        line_edit_font.setPointSize(15)
        line_edit_font.setBold(True)
        self.rename_line_edit.setFont(line_edit_font)
        self.replace_line_edit.setFont(line_edit_font)
        self.replace_with_line_edit.setFont(line_edit_font)

        bold_button_style = "QPushButton{font-weight:bold;font-size:15px}"
        self.go_rename_button.setStyleSheet(bold_button_style)
        self.go_replace_button.setStyleSheet(bold_button_style)
        self.revoke_button.setStyleSheet("QPushButton{background:MediumSeaGreen;font-weight:bold;font-size:18px}")

        self.find_duplicates_button.setStyleSheet("QPushButton{font-weight:bold;font-size:18px}")


class HierarchyButton(QtWidgets.QPushButton):
    button_clicked = QtCore.Signal(QtWidgets.QPushButton)

    def __init__(self):
        super(HierarchyButton, self).__init__()
        self.name = ""
        self.clicked.connect(lambda: self.button_clicked.emit(self))


class OutlineEditorTabWidget(QtWidgets.QWidget):
    hierarchy_button_clicked = QtCore.Signal(QtWidgets.QPushButton)

    def __init__(self):
        super(OutlineEditorTabWidget, self).__init__()
        self.__init_ui()
        self.__init_style()

    def __init_ui(self):
        # 排序按钮
        self.move_up_button = QtWidgets.QPushButton(u"↑ 向上")
        self.move_down_button = QtWidgets.QPushButton(u"↓ 向下")
        self.auto_sorted_button = QtWidgets.QPushButton(u"自动排序")
        # 排序布局
        sorted_layout = QtWidgets.QHBoxLayout()
        sorted_layout.addWidget(self.move_up_button)
        sorted_layout.addWidget(self.move_down_button)
        sorted_layout.addWidget(self.auto_sorted_button)
        sorted_group_box = QtWidgets.QGroupBox(u"大纲排序")
        sorted_group_box.setLayout(sorted_layout)

        # 创建层级文件夹按钮
        hierarchy_buttons_layout = self.__hierarchy_buttons_layout()
        self.create_group_box = QtWidgets.QGroupBox(u"创建大纲层级组")
        self.create_group_box.setLayout(hierarchy_buttons_layout)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(sorted_group_box)
        self.main_layout.addWidget(self.create_group_box)
        self.main_layout.addStretch()

    def __init_style(self):
        purple_button_style = "QPushButton{background:MediumPurple;font-weight:bold;font-size:12px}"
        self.move_up_button.setStyleSheet(purple_button_style)
        self.move_down_button.setStyleSheet(purple_button_style)
        self.auto_sorted_button.setStyleSheet("QPushButton{background:DodgerBlue;font-weight:bold;font-size:12px}")
        self.create_group_box.setStyleSheet("QPushButton{background:DodgerBlue;font-weight:bold;font-size:12px}")

    def __hierarchy_buttons_layout(self):
        hierarchy_items_layout = QtWidgets.QVBoxLayout()
        for item_name in config.OUTLINE_HIERARACHY:
            hierarchy_button = HierarchyButton()
            hierarchy_button.setText(item_name.split("|")[-1])
            hierarchy_button.setToolTip(u"父级：%s" % item_name.split("|")[0])
            hierarchy_button.name = item_name
            hierarchy_button.button_clicked.connect(self.hierarchy_button_clicked.emit)
            hierarchy_items_layout.addWidget(hierarchy_button)
        return hierarchy_items_layout


class MainUI(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    OBJECT_NAME = "Rename Tool"

    def __init__(self):
        super(MainUI, self).__init__()
        # 手动设置 object name，再开始时删除它, 防止窗口打开多个窗口
        try:
            cmds.deleteUI(u"{0}WorkspaceControl".format(self.OBJECT_NAME))
        except:
            pass
        self.setObjectName(self.OBJECT_NAME)

        self.__init_ui()
        self.__init_style()

    def __init_ui(self):
        # 搜索布局
        self.search_edit_line = QtWidgets.QLineEdit()
        self.search_edit_line.setMinimumHeight(30)
        self.search_edit_line.setPlaceholderText(u"使用'*'作为通配符")
        self.search_button = QtWidgets.QPushButton(u"搜索")
        self.search_layout = QtWidgets.QHBoxLayout()
        self.search_layout.addWidget(self.search_edit_line)
        self.search_layout.addWidget(self.search_button)
        self.search_layout.setSpacing(5)
        # 搜索弹窗
        self.objects_list_dialog = ListDialog(self)

        self.fix_widget = FixTabWidget()  # 前后缀
        self.rename_widget = ReanmeTabWidget()  # 重命名
        self.outline_editor = OutlineEditorTabWidget()  # 大纲编辑器

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.search_layout)
        tab_widget = QtWidgets.QTabWidget()
        tab_widget.addTab(self.fix_widget, u"添加前后缀")
        tab_widget.addTab(self.rename_widget, u"重命名与替换")
        tab_widget.addTab(self.outline_editor, u"大纲编辑")
        self.main_layout.addWidget(tab_widget)

    def __init_style(self):
        line_edit_font = QtWidgets.QLineEdit().font()
        line_edit_font.setPointSize(15)
        line_edit_font.setBold(True)
        self.search_edit_line.setFont(line_edit_font)
        self.search_button.setStyleSheet("QPushButton{font-weight:bold;font-size:15px}")

    def show_objects_list_dialog(self, name_list):
        self.objects_list_dialog.clear()
        self.objects_list_dialog.add_items(name_list)
        self.objects_list_dialog.show()
