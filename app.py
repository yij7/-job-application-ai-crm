from pathlib import Path
import base64
import json
import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv


DATA_DIR = Path("data")
CSV_FILE = DATA_DIR / "job_records.csv"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
QWEN_VL_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
FEISHU_CREATE_RECORD_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
FEISHU_BATCH_DELETE_RECORD_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_delete"
FEISHU_FIELDS_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"

COLUMNS = [
    "公司名",
    "岗位名",
    "岗位方向",
    "薪资",
    "地点",
    "投递平台",
    "投递状态",
    "备注",
    "聊天记录文本",
    "岗位优先级",
    "AI岗位匹配度",
    "AI岗位类型",
    "AI风险点",
    "AI下一步建议",
    "AI建议回复话术",
    "产品相关度",
    "AI数据SaaS相关度",
    "简历增值程度",
    "低价值杂活风险",
    "成长路径清晰度",
    "综合优先级",
    "岗位真实类型判断",
    "是否值得继续沟通",
    "需要追问HR的3个关键问题",
    "面试表达建议",
    "建议回复话术",
    "判断理由",
    "解析置信度",
    "解析说明",
    "飞书同步状态",
    "飞书同步时间",
]

STATUS_OPTIONS = ["", "待补充", "待投递", "已投递", "沟通中", "面试中", "已录用", "已拒绝", "已结束"]
FILTER_STATUS_OPTIONS = ["全部", "待投递", "已投递", "沟通中", "面试中", "已录用", "已拒绝", "已结束"]
AI_MATCH_FILTER_OPTIONS = ["全部", "高", "中", "低"]
AI_JOB_TYPE_FILTER_OPTIONS = ["全部", "AI产品", "产品助理", "产品运营", "项目助理", "数据分析", "低价值岗位", "未知"]
AI_JOB_TYPE_KEYWORDS = {
    "AI产品": [
        "AI产品",
        "人工智能产品",
        "AI 产品助理",
        "AI工具",
        "智能产品",
        "AIGC",
        "ChatGPT",
        "DeepSeek",
        "SaaS产品",
        "B端AI",
        "AI应用",
    ],
    "产品助理": [
        "产品助理",
        "产品实习生",
        "助理产品经理",
        "产品经理助理",
        "需求分析",
        "PRD",
        "原型",
        "竞品分析",
    ],
    "产品运营": [
        "产品运营",
        "用户运营",
        "增长运营",
        "SaaS运营",
        "内容运营",
        "活动运营",
        "用户反馈",
    ],
    "项目助理": [
        "项目助理",
        "项目运营",
        "项目管理",
        "交付",
        "客户需求",
        "进度跟进",
        "风险跟踪",
    ],
    "数据分析": [
        "数据分析",
        "数据运营",
        "BI",
        "看板",
        "指标",
        "SQL",
        "Excel",
        "报表",
        "数据统计",
    ],
    "低价值岗位": [
        "销售",
        "客服",
        "社群维护",
        "地推",
        "电话销售",
        "纯剪辑",
        "纯发布",
        "行政",
        "拉群",
        "私域转化",
    ],
}
AI_JOB_TYPE_SEARCH_COLUMNS = ["AI岗位类型", "岗位真实类型判断", "岗位名", "岗位方向", "备注", "判断理由"]
PRIORITY_OPTIONS = ["", "高优先级", "中优先级", "低优先级", "暂不跟进"]
PRIORITY_SORT_ORDER = {"高优先级": 0, "中优先级": 1, "低优先级": 2, "暂不跟进": 3}
AI_MATCH_SORT_ORDER = {"高": 0, "中": 1, "低": 2}
FEISHU_SYNC_FIELDS = [
    "公司名",
    "岗位名",
    "岗位方向",
    "薪资",
    "地点",
    "投递平台",
    "投递状态",
    "岗位优先级",
    "备注",
    "聊天记录文本",
    "产品相关度",
    "AI数据SaaS相关度",
    "简历增值程度",
    "低价值杂活风险",
    "成长路径清晰度",
    "综合优先级",
    "岗位真实类型判断",
    "是否值得继续沟通",
    "需要追问HR的3个关键问题",
    "面试表达建议",
    "建议回复话术",
    "判断理由",
]

FIELD_KEYS = {
    "公司名": "company_name",
    "岗位名": "job_title",
    "岗位方向": "job_direction",
    "薪资": "salary",
    "地点": "location",
    "投递平台": "platform",
    "投递状态": "status",
    "岗位优先级": "priority",
    "备注": "notes",
    "聊天记录文本": "chat_text",
}

AI_FIELD_KEYS = {
    "AI岗位匹配度": "ai_match_level",
    "AI岗位类型": "ai_job_type",
    "AI风险点": "ai_risks",
    "AI下一步建议": "ai_next_step",
    "AI建议回复话术": "ai_reply",
}

DIAGNOSIS_FIELD_KEYS = {
    "产品相关度": "product_relevance",
    "AI数据SaaS相关度": "ai_data_saas_relevance",
    "简历增值程度": "resume_value",
    "低价值杂活风险": "low_value_risk",
    "成长路径清晰度": "growth_clarity",
    "综合优先级": "overall_priority",
    "岗位真实类型判断": "real_job_type",
    "是否值得继续沟通": "worth_following",
    "需要追问HR的3个关键问题": "hr_questions",
    "面试表达建议": "interview_advice",
    "建议回复话术": "reply_script",
    "判断理由": "reasoning",
    "解析置信度": "parse_confidence",
    "解析说明": "parse_notes",
}

ALL_AI_COLUMNS = list(AI_FIELD_KEYS.keys()) + list(DIAGNOSIS_FIELD_KEYS.keys())


def ensure_csv_file():
    DATA_DIR.mkdir(exist_ok=True)
    if not CSV_FILE.exists():
        empty_df = pd.DataFrame(columns=COLUMNS)
        empty_df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")


def read_records():
    ensure_csv_file()
    records_df = pd.read_csv(CSV_FILE, encoding="utf-8-sig", keep_default_na=False)

    csv_changed = False
    for column in COLUMNS:
        if column not in records_df.columns:
            records_df[column] = ""
            csv_changed = True

    records_df = records_df[COLUMNS].fillna("")
    if csv_changed:
        records_df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

    return records_df


