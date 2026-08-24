# 项目记忆文档（AI 助手必读）

> 本文件是"CFA 道德合规 AI 自检助手"项目的完整记忆，供 AI 助手（opencode）接手时快速恢复上下文。
> 每次打开项目，opencode 会自动读取本文件。

## ⚠️ 重要规则（每次会话必遵守）

1. **每次会话中完成任何修改/新功能后，必须同步更新本文件**：修改对应章节、并在文末「更新日志」追加一条本次改动记录。
2. 用户说"更新记忆"时，立即把本次会话的所有改动补进本文件和更新日志。
3. 会话结束时，主动问一句"需要我把本次改动更新进记忆文档吗？"（或在结束前自动更新）。

---

## 一、项目是什么

一个 PWA（渐进式网页应用），员工输入自然语言描述的行为，系统自动：
1. 识别涉及的 CFA 道德准则条款（Standard I–VII 共 22 子条款）
2. 评估风险等级（高/中/低）
3. 生成披露/审批检查清单
4. 提供操作建议 + 披露草稿
5. 引用类似题库案例（RAG）
6. 高风险时"风险拦截"
7. 一键"合规申报"（生成申报单 + 真实发邮件）
8. 生成"合规自证声明"（清白证明，可打印）

用途：CFA 商业策划大赛参赛作品（商策 B 赛道）。

## 二、技术栈

- 前端：HTML5 + Vanilla JS + 原生 CSS（PWA，无构建工具）
- 后端：Python FastAPI + Pydantic v2
- 检索：ChromaDB + 离线 TF-IDF/Jieba 嵌入（默认，无需联网；可选 sentence-transformers）
- 邮件：QQ 邮箱 SMTP（国内无需翻墙）
- 数据：230 道 CFA 一级道德题库（中英对照）

## 三、目录结构

```
D:\cfa-compliance-assistant\
├── data\
│   └── ethics_corpus.jsonl        # 结构化题库（230 题，核心数据）
├── scripts\
│   ├── extract_corpus.py          # 从 PDF 提取题库（数据工程）
│   ├── export_cases.py            # 导出案例到前端 cases.js
│   └── start_demo.py              # 局域网演示一键启动（检测IP+二维码+启动服务）
├── backend\
│   ├── main.py                    # FastAPI 入口（含静态托管前端）
│   ├── config.py                  # 全局配置（含 .env 加载、SMTP）
│   ├── build_kb.py                # 向量知识库（ChromaDB）
│   ├── requirements.txt           # 依赖（固定版本）
│   ├── models\schemas.py          # Pydantic 模型
│   ├── routers\compliance.py      # /api/analyze、/api/send-declaration
│   └── services\
│       ├── classifier.py          # 8类行为意图识别（规则+语义）
│       ├── rag_engine.py          # RAG 引擎（分类→检索→生成）
│       ├── llm_client.py          # LLM 客户端（可插拔，未配key时离线）
│       ├── embedder.py            # 嵌入层（TF-IDF+SVD 默认）
│       └── standards.py           # 22 子条款定义
├── frontend\
│   ├── index.html                 # 主页面（3视图+2弹窗）
│   ├── manifest.json / sw.js      # PWA 配置 / Service Worker
│   ├── css\style.css              # 全部样式（深蓝金主题）
│   └── js\
│       ├── app.js                 # 主逻辑（自检/申报/自证/历史）
│       ├── offline.js             # 离线规则引擎（8类关键词）
│       ├── cases.js               # 内置案例库（export_cases.py 生成）
│       ├── api.js                 # 后端 API 调用
│       └── storage.js             # IndexedDB 封装
├── tests\                         # pytest 测试（29 通过）
├── Dockerfile / render.yaml / vercel.json
├── .env                           # 本地密钥（已 gitignore，勿删）
├── 启动演示.bat                    # 双击启动局域网演示
├── 继续开发.bat                    # 双击打开 AI 助手续聊
└── report.md                      # 商策报告（6760 字）
```

## 四、已实现功能（全部完成）

