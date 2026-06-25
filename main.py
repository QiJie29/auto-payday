import asyncio
from pathlib import Path

import bilibili_api
from autosv import slice_video_by_danmaku
import os

import utils
import watch_dog


async def main():
    # 你的监控路径列表
    config = utils.load_json_config('config.json')

    directories = []

    for live_stream in config['live_stream'] :
        # print(live_stream['xml_url'])
        if live_stream['enabled']:
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