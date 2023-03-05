# -*- coding: utf-8 -*-
# author:yangtao
# time: 2022/03/21

__version__ = "4.0"

from . import ui
from . import core


class MainWindow(ui.MainUI):
    INSTANCE = None
    OBJECT_NAME = "Rename Tool"

    def __init__(self):
        super(MainWindow, self).__init__()
        self.objects_namer = core.Namer()

        self.setWindowTitle("%s - %s" % (self.OBJECT_NAME, __version__))
        self.__init_connect()

    def __init_connect(self):
        # 搜索框
        self.search_button.clicked.connect(self.search)
        self.objects_list_dialog.selection_changed.connect(core.select_and_fit_objests)

        # 添加前后缀
        self.fix_widget.fix_button_clicked.connect(lambda fix_button:
                                                   self.objects_namer.add_fix(fix_type=fix_button.fix_type,
                                                                              code=fix_button.code)
                                                   )
        self.fix_widget.smart_fix_button.clicked.connect(self.objects_namer.smart_fix)
        self.fix_widget.remove_prefix_button.clicked.connect(self.objects_namer.remove_prefix)
        self.fix_widget.remove_suffix_button.clicked.connect(self.objects_namer.remove_suffix)
        self.fix_widget.revoke_button.clicked.connect(self.objects_namer.revoke)

        # 查找重复
        self.rename_widget.find_duplicates_button.clicked.connect(lambda:
                                                                  self.show_objects_list_dialog(
                                                                      name_list=self.objects_namer.find_duplicates())
                                                                  )

        # 重命名与替换
        self.rename_widget.go_rename_button.clicked.connect(lambda:
                                                            self.objects_namer.rename(
                                                                self.rename_widget.rename_line_edit.text())
                                                            )
        self.rename_widget.revoke_button.clicked.connect(self.objects_namer.revoke)
        self.rename_widget.go_replace_button.clicked.connect(lambda:
                                                             self.objects_namer.repalce(
                                                                 self.rename_widget.replace_line_edit.text(),
                                                                 self.rename_widget.replace_with_line_edit.text())
                                                             )

        # 大纲编辑
        self.outline_editor.move_up_button.clicked.connect(lambda:
                                                           core.selection_reorder(-1))
        self.outline_editor.move_down_button.clicked.connect(lambda:
                                                             core.selection_reorder(1))
        self.outline_editor.auto_sorted_button.clicked.connect(lambda:
                                                               core.selection_auto_reorder())
        self.outline_editor.hierarchy_button_clicked.connect(self.create_hierarchy_group)

    def create_hierarchy_group(self, button):
        core.create_hierarchy(hierarchy_name=button.name)

    def search(self):
        self.objects_namer.ls_objects(self.search_edit_line.text())
        long_name_list = self.objects_namer.objects_long_name_map.keys()
        if long_name_list:
            self.show_objects_list_dialog(name_list=long_name_list)
        else:
            ui.MessageBox.warning(self, u"未找到对象",
                                  u"未找到对象\n"
                                  u"可以尝试添加通配符“ * ”来获取更多结果\n"
                                  u"例如：*cat*")


def show():
    MainWindow.INSTANCE = MainWindow()
    MainWindow.INSTANCE.show()
