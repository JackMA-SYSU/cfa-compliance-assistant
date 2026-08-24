# CFA 道德合规 AI 自检助手

基于 RAG 的 CFA 道德准则智能申报系统。员工输入自然语言描述的行为，系统自动：
识别涉及的 CFA 道德准则条款、评估风险等级、生成披露/审批清单、提供可操作建议，并引用类似题库案例。

## 功能
- **行为自检**：自然语言输入 → 风险评级（高/中/低）→ 准则匹配 → 检查清单 → 披露草稿
- **准则速查**：Standard I–VII 共 22 条子准则中英对照，可搜索
- **历史记录**：本地保存申报记录，可导出 PDF
- **离线可用**：PWA + Service Worker，断网时用本地规则引擎给出基础分析

## 技术栈
- 前端：HTML5 + Vanilla JS + 原生 CSS（PWA）
- 后端：Python FastAPI + Pydantic v2
- 检索：ChromaDB + 离线 TF-IDF/Jieba 嵌入（可选 sentence-transformers）
- LLM：OpenAI / DeepSeek / 通义千问 / 本地 Ollama（可插拔）

## 目录结构
```
├── data/                  # 结构化题库（230 题，中英对照）
│   └── ethics_corpus.jsonl
├── scripts/               # 数据工程
│   └── extract_corpus.py
├── backend/               # FastAPI 后端
│   ├── main.py
│   ├── build_kb.py        # 向量知识库
│   ├── routers/compliance.py
│   ├── services/          # classifier / rag_engine / llm_client / embedder / standards
│   └── models/schemas.py
├── frontend/              # PWA 前端
├── tests/                 # pytest 测试
└── Dockerfile
```

## 本地运行

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 构建知识库
```bash
cd backend
python build_kb.py
```

### 3. 启动服务
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

浏览器打开 http://localhost:8000 即可（前端已由后端托管）。

### 4. （可选）启用 LLM 生成
```bash
# DeepSeek
set LLM_API_KEY=sk-xxx
set LLM_BASE_URL=https://api.deepseek.com
set LLM_MODEL=deepseek-chat
```
未配置 API Key 时，系统使用本地规则引擎（离线可用）。

## API
- `POST /api/analyze` — 请求 `{"behavior": "..."}`，返回风险评级、准则列表、检查清单、披露草稿等
- `GET /health` — 健康检查
- Swagger UI：http://localhost:8000/docs

## 测试
```bash
pytest tests -q
```

## 部署
- 前端：Vercel（见 `frontend/vercel.json`）
- 后端：Render / Railway（见 `render.yaml`、`Dockerfile`）
