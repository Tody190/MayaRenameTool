# -*- coding: utf-8 -*-
# author:yangtao
# time: 2022/03/21

import os.path
import pprint
import re
import datetime

import pymel.core as pm

import config


class ObjectNamer():
    def __init__(self, node_object):
        self.node_object = node_object
        self.back_name = self.short_name

    @property
    def long_name(self):
        return self.node_object.longName()

    @property
    def short_name(self):
        return self.node_object.shortName()

    @property
    def nano_name(self):
        return self.short_name.split("|")[-1]

    @property
    def object_type(self):
        # 判断是否为 group
        node_type = self.node_object.nodeType()
        if node_type == "transform":
            shape = self.node_object.getShape()
            if not shape:
                return "group"

            connections_list = pm.listConnections(shape)
            if connections_list:
                for node in connections_list:
                    for lgt_match_str in ["lightList"]:
                        if lgt_match_str in str(node):
                            return "light"

            shape_type = shape.nodeType()
            # for geo_match_str in ["mesh", "nurbsSurface"]:
            #     if shape_type == geo_match_str:
            #         return "geometry"
            for curve_match_str in ["nurbsCurve"]:
                if shape_type == curve_match_str:
                    return "curve"
            return shape_type
        else:
            connections_list = pm.listConnections(self.node_object)
            if connections_list:
                for node in connections_list:
                    for mat_match_str in ["ShadingGroup", "defaultShaderList"]:
                        if mat_match_str in str(node):
                            return "material"
            return node_type

    @property
    def match_name_item(self):
        """
        根据项目类型返回指定的命名类型
        Args:
            object_type:

        Returns:

        """
        for object_type_map_key in config.MATCH_TYPE_MAP.keys():  # 对应配置文件中的 match_type
            # 带有*号的使用正则表达式匹配
            if "*" in object_type_map_key:
                object_type_re_str = object_type_map_key.replace("*", "(.+)")
                if re.match(object_type_re_str, self.object_type.lower()):
                    return config.MATCH_TYPE_MAP[object_type_map_key]
            else:
                if self.object_type.lower() == object_type_map_key:
                    return config.MATCH_TYPE_MAP[object_type_map_key]

    def rename(self, new_name):
        self.node_object.rename(new_name)

    def add_prefix(self, fix_name):
        self.rename("%s_%s" % (str(fix_name), self.short_name))

    def add_suffix(self, fix_name):
        self.rename("%s_%s" % (self.short_name, str(fix_name)))

    def remove_prefix(self):
        self.rename(self.short_name.split("_", 1)[-1])

    def remove_suffix(self):
        self.rename(self.short_name.rsplit("_", 1)[0])

    def revoke(self):
        if self.back_name != self.short_name:
            self.back_name = self.short_name
            self.rename(self.back_name)

    def smart_fix(self):
        """
        智能命名
        Returns:

        """
        if self.match_name_item:
            if self.match_name_item.get("fix_type") == "prefix":
                self.rename("%s_%s" % (self.match_name_item.get("code"),
                                       self.short_name))
            elif self.match_name_item.get("fix_type") == "suffix":
                self.rename("%s_%s" % (self.short_name,
                                       self.match_name_item.get("code")))

        else:
            self.rename("%s_%s" % (self.short_name,
                                   self.object_type))

    def select(self):
        self.node_object.select()
        pm.viewFit()  # 视窗匹配
        for ul in pm.windows.getPanel(typ='outlinerPanel'):  # 找到大纲:
            pm.outlinerEditor(ul, edit=True, showSelected=True)  # 展开选中

    def replace(self, replace_field, replace_with_field):
        self.rename(self.short_name.replace(replace_field, replace_with_field))


