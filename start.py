import os
import re
import sys
import requests

# 设置直接内置在程序中
HOST = "127.0.0.1"
LANG = "zh,en"  # 使用的语言

# 初始化代理（如果需要）
PROXY = None  # 如果需要代理，设置为'http://your_proxy'

ROOT = os.getcwd()

# 初始化环境变量并传入 PORT 参数
def init(port):
    if PROXY:
        os.environ['http_proxy'] = PROXY
        os.environ['https_proxy'] = PROXY
    os.environ['SNAP'] = ROOT
    os.environ['SNAP_USER_DATA'] = ROOT
    os.environ['PORT'] = str(port)  # 将 PORT 环境变量设置为字符串形式

# 测试GitHub连接和模型下载
def test_github():
    path = os.path.join(ROOT, '.local/cache/argos-translate')
    os.makedirs(path, exist_ok=True)
    cache = os.path.join(path, 'index.json')
    
    # 如果缓存存在且非空，则直接返回
    if os.path.exists(cache) and os.path.getsize(cache) > 0:
        return True
    
    try:
        print("测试下载模型")
        proxy = None
        if PROXY:
            proxy = {
                "http": PROXY,
                "https": PROXY
            }
        print(f'代理: {"无" if not proxy else PROXY}')
        res = requests.get("https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json", proxies=proxy)
        
        if res.status_code != 200:
            raise Exception(f"status_code={res.status_code}")
        
        with open(cache, 'w', encoding='utf-8') as f:
            f.write(res.text)
    except Exception as e:
        msg = '第一次启动需要下载模型，请设置代理地址' if not PROXY else f'你设置的代理地址不正确:{PROXY},请正确设置代理，以便下载模型'
        print(f"\n=======\n无法下载模型，{msg}\n\n{e}\n\n")
        return False
    
    print('测试通过，准备下载模型，模型可能较大，确保网络稳定')
    return True

# 启动翻译服务
def run(port):
    init(port)
    try:
        sys.argv.extend(["--host", HOST, "--port", str(port), "--load-only", LANG, "--update"])
        
        if not test_github():
            return
        
        from libretranslate_totally_local.main import main
        main()
    except Exception as e:
        err = str(e)
        if re.search(r'download error', err, re.I):
            msg = '第一次启动需要下载模型，请设置代理地址' if not PROXY else f'你设置的代理地址不正确:{PROXY},请正确设置代理，以便下载模型'
            print(f"\n=======\n无法下载模型，{msg}\n{err}\n\n")
        else:
            print(err)
        sys.exit()
