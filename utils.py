import json
import logging
import os
import subprocess
from pathlib import Path


# 读取login文件
def load_json_config(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 根据关键字段查找同层级下的某个数据
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

# 将录制斗鱼直播的xml文件转为ass文件，其他平台的xml文件暂未测试
def parse_douyu_danmaku(xml_url: str):
    config = load_json_config('config.json')
    danmakuFactory_path = config['DanmakuFactory_url']
    ass_url = os.path.splitext(xml_url)[0] + '.ass'
    # 如果ass文件已经存在则删除重新生成
    if os.path.isfile(ass_url):
        os.remove(ass_url)

    cmd = f'"{danmakuFactory_path}" -o "{ass_url}" -i "{xml_url}"'
    subprocess.run(cmd, shell=True, check=True)
    return ass_url

# 将弹幕压制到视频中
def press_danmu_to_video(video_url: str,ass_url: str):
    video_danmu_url = os.path.splitext(video_url)[0] + '弹幕版' + os.path.splitext(video_url)[1]

    work_dir = Path(video_url).parent
    original_dir = os.getcwd()
    try:
        os.chdir(work_dir)
        # 相对路径（仅文件名，不含目录）
        video_name = Path(video_url).name
        ass_name = Path(ass_url).name
        output_name = Path(video_danmu_url).name
        cmd = f'ffmpeg -i "{video_name}" -vf "ass={ass_name}" -c:a copy "{output_name}"'
        # cmd = f'ffmpeg -i "{video_name}" -vf "subtitles={ass_name}:force_style=FontName=Segoe UI Emoji" -c:a copy "{output_name}"'
        subprocess.run(cmd, shell=True, check=True)
        logging.info(f"弹幕压制成功: {video_danmu_url}")
        return video_danmu_url
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg 执行失败: {e}")
    finally:
        os.chdir(original_dir)  # 恢复原工作目录


# 根据关键字删除某个路径下的所有文件
def delete_files_containing_keyword(directory, keyword, recursive=False, dry_run=True):
    """
    删除目录下文件名包含指定关键字的文件。

    参数:
        directory (str): 要清理的目录路径
        keyword (str): 文件名需要包含的关键字
        recursive (bool): 是否递归子目录，默认 False
        dry_run (bool): 是否仅模拟运行（不实际删除），默认 True
    """
    path = Path(directory).resolve()
    if not path.exists():
        print(f"错误：路径不存在 - {path}")
        return

    deleted_count = 0
    # 决定遍历模式：glob 或 rglob
    if recursive:
        iterator = path.rglob("*")   # 递归所有子目录
    else:
        iterator = path.glob("*")    # 仅当前目录

    for item in iterator:
        if item.is_file() and keyword in item.name and 'PART' not in item:
            if dry_run:
                print(f"[模拟] 将删除: {item}")
            else:
                try:
                    item.unlink()   # 删除文件
                    print(f"[已删除] {item}")
                    deleted_count += 1
                except Exception as e:
                    print(f"删除失败 {item}: {e}")

    if dry_run:
        print(f"\n模拟运行结束，共匹配到 {deleted_count} 个文件（未实际删除）")
    else:
        print(f"\n实际删除完成，共删除 {deleted_count} 个文件")