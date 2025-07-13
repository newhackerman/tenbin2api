# tenbin2api，感谢 linux.do 的大佬们

## 生成 session id，放到 tenbin.json
- session_id 获取方法： 登录 tenbin.ai后，按F12，转到应用-左侧-cookies ： session_id的值，复制出来填入tenbin.json
## 准备环境
- 新开一个 PowerShell窗口
- git clone https://github.com/newhackerman/tenbin2api.git
- cd tenbin2api
- python -m venv venv (python要3.8+)
- venv\Scripts\activate
- pip install -r requirements.txt
- python -m patchright install chromium
- python api_solver.py
- 新开一个 PowerShell窗口，执行 venv\Scripts\activate，然后执行 python main.py 
- 新开一个 PowerShell窗口，执行 venv\Scripts\activate，然后执行 python serve_chat.py
- web端使用  http://127.0.0.1:8402/chat.html
- 客户端使用 http://127.0.0.1:8401/v1/models 获取模型列表，API KEY 从 client_api_keys.json 获取


## 本项目只做学习使用，请遵守tenbin.ai官方的约定下使用，否则，请不要下载及使用
