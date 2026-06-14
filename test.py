import os
from config import load_json_config

if __name__ == '__main__':
    # path = r'C:\Users\JQJ\Downloads\斗鱼\ok林仔\test/2902s_2026-06-12 12-07-29-219 顶级一号位教学，五黑有位置.mp4'
    # os.remove(path)
    config = load_json_config('config.json')
    print(config['live_stream'])