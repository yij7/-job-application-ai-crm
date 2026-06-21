# job-application-ai-crm

AI 求职投递管理与沟通分析系统。

本项目当前版本是 V8。项目不做 BOSS 自动登录、不做爬虫、不绕过平台权限。网页采集能力只通过用户主动安装 Chrome 插件、点击“开始监控”或“发送到 BossPilot 分析”后读取当前 Boss 直聘页面可见文本，并在用户点击上传后进入 BossPilot 分析流程。

## 项目背景

求职过程中，候选人通常会在多个平台投递大量岗位，并与不同公司、HR 或招聘方沟通。信息分散在不同平台后，很容易忘记投递状态、岗位细节、沟通进展和后续跟进动作。

本项目希望先用一个简单清晰的本地工具，帮助用户集中记录求职投递信息。后续可以在用户授权和手动提供数据的前提下，逐步增加 AI 分析、同步和 OCR 能力。

## 当前 MVP 功能

- 手动录入公司名、岗位名、岗位方向、薪资、地点、投递平台、投递状态、备注和聊天记录文本。
- 点击“保存记录”后，将数据保存到 `data/job_records.csv`。
- 页面下方展示已经保存的全部投递记录。
- 如果 `data/job_records.csv` 不存在，应用启动时会自动创建。
- 支持删除已经保存的记录。
- 支持编辑已经保存的记录，并更新到 CSV 文件。
- 支持粘贴岗位原始信息后，用简单规则一键解析并填充表单字段。
- 支持点击“AI 分析岗位”，使用 DeepSeek API 分析当前表单中的岗位信息、备注和聊天记录。
- 保存记录时，会同时保存 AI 岗位匹配度、岗位类型、风险点、下一步建议和建议回复话术。
- 支持按投递状态、AI 岗位匹配度、AI 岗位类型和关键词筛选已保存记录。
- 支持为岗位设置优先级，并自动生成“岗位优先级分值”，本地默认按优先级从高到低展示。
- 支持将单条已保存记录同步到飞书多维表格，并记录同步状态和同步时间。
- 飞书中可按“岗位优先级分值”降序排序，以优先查看高价值岗位。
- 支持“智能粘贴解析”，从岗位详情、公司介绍、HR 聊天记录或混合文本中自动生成结构化求职记录。
- 支持上传岗位页、公司介绍页或 HR 聊天截图，调用阿里云百炼 Qwen 视觉模型读取图片并生成结构化求职记录。
- 支持面向产品、AI 产品、产品运营、项目助理实习方向的深度诊断，输出产品相关度、AI/数据/SaaS 相关度、简历增值程度、低价值杂活风险、成长路径清晰度、综合优先级、HR 追问问题、面试表达建议和建议回复话术。
- 支持 Chrome 插件从 Boss 直聘网页版岗位详情页一键采集页面文本，并自动导入 BossPilot 分析、保存和可选同步飞书。
- 支持 Chrome 插件求职会话监控模式：用户主动开始监控后正常浏览 Boss 直聘，结束后上传本次会话，BossPilot 可批量导入、解析、AI 分析、保存和可选同步飞书。

## 一键解析规则

当前版本不调用 AI API，只按简单文本规则识别以下格式：

- `公司名：xxx`
- `岗位名：xxx`
- `岗位方向：xxx`
- `薪资：xxx`
- `地点：xxx`
- `投递平台：xxx`
- `备注：xxx`
- `聊天记录：xxx`

没有识别到的字段会保持为空，不会报错。

## 技术栈

- Python
- Streamlit
- Pandas
- Requests
- python-dotenv
- Pillow
- pytesseract
- 阿里云百炼 Qwen 视觉模型
- DeepSeek API
- 飞书开放平台 API
- CSV 本地文件存储

## 运行方式

### 本地启动

1. 安装 Python 依赖：

```bash
pip install -r requirements.txt
```

2. 配置环境变量：

复制 `.env.example` 为 `.env`，然后把里面的示例值替换成你的真实 key。

```env
DEEPSEEK_API_KEY=your_api_key_here
QWEN_API_KEY=your_qwen_api_key_here
QWEN_VL_MODEL=qwen3.6-plus
FEISHU_APP_ID=your_app_id_here
FEISHU_APP_SECRET=your_app_secret_here
FEISHU_APP_TOKEN=your_bitable_app_token_here
FEISHU_TABLE_ID=your_table_id_here
```

3. 启动应用：

```bash
streamlit run app.py
```

4. 在浏览器中打开 Streamlit 提供的本地地址。

本地数据会保存到 `data/job_records.csv`。如果该文件不存在，应用启动时会自动创建。

### 部署到 Streamlit Cloud

项目可以作为 Streamlit Web MVP 部署到 Streamlit Cloud。部署入口文件是：

```text
app.py
```

部署前请确认仓库中包含：

- `app.py`
- `requirements.txt`
- `packages.txt`
- `.env.example`
- `.gitignore`
- `README.md`

`requirements.txt` 用于安装 Python 依赖，`packages.txt` 用于在云端安装截图 OCR 需要的系统依赖：

```text
tesseract-ocr
tesseract-ocr-chi-sim
```

部署步骤：

1. 将项目推送到 GitHub 仓库。
2. 打开 Streamlit Cloud，新建 App。
3. 选择对应 GitHub 仓库。
4. Main file path 填写：

```text
app.py
```

5. 在 Streamlit Cloud 的 Secrets 中配置环境变量，不要上传 `.env`。

Secrets 示例：