def save_records(records_df):
    records_df = records_df.fillna("")
    records_df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")


def clear_local_records():
    records_df = read_records()
    deleted_count = len(records_df)
    empty_df = pd.DataFrame(columns=COLUMNS)
    save_records(empty_df)
    return deleted_count


def clean_value(value):
    if value is None:
        return ""
    return str(value).strip()


def get_config_value(key):
    value = os.getenv(key, "").strip()
    if value:
        return value

    try:
        return str(st.secrets.get(key, "")).strip()
    except Exception:
        return ""


def get_form_record():
    record = {
        "公司名": clean_value(st.session_state.company_name),
        "岗位名": clean_value(st.session_state.job_title),
        "岗位方向": clean_value(st.session_state.job_direction),
        "薪资": clean_value(st.session_state.salary),
        "地点": clean_value(st.session_state.location),
        "投递平台": clean_value(st.session_state.platform),
        "投递状态": clean_value(st.session_state.status),
        "备注": clean_value(st.session_state.notes),
        "聊天记录文本": clean_value(st.session_state.chat_text),
        "岗位优先级": clean_value(st.session_state.priority),
        "AI岗位匹配度": clean_value(st.session_state.ai_match_level),
        "AI岗位类型": clean_value(st.session_state.ai_job_type),
        "AI风险点": clean_value(st.session_state.ai_risks),
        "AI下一步建议": clean_value(st.session_state.ai_next_step),
        "AI建议回复话术": clean_value(st.session_state.ai_reply),
        "飞书同步状态": "",
        "飞书同步时间": "",
    }

    for column, key in DIAGNOSIS_FIELD_KEYS.items():
        record[column] = clean_value(st.session_state[key])

    return record


def load_record_to_form(row_index):
    records_df = read_records()
    selected_record = records_df.iloc[row_index]

    for column, key in FIELD_KEYS.items():
        st.session_state[key] = clean_value(selected_record[column])

    for column, key in AI_FIELD_KEYS.items():
        st.session_state[key] = clean_value(selected_record[column])

    for column, key in DIAGNOSIS_FIELD_KEYS.items():
        st.session_state[key] = clean_value(selected_record[column])

    if st.session_state.status not in STATUS_OPTIONS:
        st.session_state.status = STATUS_OPTIONS[0]

    if st.session_state.priority not in PRIORITY_OPTIONS:
        st.session_state.priority = ""

    st.session_state.edit_index = row_index


def parse_raw_text(raw_text):
    label_map = {
        "公司名": "公司名",
        "公司名称": "公司名",
        "岗位名": "岗位名",
        "岗位名称": "岗位名",
        "岗位方向": "岗位方向",
        "薪资": "薪资",
        "地点": "地点",
        "投递平台": "投递平台",
        "投递状态": "投递状态",
        "岗位优先级": "岗位优先级",
        "备注": "备注",
        "聊天记录": "聊天记录文本",
        "聊天记录文本": "聊天记录文本",
    }

    parsed_data = {}
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        if "：" in line:
            label, value = line.split("：", 1)
        elif ":" in line:
            label, value = line.split(":", 1)
        else:
            continue

        label = label.strip()
        value = value.strip()

        if label in label_map:
            parsed_data[label_map[label]] = value

    return parsed_data


def fill_form_from_raw_text():
    parsed_data = parse_raw_text(st.session_state.raw_job_text)

    for column in FIELD_KEYS:
        key = FIELD_KEYS[column]
        st.session_state[key] = clean_value(parsed_data.get(column, ""))

    if st.session_state.status not in STATUS_OPTIONS:
        st.session_state.status = ""

    if st.session_state.priority not in PRIORITY_OPTIONS:
        st.session_state.priority = ""


def get_value_from_record(record, column):
    if record is None:
        return clean_value(get_form_record().get(column, ""))
    return clean_value(record.get(column, ""))


def build_deep_diagnosis_prompt(record=None):
    return f"""
你是一个专注产品/AI产品/产品运营/项目助理实习方向的求职诊断助手。
请只分析产品相关实习机会，不要做全行业通用建议。
请只返回合法 JSON，不要返回 Markdown，不要解释 JSON 之外的内容。

必须返回以下字段：
{{
  "产品相关度": 0,
  "AI数据SaaS相关度": 0,
  "简历增值程度": 0,
  "低价值杂活风险": 0,
  "成长路径清晰度": 0,
  "综合优先级": "高/中/低/放弃",
  "岗位真实类型判断": "",
  "是否值得继续沟通": "是/否/观察",
  "需要追问HR的3个关键问题": [],
  "面试表达建议": "",
  "建议回复话术": "",
  "判断理由": ""
}}

评分规则：
- 0 分表示完全不相关或风险极高，5 分表示非常相关或质量很高。
- 低价值杂活风险分数越高，表示越可能是发帖、拉群、销售转化、打杂、纯执行。
- 综合优先级只能从 高 / 中 / 低 / 放弃 中选择。

岗位信息：
公司名：{get_value_from_record(record, "公司名")}
岗位名：{get_value_from_record(record, "岗位名")}
岗位方向：{get_value_from_record(record, "岗位方向")}
薪资：{get_value_from_record(record, "薪资")}
地点：{get_value_from_record(record, "地点")}
投递平台：{get_value_from_record(record, "投递平台")}
投递状态：{get_value_from_record(record, "投递状态")}
备注：{get_value_from_record(record, "备注")}
聊天记录文本：{get_value_from_record(record, "聊天记录文本")}
"""


