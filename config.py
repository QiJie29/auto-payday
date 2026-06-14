from bilibili_api import Credential

import json

def load_json_config(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_value_by_key_recursive(data,search_key, search_value, target_key, default=None):
    """
    递归搜索：通过键值对查找目标值（支持多层嵌套）
    data: JSON 数据（可以是字典、列表或嵌套结构）
    search_key: 搜索的键名
    search_value: 搜索的值
    target_key: 要获取的目标键名
    default: 未找到时的默认值
    """

    def search(obj):
        if isinstance(obj, dict):
            # 检查当前字典是否匹配
            if search_key in obj and obj[search_key] == search_value:
                return obj.get(target_key, default)

            # 递归搜索字典的每个值
            for value in obj.values():
                result = search(value)
                if result is not None:
                    return result

        elif isinstance(obj, list):
            # 递归搜索列表的每个元素
            for item in obj:
                result = search(item)
                if result is not None:
                    return result

        return None

    result = search(data)
    return result if result is not None else default