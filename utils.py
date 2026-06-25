import json
import logging
import os
import subprocess
from pathlib import Path

from abstract_utilities import requests
from bilibili_api import Credential, user


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
        if item.is_file() and keyword in item.name and "PART" not in item.name:
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

# 获取up名字
def get_up(xml_rul: str):
    p = Path(xml_rul)
    return p.parent.name

#获取b站用户的cookies
def get_cookies(uname: str):
    # B站用户cookie等数据
    config = load_json_config('config.json')

    # 1. 将从浏览器获取的 Cookies 填入字典
    cookies = {
        "SESSDATA": get_value_by_key_recursive(config, "uname", uname, "sessdata"),
        "bili_jct": get_value_by_key_recursive(config, "uname", uname, "bili_jct"),
        "DedeUserID": get_value_by_key_recursive(config, "uname", uname, "DedeUserID"),
        "buvid3": get_value_by_key_recursive(config, "uname", uname, "buvid3"),
        "buvid4": get_value_by_key_recursive(config, "uname", uname, "buvid4"),
    }

    return cookies

#获取b站用户的cookies
def get_credential(uname: str):
    config = load_json_config('config.json')
    credential = Credential(
        sessdata=get_value_by_key_recursive(config, "uname", uname, "sessdata"),
        bili_jct=get_value_by_key_recursive(config, "uname", uname, "bili_jct"),
        DedeUserID=get_value_by_key_recursive(config, "uname", uname, "DedeUserID"),
        buvid3=get_value_by_key_recursive(config, "uname", uname, "buvid3"),
        buvid4=get_value_by_key_recursive(config, "uname", uname, "buvid4"),
    )

    return credential

# 建立b站合集
def create_season(uname: str,title: str,desc: str,cover_url: str):
    # 1. 将从浏览器获取的 Cookies 填入字典
    cookies = get_cookies(uname)
    # 使用B站上已经存在的图片URL作为封面（测试用）

    data = {
        "title": title,
        "desc": desc,
        "cover": cover_url,
        "csrf": cookies.get("bili_jct", "")
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "Referer": "https://member.bilibili.com/",
        "Origin": "https://member.bilibili.com",
        "Accept": "application/json, text/plain, */*",
    }

    session = requests.Session()
    session.cookies.update(cookies)
    session.headers.update(headers)

    try:
        print("正在创建合集...")
        print(f"封面图: {cover_url}")

        response = session.post(
            "https://member.bilibili.com/x2/creative/web/season/add",
            data=data,
            timeout=30
        )

        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 200:
            try:
                result = response.json()
                print(f"解析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

                if result.get("code") == 0:
                    # 修正这里：data 字段直接是 ID，而不是一个对象
                    season_id = result.get("data")
                    print(f"✅ 合集创建成功！合集ID为: {season_id}")
                    print(f"📌 查看合集: https://www.bilibili.com/season/{season_id}")
                    return season_id
                else:
                    print(f"❌ 创建失败: {result.get('message')}")
                    return None
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                return None
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()
        return None

async def get_seasons(uname: str):
    config = load_json_config('config.json')
    # 替换为你想查询的B站用户ID（数字UID）
    uid = get_value_by_key_recursive(config, "uname", uname, "DedeUserID"),  # 例如：12345678

    # 初始化用户对象
    u = user.User(uid)

    try:
        # 获取用户的合集（频道系列）
        channels = await u.get_channels()

        print(f"用户 {uid} 的合集列表：")
        print("=" * 60)

        if not channels:
            print("该用户暂无合集")
            return []

        # 遍历并解析每个 ChannelSeries 对象
        for idx, channel in enumerate(channels, 1):
            print(f"{idx}. 合集信息:")

            # ChannelSeries 对象通常有以下属性或方法
            # 尝试不同的方式获取信息
            try:
                # 方式1：直接访问属性
                season_id = getattr(channel, 'id', None) or getattr(channel, 'season_id', None)
                title = getattr(channel, 'name', None) or getattr(channel, 'title', None)
                desc = getattr(channel, 'desc', None) or getattr(channel, 'description', None)
                count = getattr(channel, 'count', None) or getattr(channel, 'video_count', 0)

                # 如果属性不存在，尝试转换为字典
                if not title:
                    # 尝试获取对象的 __dict__ 属性
                    if hasattr(channel, '__dict__'):
                        channel_dict = channel.__dict__
                        print(f"   对象属性: {channel_dict}")
                        title = channel_dict.get('name') or channel_dict.get('title')
                        season_id = channel_dict.get('id') or channel_dict.get('season_id')

                # 如果还是获取不到，打印对象本身看看
                if not title:
                    print(f"   对象类型: {type(channel)}")
                    print(f"   对象内容: {channel}")
                    # 尝试调用对象的方法获取信息
                    if hasattr(channel, 'get_info'):
                        info = await channel.get_info()
                        print(f"   获取到的信息: {info}")
                        title = info.get('title') or info.get('name')
                        season_id = info.get('id') or info.get('season_id')

                print(f"   合集ID: {season_id}")
                print(f"   标题: {title or '未命名'}")
                print(f"   描述: {desc or '无描述'}")
                print(f"   视频数: {count or 0}")

            except Exception as e:
                print(f"   解析失败: {e}")
                print(f"   原始对象: {channel}")

            print("-" * 40)

        return channels

    except Exception as e:
        print(f"获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None