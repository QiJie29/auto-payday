from autosv import slice_video_by_danmaku

if __name__ == '__main__':
    # 传入视频及弹幕文件进行智能切片
    slice_video_by_danmaku(ass_path, video_path, duration=300, top_n=3, max_overlap=60, step=1)