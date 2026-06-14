import asyncio
import subprocess
import time
import os
import logging
from datetime import datetime, timedelta

from bilibili_api import Credential
from bilibili_api.channel_series import add_aids_to_series
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import parse
from pathlib import Path
from autosv import slice_video_by_danmaku

import upload

# 配置日志（便于排查问题）
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- 配置区 ---
WATCH_DIRECTORY = r"C:\Users\JQJ\Downloads\斗鱼\ok林仔"  # 请替换为你的监控目录
VIDEO_EXTENSIONS = ['.xml']  # 需要监控的视频格式


def custom_process(file_path):
    """
    自定义处理函数：视频文件写入完成后执行的操作
    请根据实际需求修改此函数内容
    """
    logging.info(f"开始处理视频文件: {file_path}")
    # 示例：打印文件大小
    file_size = os.path.getsize(file_path) / (1024 * 1024)
    logging.info(f"文件大小: {file_size:.2f} MB")
    # 2、录制完成后将弹幕从xml转换为ass格式
    video_file = os.path.splitext(file_path)[0] + '.mp4'
    ass_file = os.path.splitext(file_path)[0] + '.ass'
    events = parse.parse_douyu_danmaku(file_path)
    parse.events_to_ass(events, ass_file)

    # 3、调用 FFmpeg 压制视频
    # video_danmu_file = os.path.splitext(file_path)[0] + '弹幕版.mp4'
    #
    # work_dir = Path(file_path).parent
    # original_dir = os.getcwd()
    # try:
    #     os.chdir(work_dir)
    #     # 相对路径（仅文件名，不含目录）
    #     video_name = Path(video_file).name
    #     ass_name = Path(ass_file).name
    #     output_name = Path(video_danmu_file).name
    #     cmd = f'ffmpeg -i "{video_name}" -vf "ass={ass_name}" -c:a copy "{output_name}"'
    #     subprocess.run(cmd, shell=True, check=True)
    #     logging.info(f"弹幕压制成功: {video_danmu_file}")
    # except subprocess.CalledProcessError as e:
    #     logging.error(f"FFmpeg 执行失败: {e}")
    # finally:
    #     os.chdir(original_dir)  # 恢复原工作目录

    # 4、利用auto-slice-video自动完成切片功能
    ass_path = ass_file
    video_path = video_file
    # 传入视频及弹幕文件进行智能切片,对一段视频提取 3 条高能片段，每个片段 300 秒，允许最大重叠 60 秒。
    logging.info("切片开始")
    output_video_path = slice_video_by_danmaku(ass_path, video_path, 300, 3, 60, 1)
    logging.info("切片结束")

    # 5、上传自媒体网站
    for path in output_video_path:
        logging.info(path)
        asyncio.run(upload.upload(path))
        # asyncio.run(upload.list_all_my_series())

        # 1. 设置认证信息
        # credential = Credential(
        #     sessdata="e35e940a%2C1796701790%2Cf657a%2A62CjDo4ZTHqe_im7o2GTvVCOFuhq6Q9nogBxwSXHBAwQDpBur1ebWUonTK9r43GjU7sgYSVmFTZ1owU2d5dlQwYnNud2NCTG9fVHZnZlRHYlVjMmRrX1dVdEZVSEZjQVlKSXREQVNIeUszUS1FYVBaOXdJMndwSGoyWnpWNGJzVmpIT1JSai1uMmxRIIEC",
        #     bili_jct="f43703674f1c47995c218f600a45099b",
        #     buvid3="你的 buvid3" # 有时需要，可选
        # )
        # asyncio.run(upload.list_all_my_series())
        # break
    # 运行批量上传
    # asyncio.run(upload.upload_multiple(output_video_path, 8319296))
    # 6、检测上传成功后，删除源文件释放空间
    os.remove(file_path)
    logging.info("文件已清理：" + file_path)
    os.remove(ass_path)
    logging.info("文件已清理：" + ass_path)
    os.remove(video_path)
    logging.info("文件已清理：" + video_path)

    for path in output_video_path:
        os.remove(Path(path))
        logging.info("文件已清理：" + path)


    logging.info(f"处理完成: {file_path}")
    # input("按回车键退出...")

class VideoHandler(FileSystemEventHandler):
    """视频文件事件处理器（带异常保护）"""

    def on_closed(self, event):
        """文件关闭时触发（表示写入完成）"""
        if event.is_directory:
            return

        file_path = event.src_path
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext in VIDEO_EXTENSIONS:
            logging.info(f"检测到视频写入完成: {file_path}")
            try:
                # 调用自定义处理函数
                custom_process(file_path)
            except Exception as e:
                logging.error(f"处理文件 {file_path} 时发生错误: {e}", exc_info=True)

    def on_modified(self, event):
        """文件修改时触发（用于记录进度，可选）"""
        if not event.is_directory:
            logging.info(f"文件正在写入: {event.src_path}")


def start_monitoring():
    """启动监控（带自动恢复的无限循环）"""
    while True:
        event_handler = VideoHandler()
        observer = Observer()
        observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)

        logging.info(f"开始监控目录: {WATCH_DIRECTORY}")
        observer.start()

        try:
            # 保持主线程运行，每秒检查一次 observer 是否存活
            while observer.is_alive():
                time.sleep(1)
        except Exception as e:
            logging.error(f"监控服务发生异常: {e}", exc_info=True)
        finally:
            observer.stop()
            observer.join()
            logging.warning("监控服务已停止，5秒后尝试重启...")
            time.sleep(5)


def check_files(directory_path, interval=60):
    """
    定时检查目录下所有XML文件的最后修改时间

    参数:
        directory_path: 要监控的目录路径
        interval: 检查间隔（秒），默认60秒
    """
    while True:
        try:
            current_time = datetime.now()
            # 计算5分钟前的时间点
            five_minutes_ago = current_time - timedelta(minutes=5)

            # 遍历目录下所有XML文件
            for filename in os.listdir(directory_path):
                if filename.lower().endswith('.xml'):
                    file_path = os.path.join(directory_path, filename)

                    # 获取文件的最后修改时间
                    if os.path.isfile(file_path):
                        mod_timestamp = os.path.getmtime(file_path)
                        mod_time = datetime.fromtimestamp(mod_timestamp)

                        # 判断是否早于5分钟前
                        if mod_time < five_minutes_ago:
                            custom_process(file_path)

        except Exception as e:
            print(f"扫描过程中出错: {e}")

        # 等待设定的间隔时间后再次检查
        time.sleep(interval)


# def start_timer(directory_path, interval=60, daemon=False):
#     """
#     启动定时器线程
#
#     参数:
#         directory_path: 要监控的目录路径
#         interval: 检查间隔（秒），默认60秒
#         daemon: 是否作为守护线程运行
#     """
#     timer_thread = threading.Thread(
#         target=check_files,
#         args=(directory_path, interval),
#         daemon=daemon
#     )
#     timer_thread.start()
#     return timer_thread