def build_smart_parse_prompt(raw_text):
    return f"""
你是一个专注产品/AI产品/产品运营/项目助理实习方向的求职信息解析助手。
请从用户粘贴的 BOSS 岗位详情、公司介绍、HR 聊天记录、岗位描述和混合文本中提取信息，并做产品岗深度诊断。
请只返回合法 JSON，不要返回 Markdown，不要解释 JSON 之外的内容。

无法识别的文本字段返回空字符串，无法判断的分数字段返回 0。

必须返回以下字段：
{{
  "公司名": "",
  "岗位名": "",
  "岗位方向": "",
  "薪资": "",
  "地点": "",
  "投递平台": "",
  "投递状态": "",
  "岗位优先级": "",
  "备注": "",
  "聊天记录文本": "",
  "解析置信度": "高/中/低",
  "解析说明": "",
  "产品相关度": 0,
  "AI数据SaaS相关度": 0,
  "简历增值程度": 0,
  "低价值杂活风险": 0,
  "成长路径清晰度": 0,
  "综合优先级": "高/中/低/放弃",
  "岗位真实类型判断": "",
  "是否值得继续沟通": "是/否/观察",
  "需要追问HR的3个关键问题": [],
  "面试表达建议": "",
  "建议回复话术": "",
  "判断理由": ""
}}

字段要求：
- 岗位优先级只能从 高优先级 / 中优先级 / 低优先级 / 暂不跟进 / 空字符串 中选择。
- 投递状态只能从 待投递 / 已投递 / 沟通中 / 面试中 / 已录用 / 已拒绝 / 已结束 / 空字符串 中选择。
- 解析置信度只能从 高 / 中 / 低 中选择。
- 需要追问HR的3个关键问题必须是数组，最多 3 条。

原始文本：
{raw_text}
"""


def parse_ai_response(content):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        json_start = content.find("{")
        json_end = content.rfind("}")
        if json_start != -1 and json_end != -1:
            return json.loads(content[json_start : json_end + 1])
        raise


