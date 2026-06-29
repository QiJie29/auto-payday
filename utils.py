import json
import logging
import os
import platform
import subprocess
import time
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
        logging.info("检测到ass文件已经存在，执行删除操作")
        os.remove(ass_url)

    # cmd = f'"{danmakuFactory_path}" -o "{ass_url}" -i "{xml_url}"'
    # subprocess.run(cmd, shell=True, check=True)

    # 优化cmd调用，copy本机环境
    cmd = [
        f"{danmakuFactory_path}",
        "-o",
        f"{ass_url}",
        "-i",
        f"{xml_url}"
    ]

    # 关键：使用当前进程的完整环境变量（等同于CMD的环境）
    result = subprocess.run(cmd, env=os.environ.copy(), capture_output=True, text=True)
    return ass_url

# 将弹幕压制到视频中
def press_danmu_to_video(video_url: str,ass_url: str):
    video_danmu_url = os.path.splitext(video_url)[0] + '弹幕版' + os.path.splitext(video_url)[1]

    if os.path.isfile(video_danmu_url):
        logging.info("检测到视频弹幕版文件已经存在，执行删除操作")
        os.remove(video_danmu_url)

    work_dir = Path(video_url).parent
    original_dir = os.getcwd()
    try:
        os.chdir(work_dir)
        # 相对路径（仅文件名，不含目录）
        video_name = Path(video_url).name
        ass_name = Path(ass_url).name
        output_name = Path(video_danmu_url).name
        cmd = f'ffmpeg -i "{video_name}" -vf "ass={ass_name}" -c:a copy "{output_name}"'
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

def get_seasons(uname: str):
    """
    获取当前用户的所有合集（Season）列表
    """
    sessdata = get_cookies(uname).get("SESSDATA")
    bili_jct = get_cookies(uname).get("bili_jct")

    # 1. 构建请求URL
    url = "https://member.bilibili.com/x2/creative/web/seasons"

    # 2. 设置请求参数（分页等）
    params = {
        "pn": 1,  # 页码
        "ps": 30,  # 每页数量
        "order": "mtime",  # 按修改时间排序
        "sort": "desc"  # 降序
    }

    # 3. 设置Cookie
    cookies = {
        'SESSDATA': sessdata,
        'bili_jct': bili_jct
    }

    # 4. 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://member.bilibili.com/'
    }

    try:
        response = requests.get(url, headers=headers, cookies=cookies, params=params)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                # 此处不返回数据集，直接打印出来
                # return result.get('data', {})
                data = result.get('data')
                print(data)
                if data:
                    seasons = data.get('seasons', [])
                    print(f"找到 {len(seasons)} 个合集:\n")

                    for season in seasons:
                        season_id = season.get('season').get('id')
                        season_title = season.get('season').get('title')
                        print(f"📁 合集ID: {season_id}, 标题: {season_title}")

                        # 获取该合集下的分段（Sections）信息
                        sections = season.get('sections', {}).get('sections', [])
                        if sections:
                            print(f"   包含 {len(sections)} 个分段:")
                            for section in sections:
                                section_id = section.get('id')
                                section_title = section.get('title')
                                print(f"      🔹 分段ID: {section_id}, 标题: {section_title}")
                        else:
                            print("   该合集暂无分段。")
                        print("-" * 30)
            else:
                print(f"API返回错误: {result.get('message')}")
                return None
        else:
            print(f"HTTP请求失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"请求异常: {e}")
        return None

# 根据aid获取视频状态，是否上传到合集中
def get_video_info(aid):
    """
    获取视频详细信息，包括它所属的合集
    使用更稳定的接口和完整的请求头
    """
    # 使用更稳定的接口
    url = f"https://api.bilibili.com/x/web-interface/view?aid={aid}"

    # 添加完整的请求头，模拟浏览器行为
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.bilibili.com/',  # 关键：必须添加 Referer
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Origin': 'https://www.bilibili.com'
    }

    try:
        print(f"📤 查询视频信息: AID={aid}")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   HTTP状态: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if data.get('code') == 0:
                video_data = data.get('data', {})
                season = video_data.get('season', {})
                print(f"\n📹 视频所有内容: {video_data}")
                print(f"\n📹 视频标题: {video_data.get('title')}")
                print(f"\n📹 视频cid: {video_data.get('cid')}")
                print(f"📊 视频状态: 已发布")

                if season and season.get('season_id'):
                    print(f"📁 所属合集ID: {season.get('season_id')}")
                    print(f"   合集名称: {season.get('title', '未知')}")
                    print(f"   合集内排序: {season.get('position', '未知')}")
                else:
                    print("📁 该视频未加入任何合集")

                return video_data
            else:
                print(f"❌ API返回错误: {data.get('message')}")
                return None
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}")
            return None

    except requests.exceptions.JSONDecodeError:
        print(f"❌ 响应不是有效的JSON格式")
        print(f"   原始响应: {response.text[:200]}")
        return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

# 在视频上传完审批通过后调用该函数将视频加入合集中
def add_video_to_season(season_id, section_id, aid, cid, sessdata, bili_jct, title=""):
    """
    精确模拟 @renmu/bili-api 的 addMedia2Season 方法
    """
    # 1. 构建请求 URL（带时间戳和 csrf）
    timestamp = int(time.time() * 1000)  # 毫秒级时间戳
    url = f"https://member.bilibili.com/x2/creative/web/season/section/episodes/add?t={timestamp}&csrf={bili_jct}"

    # 2. 构建请求体（JSON 格式）
    payload = {
        "sectionId": int(section_id),
        "episodes": [
            {
                "aid": int(aid),
                "cid": int(cid),
                "title": title
            }
        ],
        "csrf": bili_jct
    }

    # 3. 构建请求头（模拟库的行为）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',  # 关键：使用 JSON 格式
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://member.bilibili.com',
        'Referer': f'https://member.bilibili.com/platform/season?season_id={season_id}',
        'X-Requested-With': 'XMLHttpRequest'
    }

    # 4. Cookie
    cookies = {
        'SESSDATA': sessdata,
        'bili_jct': bili_jct
    }

    print(f"📤 发送请求:")
    print(f"   URL: {url}")
    print(f"   Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    try:
        # 5. 发送 POST 请求（使用 JSON 格式）
        response = requests.post(
            url,
            headers=headers,
            cookies=cookies,
            json=payload,  # 使用 json= 自动设置 Content-Type 为 application/json
            timeout=30
        )

        print(f"   HTTP状态: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        else:
            print(f"   HTTP错误: {response.status_code}")
            print(f"   响应内容: {response.text[:500]}")
            return None

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None


def escape_ass_text_commas(ass_path):
    """将 ASS 文件 Text 字段中的逗号替换为中文逗号，避免干扰解析"""
    with open(ass_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith('Dialogue:'):
            # 将 Text 字段中的英文逗号替换为中文逗号
            # 注意：保留前 9 个逗号作为分隔符，只替换第 10 个之后的逗号
            parts = line.split(',', 9)  # 最多分割 9 次，保留 Text 字段整体
            if len(parts) == 10:
                # 替换 Text 字段内的逗号
                parts[9] = parts[9].replace(',', '，')
                line = ','.join(parts)
        new_lines.append(line)

    with open(ass_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)