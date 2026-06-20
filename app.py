from pathlib import Path
import base64
import io
import json
import os
import time
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
PRIORITY_OPTIONS = ["待评估", "高", "中", "低", "观察"]
PRIORITY_SORT_ORDER = {"高": 0, "中": 1, "低": 2, "观察": 3, "待评估": 4}
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
    records_df = ensure_ai_columns_are_strings(records_df)
    if csv_changed:
        records_df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

    return records_df


def save_records(records_df):
    records_df = records_df.fillna("")
    records_df = ensure_ai_columns_are_strings(records_df)
    for column in records_df.columns:
        records_df[column] = records_df[column].map(safe_str).astype(object)
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


def safe_str(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def normalize_priority(priority):
    priority = clean_value(priority)
    priority_map = {
        "": "待评估",
        "高优先级": "高",
        "中优先级": "中",
        "低优先级": "低",
        "暂不跟进": "观察",
        "放弃": "低",
    }
    priority = priority_map.get(priority, priority)
    if priority not in PRIORITY_OPTIONS:
        return "待评估"
    return priority


def safe_score(value):
    value = safe_str(value)
    try:
        return int(float(value))
    except ValueError:
        return None


def generate_priority_from_ai_result(ai_result):
    product_relevance = safe_score(ai_result.get("产品相关度", ""))
    resume_value = safe_score(ai_result.get("简历增值程度", ""))
    low_value_risk = safe_score(ai_result.get("低价值杂活风险", "") or ai_result.get("价值低杂活风险", ""))

    if product_relevance is None or resume_value is None or low_value_risk is None:
        return "观察"
    if product_relevance >= 4 and resume_value >= 4 and low_value_risk <= 2:
        return "高"
    if product_relevance >= 3 and resume_value >= 3 and low_value_risk <= 3:
        return "中"
    if low_value_risk >= 4 or product_relevance <= 2:
        return "低"
    return "观察"


def ensure_ai_columns_are_strings(records_df):
    for column in ALL_AI_COLUMNS:
        if column not in records_df.columns:
            records_df[column] = ""
        records_df[column] = records_df[column].map(safe_str).astype(object)
    if "岗位优先级" not in records_df.columns:
        records_df["岗位优先级"] = "待评估"
    records_df["岗位优先级"] = records_df["岗位优先级"].map(normalize_priority).astype(object)
    return records_df


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
        "岗位优先级": normalize_priority(st.session_state.priority),
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
        st.session_state.priority = normalize_priority(st.session_state.priority)

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

    st.session_state.priority = normalize_priority(st.session_state.priority)

    if st.session_state.priority not in PRIORITY_OPTIONS:
        st.session_state.priority = normalize_priority(st.session_state.priority)


def get_value_from_record(record, column):
    if record is None:
        return clean_value(get_form_record().get(column, ""))
    return clean_value(record.get(column, ""))


def build_deep_diagnosis_prompt(record=None):
    return f"""
你是 BossPilot 的求职决策助手，专注判断产品/AI产品/产品运营/项目助理/数据产品相关实习机会的真实价值。
你的目标不是普通聊天建议，而是帮助用户判断：这个岗位是否值得继续沟通、风险在哪里、下一步应该问 HR 什么。

固定用户背景，必须严格遵守：
- 本科在读，学校：中国计量大学。
- 当前方向：AI 产品 / 产品助理 / 项目运营 / 数据产品相关实习。
- 有项目经历：
  1. BossPilot AI 求职投递管理与沟通分析系统
  2. Olist 电商数据分析项目
  3. AI 视频营销项目交付管理与需求分析系统
- 能力关键词：需求分析、产品文档、原型/产品作品集、数据分析、AI 工具使用、项目记录与复盘。
- 暑期可实习，但不要默认“6个月全职”。
- 不允许编造学校、专业、经历、奖项、公司经历、实习时间。
- 如果输入材料没有提到的信息，必须写“信息不足”或“需要进一步确认”，不能编造。
- 绝对不要写“中国医科大学”。

请只返回合法 JSON，不要返回 Markdown，不要解释 JSON 之外的内容。

必须返回以下字段：
{{
  "产品相关度": "",
  "AI/数据/SaaS相关度": "",
  "简历增值程度": "",
  "价值低杂活风险": "",
  "成长路径": "",
  "岗位真实类型判断": "",
  "是否值得继续沟通": "",
  "解析置信度": "",
  "解析说明": "",
  "判断理由": "",
  "需要追问HR的3个关键问题": [],
  "面试表达建议": "",
  "建议回复话术": "",
  "岗位优先级": ""
}}

评分规则：
- 所有分数统一使用 1-5 分，不要输出 0。
- 产品相关度：5=明确参与需求分析、产品设计、原型、迭代；4=产品相关较强但可能偏辅助；3=有部分产品相关内容；2=偏运营/执行；1=基本无产品价值。
- AI/数据/SaaS相关度：5=明确 AI/数据产品/SaaS；4=明确数据产品/B端系统；3=有数据或平台属性；2=互联网产品但数据属性弱；1=无关。
- 简历增值程度：5=可形成作品集/项目经历/面试故事；4=有项目产出；3=有一定积累；2=主要执行；1=低价值。
- 价值低杂活风险：5=高风险，偏打杂/销售/客服/行政；4=风险较高；3=不确定；2=风险较低；1=基本无杂活风险。
- 成长路径：5=有导师、项目闭环、明确产出；4=有较好成长空间；3=普通；2=不清晰；1=无成长。

岗位真实类型判断只能从以下选项中选择：
- 产品经理实习生
- 产品运营实习生
- 数据产品实习生
- 项目运营实习生
- 销售/客服/行政杂活岗
- 信息不足

是否值得继续沟通只能从以下选项中选择：
- 是
- 否
- 需要进一步确认

判断理由必须包含三部分：
- 有利点：该岗位对用户产品/AI产品/数据产品方向的价值。
- 风险点：是否偏销售、客服、行政、资料整理、纯执行、无导师、无项目闭环。
- 需要向 HR 验证的点：哪些关键信息当前不足。
不要只复述岗位描述，必须给出决策判断。

需要追问HR的3个关键问题必须互不重复，严格覆盖以下三类：
1. 工作内容：实习生具体负责哪些产品模块？是需求分析、原型设计、数据分析，还是偏资料整理和运营支持？
2. 培养机制：是否有产品经理或业务导师带教？是否能参与完整需求从提出到上线的过程？
3. 产出与转化：实习期间是否有明确项目产出？是否有机会沉淀为作品集、复盘材料或后续转正机会？
禁止三个问题都围绕“负责什么模块”。

建议回复话术要求：
- 必须基于真实背景：中国计量大学本科在读。
- 可以提到 BossPilot、Olist 电商数据分析、AI 视频营销项目交付管理与需求分析系统。
- 可以提到需求分析、产品文档、数据分析、AI 工具应用、产品作品集。
- 不要写不存在的经历，不要过度夸大。
- 不要说“我可以满足6个月全职”，除非岗位文本明确要求且用户确认。
- 话术要自然，适合发给 Boss 直聘 HR。

岗位优先级规则：
- 高：产品相关度 >=4，简历增值程度 >=4，价值低杂活风险 <=2。
- 中：产品相关度 >=3，简历增值程度 >=3，价值低杂活风险 <=3。
- 观察：信息不足，但可能有价值。
- 低：价值低杂活风险 >=4 或 产品相关度 <=2。

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
- 岗位优先级只能从 待评估 / 高 / 中 / 低 / 观察 中选择。
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


DEFAULT_HR_QUESTIONS = [
    "实习生具体负责哪些产品模块？是需求分析、原型设计、数据分析，还是偏资料整理和运营支持？",
    "是否有产品经理或业务导师带教？是否能参与完整需求从提出到上线的过程？",
    "实习期间是否有明确项目产出？是否有机会沉淀为作品集、复盘材料或后续转正机会？",
]


def normalize_hr_questions(questions):
    if isinstance(questions, str):
        raw_questions = [line.strip("- 1234567890.、 ") for line in questions.splitlines()]
    elif isinstance(questions, list):
        raw_questions = [clean_value(question) for question in questions]
    else:
        raw_questions = []

    unique_questions = []
    for question in raw_questions:
        if question and question not in unique_questions:
            unique_questions.append(question)

    for question in DEFAULT_HR_QUESTIONS:
        if len(unique_questions) >= 3:
            break
        if question not in unique_questions:
            unique_questions.append(question)

    return unique_questions[:3]


def normalize_deepseek_analysis_result(ai_result):
    if not ai_result:
        return ai_result

    alias_map = {
        "AI/数据/SaaS相关度": "AI数据SaaS相关度",
        "价值低杂活风险": "低价值杂活风险",
        "成长路径": "成长路径清晰度",
        "岗位优先级": "综合优先级",
    }
    for source_key, target_key in alias_map.items():
        if source_key in ai_result and not clean_value(ai_result.get(target_key, "")):
            ai_result[target_key] = ai_result.get(source_key, "")

    ai_result["需要追问HR的3个关键问题"] = normalize_hr_questions(
        ai_result.get("需要追问HR的3个关键问题", [])
    )

    generated_priority = generate_priority_from_ai_result(ai_result)
    ai_result["岗位优先级"] = normalize_priority(ai_result.get("岗位优先级", "") or generated_priority)
    ai_result["综合优先级"] = ai_result["岗位优先级"]

    if clean_value(ai_result.get("是否值得继续沟通", "")) == "观察":
        ai_result["是否值得继续沟通"] = "需要进一步确认"

    return ai_result


def analyze_job_with_deepseek(record=None):
    ai_result, error_message = call_deepseek_json(build_deep_diagnosis_prompt(record))
    if error_message:
        return None, error_message
    return normalize_deepseek_analysis_result(ai_result), ""


def smart_parse_with_deepseek(raw_text):
    return call_deepseek_json(build_smart_parse_prompt(raw_text))


def build_qwen_screenshot_prompt(image_index):
    return """
你正在识别一张 Boss 直聘相关截图。请先判断这张截图属于哪一类，然后只提取这张截图中真实可见的信息。
不要追求完整岗位记录，不要因为缺少公司名、岗位名、薪资等字段就判定失败。
HR聊天图只需要提取聊天内容；公司图只需要提取公司信息；地图图只需要提取地点信息；重复图也要说明它可能与其他截图重复。
图片类型只能从：岗位详情图、HR聊天图、公司信息图、地图地点图、岗位列表图、重复截图、其他 中选择。
请只返回合法 JSON，不要返回 Markdown，不要输出 JSON 之外的解释。

必须返回以下 JSON 字段：
{
  "图片序号": IMAGE_INDEX,
  "图片类型判断": "岗位详情图/HR聊天图/公司信息图/地图地点图/岗位列表图/重复截图/其他",
  "是否识别成功": true,
  "是否提供新增信息": true,
  "成功原因": "",
  "失败原因": "",
  "公司名": "",
  "岗位名": "",
  "岗位方向": "",
  "薪资": "",
  "地点": "",
  "投递平台": "BOSS直聘",
  "投递状态": "",
  "岗位描述": "",
  "工作职责": "",
  "任职要求": "",
  "HR聊天记录": "",
  "公司信息": "",
  "地点信息": "",
  "可见文字摘要": "",
  "识别置信度": "高/中/低",
  "缺失字段": [],
  "识别说明": ""
}

不同图片类型的成功标准：
- 岗位详情图：识别到岗位名、岗位描述、工作职责、任职要求、薪资中的任意一项，即成功。
- HR聊天图：识别到任意一段聊天文字，即成功。
- 公司信息图：识别到公司名、公司规模、行业、融资、地址中的任意一项，即成功。
- 地图地点图：识别到城市、区域、地址、距离、地图文字中的任意一项，即成功。
- 岗位列表图：识别到岗位名、公司名、薪资、标签中的任意一项，即成功。
- 重复截图：如果识别到内容但可能与其他截图重复，也算成功，是否提供新增信息可以为 false。
- 其他：只要提取到可用于求职记录的可见文字摘要即可成功，否则失败。

规则：
- 无法识别的文本字段返回空字符串。
- 投递平台如果截图来自 Boss 直聘，填 BOSS直聘。
- 缺失字段必须是数组。
- HR聊天图没有公司名、岗位名、薪资不能判失败。
- 公司信息图没有岗位描述不能判失败。
- 地图地点图没有薪资不能判失败。
- 不要臆造公司名和岗位名。
- 不要判断岗位优先级，不要做岗位价值分析。
""".replace("IMAGE_INDEX", str(image_index))


def build_qwen_fallback_prompt(image_index):
    return """
请只提取图片中能看到的任何文字和页面类型，不要求完整字段。
如果这是聊天图，只提取聊天内容；如果是公司或地点图，只提取公司/地点相关文字。
只返回合法 JSON，不要输出 JSON 之外的解释。JSON 字段必须与以下结构一致：
{
  "图片序号": IMAGE_INDEX,
  "图片类型判断": "岗位详情图/HR聊天图/公司信息图/地图地点图/岗位列表图/重复截图/其他",
  "是否识别成功": true,
  "是否提供新增信息": true,
  "成功原因": "",
  "失败原因": "",
  "公司名": "",
  "岗位名": "",
  "岗位方向": "",
  "薪资": "",
  "地点": "",
  "投递平台": "BOSS直聘",
  "投递状态": "",
  "岗位描述": "",
  "工作职责": "",
  "任职要求": "",
  "HR聊天记录": "",
  "公司信息": "",
  "地点信息": "",
  "可见文字摘要": "",
  "识别置信度": "高/中/低",
  "缺失字段": [],
  "识别说明": ""
}
""".replace("IMAGE_INDEX", str(image_index))


def get_uploaded_image_data_url(uploaded_file, max_side=1280, quality=85):
    from PIL import Image

    uploaded_file.seek(0)
    original_size = len(uploaded_file.getvalue())
    uploaded_file.seek(0)
    image = Image.open(uploaded_file)
    image = image.convert("RGB")

    width, height = image.size
    scale = min(max_side / max(width, height), 1)
    if scale < 1:
        image = image.resize((int(width * scale), int(height * scale)))

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    file_bytes = buffer.getvalue()
    file_type = "image/jpeg"
    image_base64 = base64.b64encode(file_bytes).decode("utf-8")
    image_info = {
        "原始图片大小": original_size,
        "压缩后大小": len(file_bytes),
        "压缩后宽度": image.size[0],
        "压缩后高度": image.size[1],
        "最长边": max_side,
        "JPEG质量": quality,
    }
    return f"data:{file_type};base64,{image_base64}", image_info


def build_qwen_debug_info(model, api_key, recognition_mode="快速识别"):
    return {
        "QWEN_VL_MODEL 当前值": model,
        "是否读取到 QWEN_API_KEY": bool(api_key),
        "请求接口 base_url": QWEN_VL_API_URL,
        "识别模式": recognition_mode,
        "每张截图识别状态": [],
        "每张截图识别结果": [],
        "每张截图调试信息": [],
        "合并后的岗位信息": {},
        "HTTP 状态码 status_code": "",
        "返回错误信息 response.text": "",
        "Python 异常类型": "",
        "Python 异常信息": "",
        "排查建议": "",
    }


def call_qwen_vision_for_single_screenshot(
    uploaded_file,
    image_index,
    headers,
    model,
    previous_results,
    max_side=1280,
    quality=80,
    timeout=150,
):
    debug_item = {
        "图片序号": image_index,
        "文件名": uploaded_file.name,
        "最终状态": "技术识别失败，已跳过，不影响最终记录生成",
        "图片大小": "",
        "压缩后大小": "",
        "模型调用耗时": "",
        "是否重试": False,
        "重试次数": 0,
        "Qwen返回的原始JSON": "",
        "尝试记录": [],
        "HTTP 状态码 status_code": "",
        "返回错误信息 response.text": "",
        "Python 异常类型": "",
        "Python 异常信息": "",
        "排查建议": "",
    }

    attempts = [
        {
            "名称": "视觉识别",
            "max_side": max_side,
            "quality": quality,
            "timeout": timeout,
            "prompt": build_qwen_screenshot_prompt(image_index),
        }
    ]

    for attempt_index, attempt in enumerate(attempts, start=1):
        attempt_debug = {
            "尝试": attempt["名称"],
            "max_side": attempt["max_side"],
            "quality": attempt["quality"],
            "timeout": attempt["timeout"],
            "HTTP 状态码 status_code": "",
            "返回错误信息 response.text": "",
            "模型调用耗时": "",
            "失败原因": "",
        }
        debug_item["是否重试"] = attempt_index > 1
        debug_item["重试次数"] = attempt_index - 1

        try:
            data_url, image_info = get_uploaded_image_data_url(
                uploaded_file,
                max_side=attempt["max_side"],
                quality=attempt["quality"],
            )
            debug_item["图片大小"] = image_info["原始图片大小"]
            debug_item["压缩后大小"] = image_info["压缩后大小"]
            attempt_debug.update(image_info)

            content = [
                {"type": "text", "text": attempt["prompt"]},
                {
                    "type": "image_url",
                    "image_url": {"url": data_url},
                },
            ]
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": content}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            }
            start_time = time.time()
            response = requests.post(QWEN_VL_API_URL, headers=headers, json=payload, timeout=attempt["timeout"])
            elapsed_time = round(time.time() - start_time, 2)
            attempt_debug["模型调用耗时"] = f"{elapsed_time}s"
            debug_item["模型调用耗时"] = f"{elapsed_time}s"
            debug_item["HTTP 状态码 status_code"] = response.status_code
            debug_item["返回错误信息 response.text"] = response.text[:1000]
            attempt_debug["HTTP 状态码 status_code"] = response.status_code
            attempt_debug["返回错误信息 response.text"] = response.text[:1000]
            print(f"Qwen视觉模型 第{image_index}张 第{attempt_index}次 response.status_code: {response.status_code}")
            print(f"Qwen视觉模型 第{image_index}张 第{attempt_index}次 response.text: {response.text}")

            if response.status_code != 200:
                attempt_debug["失败原因"] = f"API报错：{get_qwen_error_suggestion(response.status_code, response.text)}"
                debug_item["排查建议"] = attempt_debug["失败原因"]
                debug_item["尝试记录"].append(attempt_debug)
                continue

            result = response.json()
            content_text = result["choices"][0]["message"]["content"]
            image_result = parse_ai_response(content_text)
            image_result["图片序号"] = image_index
            debug_item["Qwen返回的原始JSON"] = image_result

            success, reason = validate_qwen_image_result(image_result)
            image_result["是否识别成功"] = success
            if success:
                apply_duplicate_status(image_result, previous_results)
                image_result["成功原因"] = clean_value(image_result.get("成功原因", "")) or reason
                debug_item["最终状态"] = build_qwen_status_text(image_result)
                debug_item["尝试记录"].append(attempt_debug)
                return image_result, debug_item

            image_result["失败原因"] = clean_value(image_result.get("失败原因", "")) or reason
            attempt_debug["失败原因"] = f"未提取到该类型有效信息：{image_result['失败原因']}"
            debug_item["排查建议"] = image_result["失败原因"]
            debug_item["尝试记录"].append(attempt_debug)
        except requests.exceptions.Timeout as error:
            attempt_debug["失败原因"] = "该截图识别超时，已跳过。"
            debug_item["Python 异常类型"] = type(error).__name__
            debug_item["Python 异常信息"] = str(error)
            debug_item["排查建议"] = "该截图识别超时，已跳过。"
            debug_item["尝试记录"].append(attempt_debug)
        except requests.exceptions.RequestException as error:
            attempt_debug["失败原因"] = "API报错"
            debug_item["Python 异常类型"] = type(error).__name__
            debug_item["Python 异常信息"] = str(error)
            debug_item["排查建议"] = "API报错，请检查服务端网络、百炼接口地址和 API Key 权限。"
            debug_item["尝试记录"].append(attempt_debug)
        except (KeyError, IndexError, json.JSONDecodeError) as error:
            attempt_debug["失败原因"] = "JSON解析失败"
            debug_item["Python 异常类型"] = type(error).__name__
            debug_item["Python 异常信息"] = str(error)
            debug_item["排查建议"] = "JSON解析失败，模型返回格式不是预期 JSON。"
            debug_item["尝试记录"].append(attempt_debug)
        except Exception as error:
            attempt_debug["失败原因"] = "图片压缩或请求组装失败"
            debug_item["Python 异常类型"] = type(error).__name__
            debug_item["Python 异常信息"] = str(error)
            debug_item["排查建议"] = "图片压缩或请求组装失败，请检查图片格式。"
            debug_item["尝试记录"].append(attempt_debug)

    last_failure = ""
    if debug_item["尝试记录"]:
        last_failure = clean_value(debug_item["尝试记录"][-1].get("失败原因", ""))
    if last_failure:
        debug_item["最终状态"] = f"技术识别失败：{last_failure}，已跳过，不影响最终记录生成"
    return None, debug_item


def validate_qwen_image_result(image_result):
    image_type = clean_value(image_result.get("图片类型判断", "其他"))
    image_type = normalize_qwen_image_type(image_type)
    image_result["图片类型判断"] = image_type

    if image_type == "岗位详情图":
        detail_fields = ["岗位名", "岗位描述", "工作职责", "任职要求", "薪资"]
        if any(clean_value(image_result.get(field, "")) for field in detail_fields):
            return True, "识别到岗位详情信息"
        return False, "未提取到岗位名、岗位描述、职责、任职要求或薪资"

    if image_type == "HR聊天图":
        if clean_value(image_result.get("HR聊天记录", "")) or clean_value(image_result.get("可见文字摘要", "")):
            return True, "识别到聊天内容"
        return False, "未提取到聊天内容"

    if image_type == "公司信息图":
        company_fields = ["公司名", "公司信息", "地点", "地点信息", "可见文字摘要"]
        if any(clean_value(image_result.get(field, "")) for field in company_fields):
            return True, "识别到公司信息"
        return False, "未提取到公司名、公司介绍、规模或行业信息"

    if image_type == "地图地点图":
        location_fields = ["地点", "地点信息", "可见文字摘要"]
        if any(clean_value(image_result.get(field, "")) for field in location_fields):
            return True, "识别到地点信息"
        return False, "未提取到地点、距离、城市或办公地址"

    if image_type == "岗位列表图":
        list_fields = ["岗位名", "公司名", "薪资", "岗位方向", "可见文字摘要"]
        if any(clean_value(image_result.get(field, "")) for field in list_fields):
            return True, "识别到岗位列表信息"
        return False, "未提取到岗位名、公司名或薪资"

    if image_type == "重复截图":
        if get_qwen_result_signature(image_result):
            return True, "识别到重复截图内容"
        return False, "未提取到重复截图中的可见内容"

    useful_fields = [
        "公司名",
        "岗位名",
        "岗位方向",
        "薪资",
        "地点",
        "岗位描述",
        "工作职责",
        "任职要求",
        "HR聊天记录",
        "公司信息",
        "地点信息",
        "可见文字摘要",
    ]
    if any(clean_value(image_result.get(field, "")) for field in useful_fields):
        return True, "识别到可用补充信息"
    return False, "未提取到该类型有效信息"


def normalize_qwen_image_type(image_type):
    type_map = {
        "岗位详情": "岗位详情图",
        "HR聊天": "HR聊天图",
        "公司信息": "公司信息图",
        "地图/地点图": "地图地点图",
        "地图图": "地图地点图",
        "地点图": "地图地点图",
        "岗位列表": "岗位列表图",
    }
    return type_map.get(image_type, image_type or "其他")


def get_qwen_result_signature(image_result):
    signature_fields = [
        "公司名",
        "岗位名",
        "岗位方向",
        "薪资",
        "地点",
        "岗位描述",
        "工作职责",
        "任职要求",
        "HR聊天记录",
        "公司信息",
        "地点信息",
        "可见文字摘要",
    ]
    text_parts = [clean_value(image_result.get(field, "")) for field in signature_fields]
    return " ".join(part for part in text_parts if part)


def find_duplicate_source(image_result, previous_results):
    current_signature = get_qwen_result_signature(image_result)
    if len(current_signature) < 20:
        return None

    for previous_result in previous_results:
        previous_signature = get_qwen_result_signature(previous_result)
        if len(previous_signature) < 20:
            continue
        current_compact = "".join(current_signature.split())
        previous_compact = "".join(previous_signature.split())
        if current_compact in previous_compact or previous_compact in current_compact:
            return previous_result.get("图片序号", "")
    return None


def apply_duplicate_status(image_result, previous_results):
    duplicate_source = find_duplicate_source(image_result, previous_results)
    if duplicate_source:
        image_result["图片类型判断"] = "重复截图"
        image_result["是否提供新增信息"] = False
        image_result["识别说明"] = f"该截图内容与第{duplicate_source}张重复，未提供新增字段。"
        image_result["成功原因"] = f"识别成功，内容与第{duplicate_source}张重复，未新增字段。"
        return

    if normalize_qwen_image_type(clean_value(image_result.get("图片类型判断", ""))) == "重复截图":
        image_result["图片类型判断"] = "其他"
    image_result["是否提供新增信息"] = True


def build_qwen_status_text(image_result):
    image_type = normalize_qwen_image_type(clean_value(image_result.get("图片类型判断", "其他")))
    if clean_value(image_result.get("是否提供新增信息", True)) in ["False", "false", "0", "否"]:
        return f"{image_type}，{clean_value(image_result.get('成功原因', '识别成功，未新增字段'))}"

    status_map = {
        "岗位详情图": "岗位详情图，已提取岗位信息",
        "HR聊天图": "HR聊天图，已提取聊天内容",
        "公司信息图": "公司信息图，已提取公司和地点信息",
        "地图地点图": "地图地点图，已提取地点信息",
        "岗位列表图": "岗位列表图，已提取岗位列表信息",
        "重复截图": "重复截图，识别成功，未新增字段",
    }
    return status_map.get(image_type, f"{image_type}，已提取可见信息")


def join_unique_text(values):
    cleaned_values = []
    for value in values:
        value = clean_value(value)
        if value and value not in cleaned_values:
            cleaned_values.append(value)
    return "\n\n".join(cleaned_values)


def qwen_has_new_info(image_result):
    value = image_result.get("是否提供新增信息", True)
    if isinstance(value, bool):
        return value
    return clean_value(value).lower() not in ["false", "0", "否", "no"]


def get_qwen_confidence_score(image_result):
    return {"高": 3, "中": 2, "低": 1}.get(clean_value(image_result.get("识别置信度", "低")), 1)


def get_qwen_field_score(image_result, field):
    image_type = normalize_qwen_image_type(clean_value(image_result.get("图片类型判断", "")))
    type_scores = {
        "岗位详情图": {
            "岗位名": 100,
            "薪资": 100,
            "岗位方向": 90,
            "岗位描述": 100,
            "地点": 70,
            "公司名": 70,
        },
        "公司信息图": {
            "公司名": 100,
            "地点": 80,
            "岗位描述": 70,
        },
        "地图地点图": {
            "地点": 100,
            "岗位描述": 60,
        },
        "HR聊天图": {
            "投递状态": 90,
        },
        "岗位列表图": {
            "岗位名": 70,
            "公司名": 60,
            "薪资": 70,
            "地点": 60,
        },
        "其他": {},
        "重复截图": {},
    }
    return type_scores.get(image_type, {}).get(field, 30) + get_qwen_confidence_score(image_result)


def merge_qwen_screenshot_results(image_results):
    final_result = {
        "公司名": "",
        "岗位名": "",
        "岗位方向": "",
        "薪资": "",
        "地点": "",
        "投递平台": "BOSS直聘",
        "投递状态": "",
        "岗位描述": "",
        "HR聊天记录": "",
        "识别置信度": "低",
        "缺失字段": [],
        "识别说明": "",
    }
    normal_fields = ["公司名", "岗位名", "岗位方向", "薪资", "地点", "投递平台", "投递状态"]
    field_scores = {}
    mergeable_results = [result for result in image_results if qwen_has_new_info(result)]

    for image_result in mergeable_results:
        for field in normal_fields:
            value = clean_value(image_result.get(field, ""))
            if not value:
                continue

            field_score = get_qwen_field_score(image_result, field)
            if not final_result[field] or field_score > field_scores.get(field, 0):
                final_result[field] = value
                field_scores[field] = field_score

    job_description_parts = []
    for result in mergeable_results:
        image_type = normalize_qwen_image_type(clean_value(result.get("图片类型判断", "")))
        if image_type == "岗位详情图":
            job_description_parts.append(result.get("岗位描述", ""))
            job_description_parts.append(result.get("工作职责", ""))
            job_description_parts.append(result.get("任职要求", ""))
        if image_type == "公司信息图":
            job_description_parts.append(result.get("公司信息", ""))
        if image_type == "地图地点图":
            job_description_parts.append(result.get("地点信息", ""))
        if image_type not in ["岗位详情图", "公司信息图", "地图地点图"]:
            job_description_parts.append(result.get("岗位描述", ""))

    final_result["岗位描述"] = join_unique_text(job_description_parts)
    final_result["HR聊天记录"] = join_unique_text(result.get("HR聊天记录", "") for result in mergeable_results)

    if not clean_value(final_result["地点"]):
        final_result["地点"] = next(
            (
                clean_value(result.get("地点信息", ""))
                for result in mergeable_results
                if clean_value(result.get("地点信息", ""))
            ),
            "",
        )

    missing_fields = []
    for image_result in image_results:
        for field in image_result.get("缺失字段", []):
            field = clean_value(field)
            if field and field not in missing_fields:
                missing_fields.append(field)
    final_result["缺失字段"] = missing_fields

    confidence_scores = {"高": 3, "中": 2, "低": 1}
    confidences = [
        clean_value(result.get("识别置信度", "低"))
        for result in image_results
        if clean_value(result.get("识别置信度", "低")) in confidence_scores
    ]
    if confidences:
        lowest_confidence = min(confidences, key=lambda item: confidence_scores[item])
        final_result["识别置信度"] = lowest_confidence

    notes = []
    for result in image_results:
        note = clean_value(result.get("识别说明", ""))
        if note:
            notes.append(f"第{result.get('图片序号', '')}张：{note}")
    final_result["识别说明"] = join_unique_text(notes) or f"已逐张识别并合并 {len(image_results)} 张截图。"
    return final_result


def call_qwen_vision_for_screenshots(uploaded_files, recognition_mode="快速识别", progress_placeholder=None):
    api_key = get_config_value("QWEN_API_KEY")
    model = get_config_value("QWEN_VL_MODEL") or "qwen3.6-plus"
    debug_info = build_qwen_debug_info(model, api_key, recognition_mode)

    if not api_key:
        debug_info["排查建议"] = "请在 .env / Streamlit Secrets 中配置 QWEN_API_KEY。"
        return None, "未配置 Qwen 视觉模型，截图识别不可用。请使用粘贴文本解析，或在 .env / Streamlit Secrets 中配置 QWEN_API_KEY。", debug_info

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    if recognition_mode == "快速识别":
        files_to_process = uploaded_files[:3]
        max_side = 1024
        quality = 75
        timeout = 90
    else:
        files_to_process = uploaded_files[:10]
        max_side = 1280
        quality = 80
        timeout = 150

    successful_results = []
    total_images = len(files_to_process)
    for image_index, uploaded_file in enumerate(files_to_process, start=1):
        if progress_placeholder:
            progress_placeholder.info(f"正在识别第 {image_index} / {total_images} 张截图")

        image_result, image_debug = call_qwen_vision_for_single_screenshot(
            uploaded_file,
            image_index,
            headers,
            model,
            successful_results,
            max_side=max_side,
            quality=quality,
            timeout=timeout,
        )
        debug_info["每张截图识别状态"].append(f"第{image_index}张：{image_debug['最终状态']}")
        debug_info["每张截图识别结果"].append(image_result or image_debug)
        debug_info["每张截图调试信息"].append(image_debug)
        if image_result:
            successful_results.append(image_result)

    if recognition_mode == "快速识别" and len(uploaded_files) > len(files_to_process):
        for skipped_index in range(len(files_to_process) + 1, len(uploaded_files) + 1):
            debug_info["每张截图识别状态"].append(
                f"第{skipped_index}张：快速识别模式未调用视觉模型"
            )

    if not successful_results:
        debug_info["排查建议"] = "所有图片视觉模型识别均失败，已准备进入备用 OCR。"
        return None, "Qwen视觉模型调用失败。", debug_info

    merged_result = merge_qwen_screenshot_results(successful_results)
    debug_info["合并后的岗位信息"] = merged_result
    if len(successful_results) < len(files_to_process):
        return merged_result, "部分截图未提取到有效信息，但已根据成功识别的截图生成记录。", debug_info

    return merged_result, "", debug_info


def get_qwen_error_suggestion(status_code, response_text):
    response_text_upper = response_text.upper()

    if "MODEL" in response_text_upper and ("NOT" in response_text_upper or "INVALID" in response_text_upper):
        return "可能是模型不存在或模型名不支持，请检查 QWEN_VL_MODEL。"

    if status_code in [401, 403]:
        return "可能是 API Key、权限或额度问题，请检查 QWEN_API_KEY、百炼权限和账户额度。"

    if status_code == 400 or "INVALID" in response_text_upper or "IMAGE" in response_text_upper:
        return "可能是请求格式错误，请检查图片 base64 / image_url 格式或模型是否支持当前图片输入格式。"

    return "请根据 response.text 判断具体错误；不要在页面或日志中暴露完整 API Key。"


def save_ai_result_to_session(ai_result):
    st.session_state.ai_match_level = convert_priority_to_match_level(ai_result.get("综合优先级", ""))
    st.session_state.ai_job_type = clean_value(ai_result.get("岗位真实类型判断", ""))
    st.session_state.ai_risks = clean_value(ai_result.get("判断理由", ""))
    st.session_state.ai_next_step = clean_value(ai_result.get("是否值得继续沟通", ""))
    st.session_state.ai_reply = clean_value(ai_result.get("建议回复话术", ""))

    for column, key in DIAGNOSIS_FIELD_KEYS.items():
        value = ai_result.get(column, "")
        st.session_state[key] = clean_ai_value(value)


def apply_ai_priority_to_session(ai_result):
    generated_priority = generate_priority_from_ai_result(ai_result)
    current_priority = normalize_priority(st.session_state.priority)
    if current_priority in ["待评估", "观察"]:
        st.session_state.priority = generated_priority


def get_ai_record_from_result(ai_result):
    ai_record = {
        "AI岗位匹配度": safe_str(convert_priority_to_match_level(ai_result.get("综合优先级", ""))),
        "AI岗位类型": safe_str(ai_result.get("岗位真实类型判断", "")),
        "AI风险点": safe_str(ai_result.get("判断理由", "")),
        "AI下一步建议": safe_str(ai_result.get("是否值得继续沟通", "")),
        "AI建议回复话术": safe_str(ai_result.get("建议回复话术", "")),
    }

    for column in DIAGNOSIS_FIELD_KEYS:
        ai_record[column] = safe_str(clean_ai_value(ai_result.get(column, "")))

    return ai_record


def write_ai_record_to_df(records_df, row_index, ai_record):
    records_df = ensure_ai_columns_are_strings(records_df)
    for column in ALL_AI_COLUMNS:
        records_df.at[row_index, column] = safe_str(ai_record.get(column, ""))
    return records_df


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

    st.session_state.priority = normalize_priority(
        ai_result.get("岗位优先级", "")
        or generate_priority_from_ai_result(ai_result)
        or convert_overall_priority_to_record_priority(ai_result.get("综合优先级", ""))
    )

    if st.session_state.status not in STATUS_OPTIONS:
        st.session_state.status = ""

    if st.session_state.priority not in PRIORITY_OPTIONS:
        st.session_state.priority = "待评估"

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
    st.session_state.priority = "待评估"

    if not clean_value(st.session_state.status) or st.session_state.status not in STATUS_OPTIONS:
        st.session_state.status = "待补充" if "待补充" in STATUS_OPTIONS else ""


def convert_overall_priority_to_record_priority(priority):
    priority = clean_value(priority)
    priority_map = {
        "高": "高",
        "中": "中",
        "低": "低",
        "放弃": "低",
    }
    return priority_map.get(priority, "待评估")


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
    records_df = ensure_ai_columns_are_strings(records_df)
    for column in ALL_AI_COLUMNS:
        records_df.at[row_index, column] = ""
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
    st.session_state.priority = normalize_priority(st.session_state.priority)

if "pending_priority_update" not in st.session_state:
    st.session_state.pending_priority_update = ""

if st.session_state.pending_priority_update:
    st.session_state.priority = normalize_priority(st.session_state.pending_priority_update)
    st.session_state.pending_priority_update = ""

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
    st.caption("建议上传 2–5 张 Boss 岗位截图，最多 10 张。")
    st.info("手机端建议先在相册中整理好截图，再一次性选择上传。")
    uploaded_images = st.file_uploader(
        "上传截图",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    recognition_mode = st.radio(
        "识别模式",
        ["快速识别", "完整识别"],
        index=0,
        horizontal=True,
    )
    if recognition_mode == "快速识别":
        st.caption("快速识别模式下，建议把岗位详情图、公司信息图、关键HR聊天图放在前 3 张。")
    else:
        st.caption("完整识别会处理更多截图，耗时较长，请耐心等待。")

    if uploaded_images:
        st.success(f"上传成功 {len(uploaded_images)} 张截图")
        st.caption(f"当前识别模式：{recognition_mode}")
        st.caption("已压缩图片以提升识别速度。")
        if recognition_mode == "快速识别" and len(uploaded_images) > 3:
            st.info("快速识别模式下，系统将优先分析前 3 张截图。其余截图不会调用视觉模型。")
        st.caption("图片预览")
        preview_columns = st.columns(min(len(uploaded_images), 4))
        for index, uploaded_image in enumerate(uploaded_images):
            with preview_columns[index % len(preview_columns)]:
                st.image(uploaded_image, caption=uploaded_image.name, use_container_width=True)

    if st.button("AI读取截图并生成记录"):
        if not uploaded_images:
            st.warning("请先上传截图。")
        elif len(uploaded_images) > 10:
            st.warning("最多上传 10 张截图，请减少后重新上传。")
        else:
            progress_placeholder = st.empty()
            with st.spinner("正在逐张调用视觉模型读取截图..."):
                qwen_result, qwen_error, qwen_debug_info = call_qwen_vision_for_screenshots(
                    uploaded_images,
                    recognition_mode=recognition_mode,
                    progress_placeholder=progress_placeholder,
                )
            progress_placeholder.empty()

            if qwen_result:
                fill_form_from_qwen_result(qwen_result)
                for status_text in qwen_debug_info.get("每张截图识别状态", []):
                    st.write(status_text)
                with st.expander("每张截图提取到的信息", expanded=False):
                    st.json(qwen_debug_info.get("每张截图识别结果", []))
                with st.expander("每张截图调试信息", expanded=False):
                    st.json(qwen_debug_info.get("每张截图调试信息", []))
                with st.expander("合并后的岗位信息", expanded=False):
                    st.json(qwen_result)
                if qwen_error:
                    st.warning(qwen_error)
                if len(uploaded_images) > 1:
                    st.info("已逐张识别多张截图，并合并为一份岗位记录。")
                if recognition_mode == "快速识别":
                    st.success("快速识别完成，如信息不完整，可切换完整识别或使用粘贴文本补充。")
                else:
                    st.success("已完成多张截图识别并合并，请检查下方表单。")
                st.info("如需岗位价值判断，请继续点击下方“AI岗位深度诊断”。")
            elif qwen_error.startswith("未配置 Qwen 视觉模型"):
                st.warning(qwen_error)
            else:
                with st.expander("Qwen视觉模型错误详情", expanded=False):
                    st.json(qwen_debug_info)
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
    st.subheader("粘贴岗位信息解析")
    st.caption("截图识别失败或信息不完整时，可粘贴 Boss 岗位详情、公司介绍、HR聊天记录等文本。")
    st.text_area(
        "粘贴岗位信息",
        height=180,
        key="smart_raw_text",
        placeholder="可以粘贴 BOSS 岗位详情、公司介绍、HR 聊天记录，或岗位描述和聊天混合文本。",
    )

    if st.button("一键解析并填充"):
        if not clean_value(st.session_state.smart_raw_text):
            st.warning("请先粘贴岗位详情或聊天记录。")
        else:
            with st.spinner("正在解析岗位信息..."):
                ai_result, error_message = smart_parse_with_deepseek(st.session_state.smart_raw_text)

            if error_message:
                st.session_state.raw_job_text = st.session_state.smart_raw_text
                fill_form_from_raw_text()
                st.warning("AI解析未完成，已尝试按规则填充可识别字段。")
            else:
                fill_form_from_ai_parse(ai_result)
                st.success("AI解析完成，请向下确认表单，然后点击保存记录。")

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
            st.session_state.pending_priority_update = generate_priority_from_ai_result(ai_result)
            st.session_state.success_message = "AI 分析完成。"
            st.rerun()

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
            for column in COLUMNS:
                records_df.at[st.session_state.edit_index, column] = safe_str(record.get(column, ""))
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

    with st.container(border=True):
        st.markdown(f"**岗位真实类型：** {clean_value(st.session_state.real_job_type) or '待判断'}")
        st.markdown(f"**是否值得继续沟通：** {clean_value(st.session_state.worth_following) or '待判断'}")
        if clean_value(st.session_state.overall_priority):
            st.markdown(f"**综合优先级：** {st.session_state.overall_priority}")
        if clean_value(st.session_state.parse_confidence):
            st.markdown(f"**解析置信度：** {st.session_state.parse_confidence}")
        if clean_value(st.session_state.parse_notes):
            st.markdown(f"**解析说明：** {st.session_state.parse_notes}")
        st.markdown("**判断理由**")
        if clean_value(st.session_state.reasoning):
            st.write(st.session_state.reasoning)
        else:
            st.caption("暂无")
        if clean_value(st.session_state.interview_advice):
            st.markdown("**面试表达建议**")
            st.write(st.session_state.interview_advice)

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

            current_priority = normalize_priority(row["岗位优先级"])
            core_record = {
                "公司名": clean_value(row["公司名"]),
                "岗位名": clean_value(row["岗位名"]),
                "岗位方向": clean_value(row["岗位方向"]),
                "薪资": clean_value(row["薪资"]),
                "地点": clean_value(row["地点"]),
                "投递平台": clean_value(row["投递平台"]),
                "投递状态": clean_value(row["投递状态"]),
                "岗位优先级": current_priority,
                "AI岗位摘要": " / ".join(
                    part
                    for part in [
                        clean_value(row["AI岗位类型"]),
                        f"匹配度：{clean_value(row['AI岗位匹配度'])}" if clean_value(row["AI岗位匹配度"]) else "",
                    ]
                    if part
                ),
                "飞书同步状态": clean_value(row["飞书同步状态"]),
            }
            core_record = {key: value for key, value in core_record.items() if clean_value(value)}
            st.dataframe(pd.DataFrame([core_record]), use_container_width=True, hide_index=True)

            ai_detail = {
                "产品相关度": clean_value(row["产品相关度"]),
                "AI/数据/SaaS相关度": clean_value(row["AI数据SaaS相关度"]),
                "简历增值程度": clean_value(row["简历增值程度"]),
                "低价值杂活风险": clean_value(row["低价值杂活风险"]),
                "成长路径清晰度": clean_value(row["成长路径清晰度"]),
                "综合优先级": clean_value(row["综合优先级"]),
                "岗位真实类型判断": clean_value(row["岗位真实类型判断"]),
                "是否值得继续沟通": clean_value(row["是否值得继续沟通"]),
                "解析置信度": clean_value(row["解析置信度"]),
                "解析说明": clean_value(row["解析说明"]),
                "需要追问HR的3个关键问题": clean_value(row["需要追问HR的3个关键问题"]),
                "面试表达建议": clean_value(row["面试表达建议"]),
                "建议回复话术": clean_value(row["建议回复话术"]),
                "判断理由": clean_value(row["判断理由"]),
            }
            ai_detail = {key: value for key, value in ai_detail.items() if clean_value(value)}
            if ai_detail:
                with st.expander("AI分析详情", expanded=False):
                    for key, value in ai_detail.items():
                        st.markdown(f"**{key}：**")
                        st.write(value)

            priority_col, edit_col, delete_col, analyze_col, clear_ai_col, feishu_col = st.columns(
                [1.5, 1, 1, 1, 1, 1]
            )
            with priority_col:
                st.markdown(f"岗位优先级：**{current_priority}**")

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
                        records_df = write_ai_record_to_df(records_df, row_index, ai_record)
                        current_priority = normalize_priority(records_df.at[row_index, "岗位优先级"])
                        if current_priority in ["待评估", "观察"]:
                            records_df.at[row_index, "岗位优先级"] = generate_priority_from_ai_result(ai_result)
                        save_records(records_df)
                        if st.session_state.edit_index == row_index:
                            save_ai_result_to_session(ai_result)
                            st.session_state.pending_priority_update = generate_priority_from_ai_result(ai_result)
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