def call_deepseek_json(prompt):
    api_key = get_config_value("DEEPSEEK_API_KEY")
    if not api_key:
        return None, "请先配置 DEEPSEEK_API_KEY"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-v4-flash",
        "messages": [
            {
                "role": "system",
                "content": "你是一个产品岗求职分析助手，必须返回合法 JSON。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return parse_ai_response(content), ""
    except requests.exceptions.RequestException as error:
        return None, f"API 调用失败：{error}"
    except json.JSONDecodeError:
        return None, "AI解析失败，请检查原始文本或重试"
    except (KeyError, IndexError) as error:
        return None, f"AI 返回结果解析失败：{error}"


def analyze_job_with_deepseek(record=None):
    return call_deepseek_json(build_deep_diagnosis_prompt(record))


def smart_parse_with_deepseek(raw_text):
    return call_deepseek_json(build_smart_parse_prompt(raw_text))


def build_qwen_screenshot_prompt():
    return """
你是 Boss 直聘截图信息识别助手，只负责读图和提取结构化岗位信息，不做岗位价值分析。
请从用户上传的 Boss 岗位详情、公司介绍、HR 聊天截图中提取信息。
如果多张图信息互补，请合并判断。
请只返回合法 JSON，不要返回 Markdown，不要输出 JSON 之外的解释。

必须返回以下 JSON 字段：
{
  "公司名": "",
  "岗位名": "",
  "岗位方向": "",
  "薪资": "",
  "地点": "",
  "投递平台": "BOSS直聘",
  "投递状态": "",
  "岗位描述": "",
  "HR聊天记录": "",
  "识别置信度": "高/中/低",
  "缺失字段": [],
  "识别说明": ""
}

规则：
- 无法识别的文本字段返回空字符串。
- 投递平台如果截图来自 Boss 直聘，填 BOSS直聘。
- 缺失字段必须是数组。
- 不要臆造公司名和岗位名。
"""


def get_uploaded_image_data_url(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    file_type = uploaded_file.type or "image/jpeg"
    image_base64 = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{file_type};base64,{image_base64}"


def call_qwen_vision_for_screenshots(uploaded_files):
    api_key = get_config_value("QWEN_API_KEY")
    if not api_key:
        return None, "未配置 Qwen 视觉模型，截图识别不可用。请使用粘贴文本解析，或在 .env / Streamlit Secrets 中配置 QWEN_API_KEY。"

    model = get_config_value("QWEN_VL_MODEL") or "qwen3.6-plus"
    content = [{"type": "text", "text": build_qwen_screenshot_prompt()}]

    for uploaded_file in uploaded_files:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": get_uploaded_image_data_url(uploaded_file)},
            }
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(QWEN_VL_API_URL, headers=headers, json=payload, timeout=60)
        print(f"Qwen视觉模型 response.status_code: {response.status_code}")
        print(f"Qwen视觉模型 response.text: {response.text}")

        if response.status_code != 200:
            return None, f"Qwen视觉模型调用失败：{response.text}"

        result = response.json()
        content_text = result["choices"][0]["message"]["content"]
        return parse_ai_response(content_text), ""
    except requests.exceptions.RequestException as error:
        return None, f"Qwen视觉模型调用失败：{error}"
    except (KeyError, IndexError, json.JSONDecodeError) as error:
        return None, f"Qwen视觉模型返回解析失败：{error}"


def save_ai_result_to_session(ai_result):
    st.session_state.ai_match_level = convert_priority_to_match_level(ai_result.get("综合优先级", ""))
    st.session_state.ai_job_type = clean_value(ai_result.get("岗位真实类型判断", ""))
    st.session_state.ai_risks = clean_value(ai_result.get("判断理由", ""))
    st.session_state.ai_next_step = clean_value(ai_result.get("是否值得继续沟通", ""))
    st.session_state.ai_reply = clean_value(ai_result.get("建议回复话术", ""))

    for column, key in DIAGNOSIS_FIELD_KEYS.items():
        value = ai_result.get(column, "")
        st.session_state[key] = clean_ai_value(value)


def get_ai_record_from_result(ai_result):
    ai_record = {
        "AI岗位匹配度": convert_priority_to_match_level(ai_result.get("综合优先级", "")),
        "AI岗位类型": clean_value(ai_result.get("岗位真实类型判断", "")),
        "AI风险点": clean_value(ai_result.get("判断理由", "")),
        "AI下一步建议": clean_value(ai_result.get("是否值得继续沟通", "")),
        "AI建议回复话术": clean_value(ai_result.get("建议回复话术", "")),
    }

    for column in DIAGNOSIS_FIELD_KEYS:
        ai_record[column] = clean_ai_value(ai_result.get(column, ""))

    return ai_record


def clean_ai_value(value):
    if isinstance(value, list):
        return "\n".join(clean_value(item) for item in value if clean_value(item))
    return clean_value(value)


def convert_priority_to_match_level(priority):
    priority = clean_value(priority)
    if priority == "高":
        return "高"
    if priority == "中":
        return "中"
    if priority in ["低", "放弃"]:
        return "低"
    return ""


def fill_form_from_ai_parse(ai_result):
    for column, key in FIELD_KEYS.items():
        st.session_state[key] = clean_value(ai_result.get(column, ""))

    if not st.session_state.priority or st.session_state.priority not in PRIORITY_OPTIONS:
        st.session_state.priority = convert_overall_priority_to_record_priority(ai_result.get("综合优先级", ""))

    if st.session_state.status not in STATUS_OPTIONS:
        st.session_state.status = ""

    if st.session_state.priority not in PRIORITY_OPTIONS:
        st.session_state.priority = ""

    save_ai_result_to_session(ai_result)


def fill_form_from_qwen_result(qwen_result):
    field_mapping = {
        "公司名": "company_name",
        "岗位名": "job_title",
        "岗位方向": "job_direction",
        "薪资": "salary",
        "地点": "location",
        "投递平台": "platform",
        "投递状态": "status",
    }

    for result_key, session_key in field_mapping.items():
        value = clean_value(qwen_result.get(result_key, ""))
        st.session_state[session_key] = value or "待补充"

    st.session_state.notes = clean_value(qwen_result.get("岗位描述", "")) or "待补充"
    st.session_state.chat_text = clean_value(qwen_result.get("HR聊天记录", ""))

    if not clean_value(st.session_state.status) or st.session_state.status not in STATUS_OPTIONS:
        st.session_state.status = "待补充" if "待补充" in STATUS_OPTIONS else ""


def convert_overall_priority_to_record_priority(priority):
    priority = clean_value(priority)
    priority_map = {
        "高": "高优先级",
        "中": "中优先级",
        "低": "低优先级",
        "放弃": "暂不跟进",
    }
    return priority_map.get(priority, "")


def extract_text_from_image(uploaded_file):
    try:
        from PIL import Image
        import pytesseract

        image = Image.open(uploaded_file)
        try:
            text = pytesseract.image_to_string(image, lang="chi_sim+eng")
        except pytesseract.TesseractError:
            text = pytesseract.image_to_string(image)
        return clean_value(text), ""
    except ImportError as error:
        return "", f"OCR 依赖未安装：{error}"
    except Exception as error:
        return "", f"{uploaded_file.name}: {error}"


def extract_text_from_uploaded_images(uploaded_files):
    extracted_texts = []
    error_messages = []

    for index, uploaded_file in enumerate(uploaded_files, start=1):
        text, error_message = extract_text_from_image(uploaded_file)
        if text:
            extracted_texts.append(f"截图{index}识别内容：\n{text}")
        if error_message:
            error_messages.append(error_message)

    return "\n\n".join(extracted_texts), error_messages


def fill_missing_screenshot_fields():
    fields_to_fill = [
        "company_name",
        "job_title",
        "job_direction",
        "salary",
        "location",
        "platform",
        "notes",
    ]

    for key in fields_to_fill:
        if not clean_value(st.session_state[key]):
            st.session_state[key] = "待补充"

    if st.session_state.status not in STATUS_OPTIONS:
        st.session_state.status = ""

def clear_ai_result_from_session():
    for key in list(AI_FIELD_KEYS.values()) + list(DIAGNOSIS_FIELD_KEYS.values()):
        st.session_state[key] = ""


def clear_ai_result_from_record(records_df, row_index):
    for column in ALL_AI_COLUMNS:
        records_df.loc[row_index, column] = ""
    return records_df


def filter_records(records_df, status_filter, ai_match_filter, ai_job_type_filter, keyword):
    filtered_df = records_df.copy()

    if status_filter != "全部":
        filtered_df = filtered_df[filtered_df["投递状态"] == status_filter]

    if ai_match_filter != "全部":
        filtered_df = filtered_df[filtered_df["AI岗位匹配度"] == ai_match_filter]

    if ai_job_type_filter != "全部":
        job_type_mask = filtered_df.apply(
            lambda row: match_ai_job_type_filter(row, ai_job_type_filter),
            axis=1,
        )
        filtered_df = filtered_df[job_type_mask]

    keyword = clean_value(keyword)
    if keyword:
        search_columns = ["公司名", "岗位名", "岗位方向", "备注", "聊天记录文本"]
        keyword_mask = filtered_df[search_columns].apply(
            lambda row: row.astype(str).str.contains(keyword, case=False, na=False).any(),
            axis=1,
        )
        filtered_df = filtered_df[keyword_mask]

    return filtered_df


def match_ai_job_type_filter(row, ai_job_type_filter):
    search_text = " ".join(clean_value(row.get(column, "")) for column in AI_JOB_TYPE_SEARCH_COLUMNS)

    if ai_job_type_filter == "未知":
        return not clean_value(search_text)

    keywords = AI_JOB_TYPE_KEYWORDS.get(ai_job_type_filter, [])
    search_text_lower = search_text.lower()

    return any(keyword.lower() in search_text_lower for keyword in keywords)


def sort_records(records_df):
    sorted_df = records_df.copy()
    sorted_df["_priority_sort"] = sorted_df["岗位优先级"].map(PRIORITY_SORT_ORDER).fillna(99)
    sorted_df["_ai_match_sort"] = sorted_df["AI岗位匹配度"].map(AI_MATCH_SORT_ORDER).fillna(99)
    sorted_df = sorted_df.sort_values(by=["_priority_sort", "_ai_match_sort"], kind="stable")
    return sorted_df.drop(columns=["_priority_sort", "_ai_match_sort"])


def get_feishu_config():
    return {
        "app_id": get_config_value("FEISHU_APP_ID"),
        "app_secret": get_config_value("FEISHU_APP_SECRET"),
        "app_token": get_config_value("FEISHU_APP_TOKEN"),
        "table_id": get_config_value("FEISHU_TABLE_ID"),
    }


def check_feishu_config(config):
    missing_keys = [key for key, value in config.items() if not value]
    if missing_keys:
        missing_text = "、".join(missing_keys)
        return f"飞书同步失败：缺少配置 {missing_text}。本地保存不受影响。"
    return ""


def get_feishu_config_status_text():
    config = get_feishu_config()
    labels = {
        "app_id": "FEISHU_APP_ID",
        "app_secret": "FEISHU_APP_SECRET",
        "app_token": "FEISHU_APP_TOKEN",
        "table_id": "FEISHU_TABLE_ID",
    }
    status_lines = []
    for key, label in labels.items():
        status = "已配置" if clean_value(config.get(key, "")) else "未配置"
        status_lines.append(f"{label}：{status}")
    return "\n".join(status_lines)


def translate_feishu_error(response_text):
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        return "飞书同步失败：接口返回异常。本地保存不受影响。"

    code = result.get("code")
    msg = clean_value(result.get("msg", ""))
    error_text = f"{code} {msg}".upper()

    if code == 91402 or "NOTEXIST" in error_text:
        return (
            "飞书同步失败：未找到对应的多维表格或数据表。"
            "请检查 Streamlit Secrets 中的 FEISHU_APP_TOKEN 和 FEISHU_TABLE_ID 是否与当前飞书表一致，"
            "也可能是表格权限不足。本地保存不受影响。"
        )

    if "FIELDNAMENOTFOUND" in error_text:
        return "飞书同步失败：飞书表格缺少字段。请先运行字段检查脚本或在飞书中补齐字段。本地保存不受影响。"

    if code:
        return f"飞书同步失败：{msg or '飞书接口返回错误'}（错误码 {code}）。本地保存不受影响。"

    return "飞书同步失败：请检查飞书配置和表格权限。本地保存不受影响。"


def get_feishu_tenant_access_token(config):
    payload = {
        "app_id": config["app_id"],
        "app_secret": config["app_secret"],
    }

    response = requests.post(FEISHU_TOKEN_URL, json=payload, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(translate_feishu_error(response.text))

    result = response.json()

    if result.get("code") != 0:
        raise RuntimeError(translate_feishu_error(response.text))

    return result["tenant_access_token"]


def build_feishu_fields(record):
    return {
        column: clean_value(record.get(column, ""))
        for column in FEISHU_SYNC_FIELDS
    }


def get_feishu_fields_url(config):
    return FEISHU_FIELDS_URL.format(
        app_token=config["app_token"],
        table_id=config["table_id"],
    )


def get_feishu_field_names(config, tenant_access_token):
    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
    }
    url = get_feishu_fields_url(config)
    response = requests.get(url, headers=headers, timeout=30)
    print(f"飞书字段列表 response.status_code: {response.status_code}")
    print(f"飞书字段列表 response.text: {response.text}")

    if response.status_code != 200:
        raise RuntimeError(translate_feishu_error(response.text))

    result = response.json()
    if result.get("code") != 0:
        raise RuntimeError(translate_feishu_error(response.text))

    fields = result.get("data", {}).get("items", [])
    return {field.get("field_name", "") for field in fields if field.get("field_name")}


def sync_record_to_feishu(record):
    config = get_feishu_config()
    config_error = check_feishu_config(config)
    if config_error:
        return config_error

    try:
        tenant_access_token = get_feishu_tenant_access_token(config)
        headers = {
            "Authorization": f"Bearer {tenant_access_token}",
            "Content-Type": "application/json",
        }
        url = FEISHU_CREATE_RECORD_URL.format(
            app_token=config["app_token"],
            table_id=config["table_id"],
        )
        feishu_field_names = get_feishu_field_names(config, tenant_access_token)
        payload_fields = build_feishu_fields(record)
        payload_field_names = set(payload_fields.keys())
        missing_fields = sorted(payload_field_names - feishu_field_names)

        print(f"飞书实际字段名列表: {sorted(feishu_field_names)}")
        print(f"本次准备写入的字段名列表: {sorted(payload_field_names)}")

        if missing_fields:
            return f"同步失败：以下字段在飞书中不存在：{', '.join(missing_fields)}"

        payload = {"fields": payload_fields}

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"飞书写入记录 response.status_code: {response.status_code}")
        print(f"飞书写入记录 response.text: {response.text}")

        if response.status_code != 200:
            return translate_feishu_error(response.text)

        result = response.json()

        if result.get("code") != 0:
            return translate_feishu_error(response.text)

        return ""
    except requests.exceptions.RequestException as error:
        return f"飞书同步失败：网络请求异常，请稍后重试。本地保存不受影响。{error}"
    except (KeyError, RuntimeError) as error:
        return str(error)


def get_feishu_records_url(config):
    return FEISHU_CREATE_RECORD_URL.format(
        app_token=config["app_token"],
        table_id=config["table_id"],
    )


def get_feishu_batch_delete_url(config):
    return FEISHU_BATCH_DELETE_RECORD_URL.format(
        app_token=config["app_token"],
        table_id=config["table_id"],
    )


def list_feishu_record_ids(config, tenant_access_token):
    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
    }
    url = get_feishu_records_url(config)
    record_ids = []
    page_token = ""

    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token

        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"飞书读取记录 response.status_code: {response.status_code}")
        print(f"飞书读取记录 response.text: {response.text}")

        if response.status_code != 200:
            return record_ids, (
                "飞书读取记录失败：\n"
                f"请求 URL: {response.url}\n"
                f"response.status_code: {response.status_code}\n"
                f"response.text: {response.text}"
            )

        result = response.json()
        if result.get("code") != 0:
            return record_ids, (
                "飞书读取记录失败：\n"
                f"请求 URL: {response.url}\n"
                f"response.status_code: {response.status_code}\n"
                f"response.text: {response.text}"
            )

        data = result.get("data", {})
        for item in data.get("items", []):
            record_id = item.get("record_id", "")
            if record_id:
                record_ids.append(record_id)

        if not data.get("has_more"):
            break

        page_token = data.get("page_token", "")
        if not page_token:
            break

    return record_ids, ""