```toml
DEEPSEEK_API_KEY = "your_api_key_here"
FEISHU_APP_ID = "your_app_id_here"
FEISHU_APP_SECRET = "your_app_secret_here"
FEISHU_APP_TOKEN = "your_bitable_app_token_here"
FEISHU_TABLE_ID = "your_table_id_here"
```

飞书同步需要以下环境变量：

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_APP_TOKEN`
- `FEISHU_TABLE_ID`

DeepSeek AI 解析和分析需要：

- `DEEPSEEK_API_KEY`

截图识别需要：

- `QWEN_API_KEY`
- `QWEN_VL_MODEL`

`QWEN_API_KEY` 是阿里云百炼账号级调用凭证，不是某个模型专属 Key。`QWEN_VL_MODEL` 未配置时，应用默认使用 `qwen3.6-plus`。

部署后测试截图上传：

1. 用手机浏览器打开 Streamlit Cloud 生成的公开网址。
2. 在 Boss 直聘手机端截取岗位页、公司介绍页或 HR 聊天页。
3. 回到 BossPilot 页面，进入“截图上传解析”。
4. 上传 1-10 张截图，建议 2-5 张。
5. 点击“AI读取截图并生成记录”。
6. 检查表单是否被自动填充。
7. 如需岗位价值判断，点击“AI岗位深度诊断”。
8. 确认无误后点击“保存记录”。

注意：Streamlit Cloud 的本地文件系统不适合作为长期数据库。`data/job_records.csv` 适合 Web MVP 测试，正式长期使用建议以飞书多维表格或数据库作为主存储。

## 从 wiki 链接获取飞书多维表格 App Token

如果飞书多维表格链接是 wiki 类型，例如：

```text
https://ucndxi5Oz4w3.feishu.cn/wiki/KXlzwMEMtidcVWkKEOicN76In3L
```

其中 `wiki/` 后面的 `KXlzwMEMtidcVWkKEOicN76In3L` 是 `wiki_node_token`，不是多维表格的 `FEISHU_APP_TOKEN`。

可以使用脚本从 wiki 节点获取真正的多维表格 `obj_token`：

```bash
python scripts/get_feishu_bitable_token.py KXlzwMEMtidcVWkKEOicN76In3L
```

如果不在命令中传 token，脚本会提示手动输入：

```bash
python scripts/get_feishu_bitable_token.py
```

脚本会读取项目根目录 `.env` 中的：

```env
FEISHU_APP_ID=your_app_id_here
FEISHU_APP_SECRET=your_app_secret_here
```

如果返回结果中 `obj_type` 是 `bitable`，请将打印出来的 `obj_token` 填入 `.env`：

```env
FEISHU_APP_TOKEN=这里填写 obj_token
```

## Chrome 插件安装方法

项目提供一个本地 Chrome 插件 MVP，目录为 `browser_extension/`。

安装步骤：

1. 打开 Chrome 扩展程序页面：`chrome://extensions/`
2. 打开右上角“开发者模式”
3. 点击“加载已解压的扩展程序”
4. 选择项目中的 `browser_extension` 文件夹
5. 打开 Boss 直聘网页版岗位详情页
6. 点击浏览器工具栏中的 BossPilot 插件按钮
7. 点击“发送到 BossPilot 分析”
8. 浏览器会自动跳转到 BossPilot 分析页面

插件默认发送到本地开发地址：

```js
const BOSSPILOT_URL = "http://localhost:8501";
```

部署后可以在 `browser_extension/popup.js` 中改为：

```js
const BOSSPILOT_URL = "https://bosspilot-yij7.streamlit.app";
```

插件只读取用户当前打开页面的可见文本，不自动登录 Boss 直聘，不批量采集岗位，也不绕过平台权限。

## 求职会话监控模式

会话监控模式适合电脑端连续浏览多个 Boss 岗位后统一导入。该模式只在用户点击“开始监控”后采集 `zhipin.com` 域名页面，并且只有点击“结束并上传”后才会把本次会话发送到本地接收器。

使用步骤：

1. 启动本地接收器：

```bash
python local_receiver.py
```

接收器默认监听：

```text
http://127.0.0.1:8765/api/import-session
```

2. 启动 BossPilot：

```bash
streamlit run app.py
```

3. Chrome 加载 `browser_extension/` 文件夹。
4. 打开 Boss 直聘网页版。
5. 点击插件“开始监控”。
6. 正常浏览岗位列表、岗位详情、公司页或聊天页。
7. 点击插件“结束并上传”。
8. 回到 BossPilot 页面，在“导入浏览器监控会话”中选择本次会话。
9. 点击“导入并分析本次会话”。

导入后系统会：

- 清洗并去重本次会话页面。
- 优先解析岗位详情页；如果只有列表页，则只提取页面中最明确的岗位。
- 聊天页不会单独生成岗位记录，会尝试合并到匹配岗位；无法匹配的聊天会放入“未匹配聊天记录”折叠区。
- 每条岗位独立调用解析和岗位诊断，不会把整场会话一次性发送给 AI。
- 保存到本地 CSV；飞书配置完整时会尝试同步到飞书。

注意：会话文件会保存到 `data/extension_sessions/`。如果重复导入同一会话，BossPilot 会按岗位链接或公司名+岗位名+薪资+地点跳过重复记录。

## 后续迭代计划

- AI 分析：对岗位信息和聊天记录进行总结、意向判断、风险提示和跟进建议。
- 飞书同步：将本地投递记录同步到飞书多维表格或飞书文档。
- 截图 OCR：支持用户上传截图，并从截图中识别岗位信息或聊天内容。
