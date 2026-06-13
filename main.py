from pathlib import Path

import bilibili_api
from autosv import slice_video_by_danmaku
import os

import watch_dog

if __name__ == '__main__':
    # 1、监控直播录制的路径，检测单条视频及弹幕是否录制完成
    # watch_dog.start_monitoring()

    # 2、录制完成后将弹幕从xml转换为ass格式
    file_path = r"C:\Users\JQJ\Downloads\斗鱼\ok林仔\2026-06-11 15-05-04-444 顶级一号位教学，五黑有位置.xml"
    watch_dog.custom_process(file_path)

    # 3、利用auto-slice-video自动完成切片功能

    # print(dir(bilibili_api.video_uploader))

    # ass_path = r"C:\Users\JQJ\Downloads\斗鱼\ok林仔\2026-06-11 15-05-04-444 顶级一号位教学，五黑有位置.ass"
    # video_path = r"C:\Users\JQJ\Downloads\斗鱼\ok林仔\2026-06-11 15-05-04-444 顶级一号位教学，五黑有位置.mp4"
    # # 传入视频及弹幕文件进行智能切片,对一段视频提取 3 条高能片段，每个片段 300 秒，允许最大重叠 60 秒。
    # slice_video_by_danmaku(ass_path, video_path, 300, 1, 60, 1)

    # 4、上传自媒体网站