def delete_feishu_records(config, tenant_access_token, record_ids):
    if not record_ids:
        return 0, "飞书暂无记录", ""

    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json",
    }
    url = get_feishu_batch_delete_url(config)
    deleted_count = 0

    for start_index in range(0, len(record_ids), 500):
        batch_record_ids = record_ids[start_index : start_index + 500]
        payload = {"records": batch_record_ids}
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"飞书批量删除 response.status_code: {response.status_code}")
        print(f"飞书批量删除 response.text: {response.text}")

        if response.status_code != 200:
            return deleted_count, "", (
                "飞书删除失败：\n"
                f"请求 URL: {url}\n"
                f"response.status_code: {response.status_code}\n"
                f"response.text: {response.text}"
            )

        result = response.json()
        if result.get("code") != 0:
            return deleted_count, "", (
                "飞书删除失败：\n"
                f"请求 URL: {url}\n"
                f"response.status_code: {response.status_code}\n"
                f"response.text: {response.text}"
            )

        deleted_count += len(batch_record_ids)

    return deleted_count, "", ""


def clear_feishu_records():
    config = get_feishu_config()
    config_error = check_feishu_config(config)
    if config_error:
        return 0, 0, "", config_error

    try:
        tenant_access_token = get_feishu_tenant_access_token(config)
        record_ids, list_error = list_feishu_record_ids(config, tenant_access_token)
        if list_error:
            return 0, len(record_ids), "", list_error

        deleted_count, info_message, delete_error = delete_feishu_records(config, tenant_access_token, record_ids)
        final_record_ids, final_list_error = list_feishu_record_ids(config, tenant_access_token)
        remaining_count = len(final_record_ids)

        if final_list_error:
            if delete_error:
                delete_error = f"{delete_error}\n\n删除后重新读取失败：{final_list_error}"
            else:
                delete_error = f"删除后重新读取失败：{final_list_error}"

        return deleted_count, remaining_count, info_message, delete_error
    except requests.exceptions.RequestException as error:
        return 0, 0, "", f"飞书删除失败：{error}"
    except (KeyError, RuntimeError) as error:
        return 0, 0, "", f"飞书删除失败：{error}"