class Namer():
    def __init__(self):
        self.objects = []
        self.objects_long_name_map = {}  # 长名映射表
        self.objects_nano_name_map = {}  # 短名映射表

    def ls_objects(self, *args, **kwargs):
        self.objects = []
        self.objects_long_name_map.clear()
        self.objects_nano_name_map.clear()

        for obj in pm.ls(*args, **kwargs):
            # 忽略 shape 节点
            if "shape" in pm.nodeType(obj, inherited=True):
                continue

            obj_namer = ObjectNamer(obj)
            self.objects.append(obj_namer)

            # 长名映射表
            self.objects_long_name_map[obj_namer.long_name] = obj_namer

            # 短名映射表
            if obj_namer.nano_name not in self.objects_nano_name_map:
                self.objects_nano_name_map[obj_namer.nano_name] = [obj_namer]
            else:
                self.objects_nano_name_map[obj_namer.nano_name].append(obj_namer)

    def rename(self, new_name):
        self.ls_objects(selection=True)
        if new_name:
            for i, obj in enumerate(self.objects):
                obj.rename(new_name + str(i + 1))

    def add_fix(self, fix_type, code):
        self.ls_objects(selection=True)
        for obj in self.objects:
            # if name == "group" and obj.object_type != "group":
            #     continue
            # elif name != "group" and obj.object_type == "group":
            #     continue
            # else:
            if fix_type == "prefix":
                obj.add_prefix(code)
            elif fix_type == "suffix":
                obj.add_suffix(code)

    def remove_prefix(self):
        self.ls_objects(selection=True)
        for obj in self.objects:
            obj.rename(obj.short_name.split("_", 1)[-1])

    def remove_suffix(self):
        self.ls_objects(selection=True)
        for obj in self.objects:
            obj.rename(obj.short_name.rsplit("_", 1)[0])

    def revoke(self):
        for obj in self.objects:
            new_name, obj.back_name = obj.back_name, obj.short_name
            obj.rename(new_name)

    def smart_fix(self):
        self.ls_objects(selection=True)
        for obj in self.objects:
            obj.smart_fix()

    def repalce(self, replace_field, replace_with_field):
        self.ls_objects(selection=True)
        for obj in self.objects:
            obj.replace(replace_field, replace_with_field)

    def find_duplicates(self):
        self.ls_objects()
        duplicates_objects_long_name = []
        for objects_list in self.objects_nano_name_map.values():
            if len(objects_list) != 1:
                for obj in objects_list:
                    duplicates_objects_long_name.append(obj.long_name)
                duplicates_objects_long_name.append("")

        return duplicates_objects_long_name


def select_and_fit_objests(obj_list):
    select_objests(obj_list)
    pm.viewFit()  # 视窗匹配


def select_objests(obj_list):
    pm.select(clear=True)

    for obj_name in obj_list:
        if obj_name:
            pm.select(obj_name, add=True)

    for ul in pm.windows.getPanel(typ='outlinerPanel'):  # 找到大纲:
        pm.outlinerEditor(ul, edit=True, showSelected=True)  # 展开选中


def selection_reorder(relative):
    """
    移动选中项
    Args:
        relative:

    Returns:

    """
    pm.reorder(pm.ls(selection=True), relative=relative)


def selection_auto_reorder():
    selection_objects_long_name_list = []  # 获取所有选中的项目
    for selection in pm.ls(selection=True):
        selection_objects_long_name_list.append(selection.longName())

    # 清理选择
    pm.select(clear=True)

    # 将同父级的项放到一个字典的value里
    same_parent_objects_map = {}
    for obj_long_name in selection_objects_long_name_list:
        parent = obj_long_name.rsplit("|", 1)[0]  # 获取父级
        if not parent:
            parent = "|"
        if parent not in same_parent_objects_map:
            same_parent_objects_map[parent] = [obj_long_name]
        else:
            same_parent_objects_map[parent].append(obj_long_name)

    # 将当前项与下一个项放到同一个列表进行正向排序
    # 如果成功排序，将原始列表两个项目交换
    # 同时，大纲内，将当前项目下移一位
    # 冒泡排序
    for same_parent_objects in same_parent_objects_map.values():  # 依次处理同父级的物体
        max_index = len(same_parent_objects) - 1
        finish = False
        while not finish:
            finish = True
            for i, current_object in enumerate(same_parent_objects):
                if i == max_index:  # 当迭代到最后一个时，跳出循环
                    break
                next_object = same_parent_objects[i + 1]

                # 两两排序，如果发生顺序变化，调换两个位置，将索引值比较大向后排
                temp_sorted_list = sorted([current_object, next_object])
                if temp_sorted_list[0] == next_object:  # 查看是否调换了顺序
                    same_parent_objects[i] = next_object
                    same_parent_objects[i + 1] = current_object
                    pm.reorder(current_object, relative=1)
                    finish = False

        for obj_name in same_parent_objects:
            pm.select(obj_name, add=True)


def create_hierarchy(hierarchy_name):
    hierarchy = ""
    for group_name in hierarchy_name.split("|"):
        if not pm.ls("%s|%s" % (hierarchy, group_name)):
            if hierarchy:
                obj = pm.group(name=group_name, em=True, parent=hierarchy)
            else:
                obj = pm.group(name=group_name, em=True)

            obj.useOutlinerColor.set(True)
            obj.outlinerColorR.set(0.0)
            obj.outlinerColorG.set(1.0)
            obj.outlinerColorB.set(1.0)

        hierarchy += "|%s" % group_name

    for selection in pm.ls(selection=True):
        try:
            pm.parent(selection.longName(), hierarchy)
        except:
            pass
    pm.select(clear=True)
