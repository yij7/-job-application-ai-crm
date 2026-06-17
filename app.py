from pathlib import Path
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

STATUS_OPTIONS = ["", "待投递", "已投递", "沟通中", "面试中", "已录用", "已拒绝", "已结束"]
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


def get_missing_basic_fields():
    field_labels = {
        "company_name": "公司名",
        "job_title": "岗位名",
        "job_direction": "岗位方向",
        "salary": "薪资",
        "location": "地点",
        "platform": "投递平台",
        "status": "投递状态",
        "notes": "备注",
        "chat_text": "聊天记录文本",
    }

    missing_fields = []
    for key, label in field_labels.items():
        if not clean_value(st.session_state[key]):
            missing_fields.append(label)

    return missing_fields

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
        return "请先在 .env 中配置 FEISHU_APP_ID、FEISHU_APP_SECRET、FEISHU_APP_TOKEN、FEISHU_TABLE_ID"
    return ""


def get_feishu_tenant_access_token(config):
    payload = {
        "app_id": config["app_id"],
        "app_secret": config["app_secret"],
    }

    response = requests.post(FEISHU_TOKEN_URL, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()

    if result.get("code") != 0:
        raise RuntimeError(result.get("msg", "获取 tenant_access_token 失败"))

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
        raise RuntimeError(f"读取飞书字段列表失败：{response.text}")

    result = response.json()
    if result.get("code") != 0:
        raise RuntimeError(f"读取飞书字段列表失败：{response.text}")

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
            return f"飞书同步失败：{response.text}"

        result = response.json()

        if result.get("code") != 0:
            if result.get("msg") == "FieldNameNotFound":
                return f"飞书同步失败：{response.text}"
            return f"飞书同步失败：{result.get('msg', '未知错误')}；完整响应：{response.text}"

        return ""
    except requests.exceptions.RequestException as error:
        return f"飞书同步失败：{error}"
    except (KeyError, RuntimeError) as error:
        return f"飞书同步失败：{error}"


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
    @media (max-width: 640px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
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

st.title("AI 求职投递管理与沟通分析系统")
st.caption("V5：一段粘贴生成结构化求职记录，并提供产品岗深度诊断。")

if st.session_state.success_message:
    st.success(st.session_state.success_message)
    st.session_state.success_message = ""

st.info("飞书同步需要在项目根目录 .env 中配置 FEISHU_APP_ID、FEISHU_APP_SECRET、FEISHU_APP_TOKEN、FEISHU_TABLE_ID。")

st.subheader("推荐使用方式")
st.markdown(
    "- 手机端：适合上传 Boss 截图并快速生成记录\n"
    "- 电脑端：适合查看、筛选、编辑、同步飞书和复盘"
)

st.subheader("截图上传解析")
st.caption("上传 Boss 岗位页、公司介绍页或 HR 聊天截图，系统会尝试识别截图内容并生成求职记录。")
st.info("建议在手机 Boss 直聘截图后，直接在手机浏览器打开本工具上传截图。")
uploaded_images = st.file_uploader(
    "上传 1-3 张截图",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

if st.button("AI识别截图并生成记录"):
    if not uploaded_images:
        st.warning("请先上传 1-3 张截图。")
    elif len(uploaded_images) > 3:
        st.warning("最多上传 3 张截图，请减少图片数量后重试。")
    else:
        with st.spinner("正在识别截图文字..."):
            extracted_text, ocr_errors = extract_text_from_uploaded_images(uploaded_images)

        if ocr_errors:
            st.warning("截图文字识别不完整，请补充文字或上传更清晰截图。")
            for error_message in ocr_errors:
                st.caption(error_message)

        if not extracted_text:
            st.warning("截图文字识别不完整，请补充文字或上传更清晰截图。")
        else:
            with st.spinner("正在根据截图内容生成求职记录..."):
                ai_result, error_message = smart_parse_with_deepseek(extracted_text)

            if error_message:
                st.error(error_message)
            else:
                fill_form_from_ai_parse(ai_result)
                missing_fields = get_missing_basic_fields()
                if missing_fields:
                    st.warning(
                        "截图文字识别不完整，请补充文字或上传更清晰截图。"
                        f" 未识别字段：{', '.join(missing_fields)}"
                    )
                st.success("截图解析完成，请确认表单后再点击保存记录。")

st.subheader("智能粘贴解析")
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
            st.success("AI解析完成，请确认表单后再点击保存记录。")

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

form_title = "编辑投递记录" if st.session_state.edit_index is not None else "新增投递记录"
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

    ai_submitted = st.form_submit_button("AI 分析岗位")
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
            st.success("记录已保存。")
        else:
            record["飞书同步状态"] = clean_value(records_df.loc[st.session_state.edit_index, "飞书同步状态"])
            record["飞书同步时间"] = clean_value(records_df.loc[st.session_state.edit_index, "飞书同步时间"])
            records_df.loc[st.session_state.edit_index, COLUMNS] = [record[column] for column in COLUMNS]
            save_records(records_df)
            st.session_state.edit_index = None
            st.session_state.success_message = "记录已更新。"
            st.rerun()

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
