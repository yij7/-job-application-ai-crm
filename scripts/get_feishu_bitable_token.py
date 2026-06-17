import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
FEISHU_WIKI_NODE_URL = "https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node"


def load_feishu_config():
    load_dotenv(PROJECT_ROOT / ".env")

    app_id = os.getenv("FEISHU_APP_ID", "").strip()
    app_secret = os.getenv("FEISHU_APP_SECRET", "").strip()

    if not app_id or not app_secret:
        print("请先在项目根目录 .env 中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET。")
        sys.exit(1)

    return app_id, app_secret


def get_tenant_access_token(app_id, app_secret):
    payload = {
        "app_id": app_id,
        "app_secret": app_secret,
    }

    response = requests.post(FEISHU_TOKEN_URL, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()

    if result.get("code") != 0:
        print("获取 tenant_access_token 失败")
        print(f"请求 URL: {FEISHU_TOKEN_URL}")
        print(f"错误码: {result.get('code')}")
        print(f"错误信息: {result.get('msg')}")
        sys.exit(1)

    return result["tenant_access_token"]


def get_wiki_node_info(tenant_access_token, wiki_node_token):
    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json",
    }
    request_body = {
        "token": wiki_node_token,
    }

    response = requests.post(FEISHU_WIKI_NODE_URL, headers=headers, json=request_body, timeout=30)
    request_url = FEISHU_WIKI_NODE_URL

    print(f"request_url: {request_url}")
    print(f"request_body: {json.dumps(request_body, ensure_ascii=False)}")
    print(f"response.status_code: {response.status_code}")
    print(f"response.text: {response.text}")

    response.raise_for_status()
    result = response.json()

    if result.get("code") != 0:
        print("获取 wiki 节点信息失败")
        print(f"请求 URL: {FEISHU_WIKI_NODE_URL}")
        print(f"错误码: {result.get('code')}")
        print(f"错误信息: {result.get('msg')}")
        sys.exit(1)

    data = result.get("data", {})
    node_info = data.get("node", data)

    return node_info, request_url, result


def get_wiki_node_token_from_args():
    parser = argparse.ArgumentParser(
        description="从飞书 wiki node token 获取多维表格 app_token。"
    )
    parser.add_argument(
        "wiki_node_token",
        nargs="?",
        help="飞书 wiki 链接中 wiki/ 后面的 token，例如 KXlzwMEMtidcVWkKEOicN76In3L。",
    )
    args = parser.parse_args()

    if args.wiki_node_token:
        return args.wiki_node_token.strip()

    return input("请输入 wiki_node_token: ").strip()


def main():
    wiki_node_token = get_wiki_node_token_from_args()
    if not wiki_node_token:
        print("wiki_node_token 不能为空。")
        sys.exit(1)

    app_id, app_secret = load_feishu_config()
    tenant_access_token = get_tenant_access_token(app_id, app_secret)
    node_info, request_url, full_response = get_wiki_node_info(tenant_access_token, wiki_node_token)

    obj_type = node_info.get("obj_type", "")
    obj_token = node_info.get("obj_token", "")

    print(f"wiki_node_token: {wiki_node_token}")
    print(f"request_url: {request_url}")
    print(f"obj_type: {obj_type}")
    print(f"obj_token: {obj_token}")

    if obj_type == "bitable" and obj_token:
        print(f"FEISHU_APP_TOKEN={obj_token}")
        print("请将 FEISHU_APP_TOKEN 设置为 obj_token。")
    else:
        print("当前 wiki 节点不是 bitable，或接口没有返回 obj_token。")
        print("完整 response:")
        print(json.dumps(full_response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
