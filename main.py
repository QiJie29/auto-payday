import asyncio
from pathlib import Path

import bilibili_api
from autosv import slice_video_by_danmaku
import os
from config import load_json_config
from config import load_json_config,get_value_by_key_recursive

import watch_dog


async def main():
    # 你的监控路径列表
    config = load_json_config('config.json')

    # directories = [
    #     get_value_by_key_recursive(config, "up", "OK林仔", "xml_url"),
    #     get_value_by_key_recursive(config, "up", "Minana呀", "xml_url")
    # ]

    directories = []

    for live_stream in config['live_stream'] :
        # print(live_stream['xml_url'])
        directories.append(live_stream['xml_url'])

    # 创建所有监控任务
    tasks = [
        watch_dog.check_and_process(dir, interval=60, delay_minutes=5)
        for dir in directories if os.path.exists(dir)
    ]

    print(f"开始监控 {len(tasks)} 个目录...")
    for dir in directories:
        print(dir)
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n监控已停止")