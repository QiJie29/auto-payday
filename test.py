import asyncio
import logging
import os
import subprocess
from pathlib import Path

import requests
from bilibili_api import Credential, sync, channel_series, favorite_list
from bilibili_api.channel_series import ChannelSeries

import upload
import utils

def get_my_seasons(sessdata, bili_jct):


    # 获取用户创建的合集列表
    # 注意：这里需要传入你的用户ID (uid)
    # 如果不确定uid，可以先从credential中获取或者通过其他API查询
    uid = 382551067  # 替换为实际的uid
    """
        获取当前登录用户的所有合集（Season）列表
        """
    url = "https://member.bilibili.com/x2/creative/web/seasons"
    cookies = {
        "SESSDATA": sessdata,
        "bili_jct": bili_jct
    }
    # 可以添加分页参数，默认第1页，每页30条
    params = {
        "pn": 1,
        "ps": 30
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://member.bilibili.com/"
    }

    try:
        resp = requests.get(url, params=params, cookies=cookies, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 0:
            # 数据在 data['data']['list'] 中
            return data.get("data", {}).get("list", [])
        else:
            print(f"API 返回错误: {data.get('message')}")
            return []
    except Exception as e:
        print(f"请求失败: {e}")
        return []


if __name__ == '__main__':
    # 出现故障后单点上传
    base_path = r"C:\Users\JQJ\Downloads\斗鱼\backup\spec"
    path = f"{base_path}\\2026-06-16 01-42-23-397 顶级一号位教学，五黑有位置.flv"
    # cover_url = f"{base_path}\\2026-06-15 21-12-10-249 顶级一号位教学，五黑有位置.jpg"
    # # asyncio.run(upload.upload_to_bilibili("猪小杰123",path,cover_url))
    # utils.delete_files_containing_keyword(Path(cover_url).parent, Path(cover_url).stem, False, False)

    base_path = r"C:\Users\JQJ\Downloads\斗鱼\OK林仔"
    path = f"{base_path}\\2026-06-16 01-42-23-397 顶级一号位教学，五黑有位置.flv"

    p = Path(path)
    parent_folder_name = p.parent.name  # 父目录的名称
    print(utils.get_up(path))
    print(parent_folder_name)  # 输出: OK林仔