ensure_csv_file()
load_dotenv()

st.set_page_config(page_title="AI 求职投递管理与沟通分析系统", layout="wide")
st.markdown(
    """
    <style>
    #MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"], .stDeployButton {
        visibility: hidden;
        height: 0;
    }
    .block-container {
        max-width: 980px;
        padding-top: 1.25rem;
    }
    h1 {
        font-size: 1.65rem !important;
        line-height: 1.2 !important;
    }
    h2, h3 {
        line-height: 1.25 !important;
    }
    div[data-testid="stAlert"] {
        border-radius: 8px;
    }
    @media (max-width: 640px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 0.75rem;
        }
        div[data-testid="stHorizontalBlock"] {
            flex-wrap: wrap;
        }
        div[data-testid="stHorizontalBlock"] > div {
            min-width: 100% !important;
        }
        .stDataFrame {
            overflow-x: auto;
        }
        .stButton button {
            width: 100%;
        }
        h1 {
            font-size: 1.35rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

if "pending_edit_index" not in st.session_state:
    st.session_state.pending_edit_index = None

if "success_message" not in st.session_state:
    st.session_state.success_message = ""

if "last_saved_index" not in st.session_state:
    st.session_state.last_saved_index = None

for field_key in FIELD_KEYS.values():
    if field_key not in st.session_state:
        st.session_state[field_key] = ""

for field_key in AI_FIELD_KEYS.values():
    if field_key not in st.session_state:
        st.session_state[field_key] = ""

for field_key in DIAGNOSIS_FIELD_KEYS.values():
    if field_key not in st.session_state:
        st.session_state[field_key] = ""

if st.session_state.status not in STATUS_OPTIONS:
    st.session_state.status = ""

if st.session_state.priority not in PRIORITY_OPTIONS:
    st.session_state.priority = ""

if "raw_job_text" not in st.session_state:
    st.session_state.raw_job_text = ""

if "smart_raw_text" not in st.session_state:
    st.session_state.smart_raw_text = ""

if st.session_state.pending_edit_index is not None:
    load_record_to_form(st.session_state.pending_edit_index)
    st.session_state.pending_edit_index = None

st.markdown("# BossPilot")
st.caption("AI 求职投递管理与岗位诊断系统")

if st.session_state.success_message:
    st.success(st.session_state.success_message)
    st.session_state.success_message = ""

st.info("飞书同步为可选功能；未配置或配置错误时，不影响截图识别和本地保存。")

st.subheader("推荐使用方式")
st.markdown(
    "- 手机端：适合上传 Boss 截图并快速生成记录\n"
    "- 电脑端：适合查看、筛选、编辑、同步飞书和复盘"
)

with st.container(border=True):
    st.subheader("截图上传")
    st.caption("建议上传 2–5 张 Boss 岗位截图 / 公司介绍 / HR 聊天截图，最多 8 张。")
    st.info("手机端建议先在相册中整理好截图，再一次性选择上传。")
    uploaded_images = st.file_uploader(
        "上传截图",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    if uploaded_images:
        st.caption("图片预览")
        preview_columns = st.columns(min(len(uploaded_images), 4))
        for index, uploaded_image in enumerate(uploaded_images):
            with preview_columns[index % len(preview_columns)]:
                st.image(uploaded_image, caption=uploaded_image.name, use_container_width=True)

    if st.button("AI读取截图并生成记录"):
        if not uploaded_images:
            st.warning("请先上传截图。")
        elif len(uploaded_images) > 8:
            st.warning("最多上传 8 张截图，请减少截图数量后重试。")
        else:
            with st.spinner("正在调用视觉模型读取截图..."):
                qwen_result, qwen_error = call_qwen_vision_for_screenshots(uploaded_images)

            if qwen_result:
                fill_form_from_qwen_result(qwen_result)
                with st.expander("视觉模型识别结果", expanded=False):
                    st.json(qwen_result)
                if len(uploaded_images) > 1:
                    st.info("已合并多张截图信息进行分析。")
                st.success("图片读取完成，请检查下方表单。")
                st.info("如需岗位价值判断，请继续点击下方“AI岗位深度诊断”。")
            elif qwen_error.startswith("未配置 Qwen 视觉模型"):
                st.warning(qwen_error)
            else:
                st.warning("视觉模型读取失败，正在尝试备用 OCR。")
                with st.spinner("正在使用备用 OCR 识别截图文字..."):
                    extracted_text, ocr_errors = extract_text_from_uploaded_images(uploaded_images)

                with st.expander("备用 OCR 识别到的原始文字", expanded=False):
                    st.text_area(
                        "OCR 原始文字",
                        value=extracted_text or "未识别到文字",
                        height=220,
                        disabled=True,
                    )

                if not extracted_text:
                    st.error("图片理解失败，请尝试粘贴岗位文字。")
                else:
                    if len(uploaded_images) > 1:
                        st.info("已合并多张截图信息进行分析。")

                    with st.spinner("正在根据 OCR 文字生成求职记录..."):
                        ai_result, error_message = smart_parse_with_deepseek(extracted_text)

                    if error_message:
                        st.error(error_message)
                    else:
                        fill_form_from_ai_parse(ai_result)
                        fill_missing_screenshot_fields()
                        st.success("图片读取完成，请检查下方表单。")
                        st.info("如需岗位价值判断，请继续点击下方“AI岗位深度诊断”。")

with st.container(border=True):
    st.subheader("智能粘贴解析")
    st.caption("截图识别不稳定时，粘贴岗位文字是最稳方式。")
    st.text_area(
        "粘贴岗位详情 / HR聊天记录 / 混合文本",
        height=180,
        key="smart_raw_text",
        placeholder="可以粘贴 BOSS 岗位详情、公司介绍、HR 聊天记录，或岗位描述和聊天混合文本。",
    )

    if st.button("AI解析并生成记录"):
        if not clean_value(st.session_state.smart_raw_text):
            st.warning("请先粘贴岗位详情或聊天记录。")
        else:
            with st.spinner("正在解析并诊断岗位..."):
                ai_result, error_message = smart_parse_with_deepseek(st.session_state.smart_raw_text)

            if error_message:
                st.error(error_message)
            else:
                fill_form_from_ai_parse(ai_result)
                st.success("AI解析完成，请向下确认表单，然后点击保存记录。")

st.subheader("粘贴岗位原始信息")
st.text_area(
    "粘贴岗位原始信息",
    height=140,
    key="raw_job_text",
    placeholder="例如：公司名：测试公司 岗位名：AI 产品助理 薪资：100-150/天 地点：杭州",
)

if st.button("一键解析并填充"):
    fill_form_from_raw_text()
    st.success("解析完成，已填充识别到的字段。")

form_title = "编辑投递记录" if st.session_state.edit_index is not None else "确认表单"
submit_text = "更新记录" if st.session_state.edit_index is not None else "保存记录"

with st.form("job_record_form"):
    st.subheader(form_title)

    col1, col2 = st.columns(2)

    with col1:
        st.text_input("公司名", key="company_name")
        st.text_input("岗位名", key="job_title")
        st.text_input("岗位方向", key="job_direction")
        st.text_input("薪资", key="salary")
        st.text_input("地点", key="location")

    with col2:
        st.text_input("投递平台", key="platform")
        st.selectbox("投递状态", STATUS_OPTIONS, key="status")
        st.selectbox("岗位优先级", PRIORITY_OPTIONS, key="priority")
        st.text_area("备注", height=120, key="notes")
        st.text_area("聊天记录文本", height=180, key="chat_text")

    ai_submitted = st.form_submit_button("AI岗位深度诊断")
    submitted = st.form_submit_button(submit_text)

    if ai_submitted:
        with st.spinner("正在分析岗位..."):
            ai_result, error_message = analyze_job_with_deepseek()

        if error_message:
            st.error(error_message)
        else:
            save_ai_result_to_session(ai_result)
            st.success("AI 分析完成。")

    if submitted:
        records_df = read_records()
        record = get_form_record()

        if st.session_state.edit_index is None:
            records_df = pd.concat([records_df, pd.DataFrame([record])], ignore_index=True)
            save_records(records_df)
            st.session_state.last_saved_index = len(records_df) - 1
            st.success("记录已保存")
            st.info("如需同步飞书，请点击下方同步按钮")
        else:
            current_edit_index = st.session_state.edit_index
            record["飞书同步状态"] = clean_value(records_df.loc[st.session_state.edit_index, "飞书同步状态"])
            record["飞书同步时间"] = clean_value(records_df.loc[st.session_state.edit_index, "飞书同步时间"])
            records_df.loc[st.session_state.edit_index, COLUMNS] = [record[column] for column in COLUMNS]
            save_records(records_df)
            st.session_state.edit_index = None
            st.session_state.last_saved_index = current_edit_index
            st.session_state.success_message = "记录已保存\n\n如需同步飞书，请点击下方同步按钮"
            st.rerun()

if st.session_state.last_saved_index is not None:
    records_df_for_sync = read_records()
    if 0 <= st.session_state.last_saved_index < len(records_df_for_sync):
        with st.container(border=True):
            st.subheader("保存与同步")
            st.success("记录已保存")
            st.caption("如需同步飞书，请点击下方同步按钮。飞书同步失败不会影响本地保存。")

            if st.button("同步刚保存的记录到飞书"):
                sync_index = st.session_state.last_saved_index
                record_to_sync = records_df_for_sync.iloc[sync_index]
                with st.spinner("正在同步到飞书..."):
                    error_message = sync_record_to_feishu(record_to_sync)

                if error_message:
                    st.error(error_message)
                    st.text(get_feishu_config_status_text())
                else:
                    records_df_for_sync.loc[sync_index, "飞书同步状态"] = "已同步"
                    records_df_for_sync.loc[sync_index, "飞书同步时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    save_records(records_df_for_sync)
                    st.success("同步到飞书成功")

st.subheader("AI 岗位分析结果")
if any(clean_value(st.session_state[key]) for key in list(AI_FIELD_KEYS.values()) + list(DIAGNOSIS_FIELD_KEYS.values())):
    score_col1, score_col2, score_col3, score_col4, score_col5 = st.columns(5)
    score_col1.metric("产品相关度", st.session_state.product_relevance or "0")
    score_col2.metric("AI/数据/SaaS相关度", st.session_state.ai_data_saas_relevance or "0")
    score_col3.metric("简历增值程度", st.session_state.resume_value or "0")
    score_col4.metric("低价值杂活风险", st.session_state.low_value_risk or "0")
    score_col5.metric("成长路径清晰度", st.session_state.growth_clarity or "0")

    diagnosis_df = pd.DataFrame(
        [
            {
                "综合优先级": st.session_state.overall_priority,
                "岗位真实类型判断": st.session_state.real_job_type,
                "是否值得继续沟通": st.session_state.worth_following,
                "解析置信度": st.session_state.parse_confidence,
                "解析说明": st.session_state.parse_notes,
                "判断理由": st.session_state.reasoning,
                "面试表达建议": st.session_state.interview_advice,
            }
        ]
    )
    st.dataframe(diagnosis_df, use_container_width=True, hide_index=True)

    st.markdown("**需要追问 HR 的 3 个关键问题**")
    questions = [question for question in st.session_state.hr_questions.splitlines() if clean_value(question)]
    if questions:
        for question in questions:
            st.markdown(f"- {question}")
    else:
        st.caption("暂无")

    st.markdown("**建议回复话术**")
    st.text_area("建议回复话术", value=st.session_state.reply_script, height=120, disabled=True)
else:
    st.info("还没有 AI 分析结果。")

if st.button("清空当前AI分析结果"):
    clear_ai_result_from_session()

    if st.session_state.edit_index is not None:
        records_df = read_records()
        records_df = clear_ai_result_from_record(records_df, st.session_state.edit_index)
        save_records(records_df)

    st.session_state.success_message = "AI分析结果已清空"
    st.rerun()

st.divider()
st.subheader("已保存的全部记录")

records_df = read_records()

if records_df.empty:
    st.info("还没有保存任何记录。")
else:
    st.markdown("**筛选记录**")
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 1.5, 2])
    with filter_col1:
        status_filter = st.selectbox("投递状态筛选", FILTER_STATUS_OPTIONS)
    with filter_col2:
        ai_match_filter = st.selectbox("AI岗位匹配度筛选", AI_MATCH_FILTER_OPTIONS)
    with filter_col3:
        ai_job_type_filter = st.selectbox("AI岗位类型筛选", AI_JOB_TYPE_FILTER_OPTIONS)
    with filter_col4:
        keyword = st.text_input("关键词搜索", placeholder="搜索公司名、岗位名、岗位方向、备注、聊天记录")

    display_df = filter_records(records_df, status_filter, ai_match_filter, ai_job_type_filter, keyword)
    display_df = sort_records(display_df)

    st.caption(f"当前显示 {len(display_df)} 条记录，共 {len(records_df)} 条记录。")

    if display_df.empty:
        st.info("没有符合筛选条件的记录。")

    for row_index, row in display_df.iterrows():
        with st.container(border=True):
            title = row["岗位名"] or "未填写岗位名"
            company = row["公司名"] or "未填写公司名"
            st.markdown(f"**{row_index + 1}. {company} - {title}**")

            st.dataframe(pd.DataFrame([row]), use_container_width=True, hide_index=True)

            current_priority = clean_value(row["岗位优先级"])
            if current_priority not in PRIORITY_OPTIONS:
                current_priority = ""

            priority_col, edit_col, delete_col, analyze_col, clear_ai_col, feishu_col = st.columns(
                [1.5, 1, 1, 1, 1, 1]
            )
            with priority_col:
                selected_priority = st.selectbox(
                    "岗位优先级",
                    PRIORITY_OPTIONS,
                    index=PRIORITY_OPTIONS.index(current_priority),
                    key=f"priority_{row_index}",
                )
                if selected_priority != current_priority:
                    records_df.loc[row_index, "岗位优先级"] = selected_priority
                    save_records(records_df)
                    st.session_state.success_message = "岗位优先级已更新。"
                    st.rerun()

            with edit_col:
                if st.button("编辑", key=f"edit_{row_index}"):
                    st.session_state.pending_edit_index = row_index
                    st.rerun()

            with delete_col:
                if st.button("删除", key=f"delete_{row_index}"):
                    records_df = records_df.drop(index=row_index).reset_index(drop=True)
                    save_records(records_df)
                    st.session_state.edit_index = None
                    st.session_state.success_message = "记录已删除。"
                    st.rerun()

            with analyze_col:
                if st.button("AI分析此记录", key=f"analyze_{row_index}"):
                    with st.spinner("正在分析该记录..."):
                        ai_result, error_message = analyze_job_with_deepseek(row)

                    if error_message:
                        st.error(error_message)
                    else:
                        ai_record = get_ai_record_from_result(ai_result)
                        records_df.loc[row_index, ALL_AI_COLUMNS] = [
                            ai_record[column] for column in ALL_AI_COLUMNS
                        ]
                        save_records(records_df)
                        if st.session_state.edit_index == row_index:
                            save_ai_result_to_session(ai_result)
                        st.session_state.success_message = "该记录AI分析已完成"
                        st.rerun()

            with clear_ai_col:
                if st.button("删除AI分析", key=f"clear_ai_{row_index}"):
                    records_df = clear_ai_result_from_record(records_df, row_index)
                    save_records(records_df)
                    if st.session_state.edit_index == row_index:
                        clear_ai_result_from_session()
                    st.session_state.success_message = "该记录AI分析结果已删除"
                    st.rerun()

            with feishu_col:
                if st.button("同步到飞书", key=f"feishu_{row_index}"):
                    already_synced = clean_value(row["飞书同步状态"]) == "已同步"
                    if clean_value(row["飞书同步状态"]) == "已同步":
                        st.info("该记录已同步过，本次将再次同步到飞书。")

                    with st.spinner("正在同步到飞书..."):
                        error_message = sync_record_to_feishu(row)

                    if error_message:
                        st.error(error_message)
                        st.text(get_feishu_config_status_text())
                    else:
                        records_df.loc[row_index, "飞书同步状态"] = "已同步"
                        records_df.loc[row_index, "飞书同步时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        save_records(records_df)
                        if already_synced:
                            st.session_state.success_message = "该记录已同步过，本次将再次同步到飞书。同步到飞书成功。"
                        else:
                            st.session_state.success_message = "同步到飞书成功。"
                        st.rerun()

st.divider()
st.subheader("危险操作")
confirm_clear_text = st.text_input(
    "输入“我确认允许清空全部记录”后才允许清空本地和飞书全部记录",
    key="confirm_clear_all_records",
)

if st.button("清空本地和飞书全部记录"):
    if confirm_clear_text != "我确认允许清空全部记录":
        st.warning("确认文本不一致，未执行清空操作。")
    else:
        local_deleted_count = clear_local_records()
        feishu_deleted_count, feishu_remaining_count, feishu_info_message, feishu_error_message = clear_feishu_records()

        st.success(f"本地删除了 {local_deleted_count} 条。")

        if feishu_info_message:
            st.info(feishu_info_message)

        st.success(f"飞书删除了 {feishu_deleted_count} 条。")
        st.info(f"飞书剩余 {feishu_remaining_count} 条。")

        if feishu_error_message:
            st.error(feishu_error_message)
