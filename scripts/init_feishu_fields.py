import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
FEISHU_FIELDS_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
TEXT_FIELD_TYPE = 1
REQUIRED_FIELDS = [
    "公司名",
    "岗位名",
    "岗位方向",
    "薪资",
    "地点",
    "投递平台",
    "投递状态",
    "岗位链接",
    "岗位优先级",
    "岗位优先级分值",
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
    "飞书同步状态",
    "飞书同步时间",
]


def load_feishu_config():
    load_dotenv(PROJECT_ROOT / ".env")

    config = {
        "app_id": os.getenv("FEISHU_APP_ID", "").strip(),
        "app_secret": os.getenv("FEISHU_APP_SECRET", "").strip(),
        "app_token": os.getenv("FEISHU_APP_TOKEN", "").strip(),
        "table_id": os.getenv("FEISHU_TABLE_ID", "").strip(),
    }

    missing_keys = [key for key, value in config.items() if not value]
    if missing_keys:
        print("请先在项目根目录 .env 中配置以下字段：")
        for key in missing_keys:
            print(f"- {key}")
        sys.exit(1)

    return config


def mask_app_token(app_token):
    if len(app_token) <= 10:
        return f"{app_token[:2]}***{app_token[-2:]}"
    return f"{app_token[:6]}***{app_token[-4:]}"


def validate_token_format(config):
    bad_patterns = ["https://", "?table=", "&view="]
    app_token = config["app_token"]
    table_id = config["table_id"]

    if any(pattern in app_token for pattern in bad_patterns) or any(pattern in table_id for pattern in bad_patterns):
        print(".env 中 FEISHU_APP_TOKEN 或 FEISHU_TABLE_ID 格式错误，只能填写 token/id 本身。")
        print(f"FEISHU_APP_TOKEN 脱敏值: {mask_app_token(app_token)}")
        print(f"FEISHU_TABLE_ID: {table_id}")
        sys.exit(1)


def get_tenant_access_token(config):
    payload = {
        "app_id": config["app_id"],
        "app_secret": config["app_secret"],
    }

    response = requests.post(FEISHU_TOKEN_URL, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()

    if result.get("code") != 0:
        print("获取 tenant_access_token 失败")
        print(f"错误码: {result.get('code')}")
        print(f"错误信息: {result.get('msg')}")
        sys.exit(1)

    return result["tenant_access_token"]


def get_fields_url(config):
    return FEISHU_FIELDS_URL.format(
        app_token=config["app_token"],
        table_id=config["table_id"],
    )


def list_existing_fields(config, tenant_access_token):
    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
    }
    url = get_fields_url(config)

    print("准备调用飞书字段列表接口：")
    print(f"app_token: {mask_app_token(config['app_token'])}")
    print(f"table_id: {config['table_id']}")
    print(f"request_url: {url}")

    response = requests.get(url, headers=headers, timeout=30)

    print(f"response.status_code: {response.status_code}")
    print(f"response.text: {response.text}")

    if response.status_code != 200:
        print("获取字段列表 HTTP 请求失败，已打印完整 response.text。")
        return set()

    result = response.json()

    if result.get("code") != 0:
        print("获取字段列表失败")
        print(f"请求 URL: {url}")
        print(f"错误码: {result.get('code')}")
        print(f"错误信息: {result.get('msg')}")
        return set()

    fields = result.get("data", {}).get("items", [])
    return {field.get("field_name", "") for field in fields if field.get("field_name")}


def create_text_field(config, tenant_access_token, field_name):
    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json",
    }
    url = get_fields_url(config)
    payload = {
        "field_name": field_name,
        "type": TEXT_FIELD_TYPE,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"\n创建字段: {field_name}")
        print(f"response.status_code: {response.status_code}")
        print(f"response.text: {response.text}")

        if response.status_code != 200:
            return False

        result = response.json()
        return result.get("code") == 0
    except requests.exceptions.RequestException as error:
        print(f"\n创建字段: {field_name}")
        print(f"请求异常: {error}")
        return False


def main():
    config = load_feishu_config()
    validate_token_format(config)
    tenant_access_token = get_tenant_access_token(config)
    existing_fields = list_existing_fields(config, tenant_access_token)
    missing_fields = [field_name for field_name in REQUIRED_FIELDS if field_name not in existing_fields]

    print("已存在字段：")
    if existing_fields:
        for field_name in sorted(existing_fields):
            print(f"- {field_name}")
    else:
        print("- 无")

    print("\n缺失字段：")
    if missing_fields:
        for field_name in missing_fields:
            print(f"- {field_name}")
    else:
        print("- 无")

    print("\n缺失字段名清单：")
    if missing_fields:
        print("\n".join(missing_fields))
    else:
        print("- 无")
        return

    created_fields = []
    failed_fields = []

    print("\n开始自动创建缺失字段：")
    for field_name in missing_fields:
        success = create_text_field(config, tenant_access_token, field_name)
        if success:
            created_fields.append(field_name)
        else:
            failed_fields.append(field_name)

    print("\n创建成功字段：")
    if created_fields:
        for field_name in created_fields:
            print(f"- {field_name}")
    else:
        print("- 无")

    print("\n创建失败字段：")
    if failed_fields:
        for field_name in failed_fields:
            print(f"- {field_name}")
    else:
        print("- 无")

    print("\n重新读取字段列表，确认最终缺失字段：")
    final_existing_fields = list_existing_fields(config, tenant_access_token)
    final_missing_fields = [field_name for field_name in REQUIRED_FIELDS if field_name not in final_existing_fields]

    if final_missing_fields:
        print("最终仍缺失字段：")
        for field_name in final_missing_fields:
            print(f"- {field_name}")
    else:
        print("所有 REQUIRED_FIELDS 均已存在。")


if __name__ == "__main__":
    main()