1. **行为自检**：输入→风险评级+准则+清单+建议+案例引用（RAG）
2. **8 类快捷场景**：收礼/兼职/离职/交易/报酬/研报/内幕/冲突（带图标）
3. **风险拦截**：高风险显示红色横幅
4. **合规申报**：申报单+编号+「一键发送邮件」（QQ SMTP）+「邮件客户端」备用
5. **合规自证**：生成带编号+时间戳的正式声明，可复制/打印
6. **准则速查**：22 子条款可搜索
7. **历史记录**：IndexedDB 存储 + 导出 PDF
8. **离线可用**：Service Worker + 本地规则引擎
9. **语音输入**：Web Speech API

## 五、关键配置（重要）

- **邮箱**：收件人 `eric_han_music@petalmail.com`（华为花瓣邮箱），发件 QQ 邮箱 `3517621936@qq.com`
- **SMTP 授权码**：存在 `.env` 文件（`SMTP_PASSWORD=...`），已 gitignore，**勿删勿上传**
- **IP 检测**：`start_demo.py` 用 `ipconfig` 解析，优先选 `192.168.x.x`（避开 VPN/虚拟网卡）
- **无 LLM Key**：系统走离线规则引擎（`offlineAnalyze`），无需 API

## 六、部署方式（两种）

1. **局域网演示（答辩主方案）**：手机开热点→电脑连热点→双击`启动演示.bat`→生成二维码`demo_qr.png`→评委手机连同一热点扫码访问 `http://<电脑IP>:8000`
2. **公网（GitHub Pages）**：`https://jackma-sysu.github.io/cfa-compliance-assistant/`（静态，无后端，「一键发邮件」不可用，只有 mailto 备用）

## 七、常用命令

```powershell
# 启动局域网演示
双击 启动演示.bat    或    python scripts\start_demo.py

# 启动后端开发
cd backend; uvicorn main:app --host 0.0.0.0 --port 8000

# 构建/更新向量库
cd backend; python build_kb.py

# 改题库后重新导出前端案例库
python scripts\export_cases.py

# 运行测试
pytest tests -q

# 提交上线
git add . ; git commit -m "说明" ; git push
```

## 八、修改指南（AI 助手改哪里）

- 改文字/按钮/快捷标签 → `frontend\index.html`
- 改样式/颜色 → `frontend\css\style.css`
- 改分类关键词、清单、建议 → `frontend\js\offline.js`（前端离线版）和 `backend\services\classifier.py`（后端）
- 改申报/自证/发邮件逻辑 → `frontend\js\app.js`（前端）+ `backend\routers\compliance.py`（后端发邮件）
- 改案例数据 → 改 `data\ethics_corpus.jsonl`，然后 `python scripts\export_cases.py` 重新生成
- 改邮件收件人/发件配置 → `backend\config.py` 或 `.env`

## 九、注意事项 / 坑

- Service Worker 是"网络优先"策略，改完前端后刷新即可看到；若还是旧的，无痕窗口或 Ctrl+Shift+R
- 邮件"一键发送"依赖后端运行（局域网模式），GitHub Pages 静态版发不了
- 开热点的手机访问不了自己热点下的电脑（系统限制），测试需第二台设备
- `.env` 授权码别上传 GitHub
- 数据文件 `data\ethics_corpus.jsonl` 是核心，别误删

## 十、更新日志

- 2026-08-24：完成核心项目——数据工程（230 题结构化）、FastAPI 后端、PWA 前端、ChromaDB 知识库、8 类意图分类、RAG 引擎、离线规则引擎
- 2026-08-24：部署到 GitHub Pages（无卡免费用方案），内置案例库到前端（cases.js）
- 2026-08-24：新增合规申报系统（申报单+编号+邮件）、风险拦截横幅、合规自证声明
- 2026-08-24：邮件发送改用 QQ 邮箱 SMTP（国内无需翻墙），授权码存本地 .env
- 2026-08-24：局域网演示方案（start_demo.py 检测IP+二维码）、一键发送邮件
- 2026-08-24：界面美化（深蓝金主题、渐变、阴影、动画、快捷标签图标）
- 2026-08-24：IP 检测改用 ipconfig 解析，避开 VPN/虚拟网卡；修复 Service Worker 缓存
- 2026-08-24：新增本项目记忆文档 AGENTS.md、双击启动脚本、继续开发脚本
