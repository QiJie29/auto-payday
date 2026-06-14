import os
from pathlib import Path

from config import load_json_config
from config import get_value_by_key_recursive

if __name__ == '__main__':
    # path = r'C:\Users\JQJ\Downloads\斗鱼\ok林仔\test/2902s_2026-06-12 12-07-29-219 顶级一号位教学，五黑有位置.mp4'
    # os.remove(path)
    config = load_json_config('config.json')
    # print(config['live_stream'])

    result = get_value_by_key_recursive(config, "up", "Minana呀", "xml_url")
    print(result)  # 输出: e35e940a...

    cut_video_url = r"1819s_2026-06-13 23-15-13-308 宝宝 晚上好～.mp4"
    print(Path(cut_video_url).stem)