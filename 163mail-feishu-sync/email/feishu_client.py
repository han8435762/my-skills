import requests
import time

FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"

_token_cache = {"token": None, "expire_at": 0}


def get_token(config):
    """获取 tenant_access_token，缓存2小时内有效"""
    now = time.time()
    if _token_cache["token"] and _token_cache["expire_at"] > now + 60:
        return _token_cache["token"]

    resp = requests.post(
        f"{FEISHU_BASE_URL}/auth/v3/tenant_access_token/internal",
        json={
            "app_id": config["feishu"]["app_id"],
            "app_secret": config["feishu"]["app_secret"],
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"获取飞书token失败: {data}")

    _token_cache["token"] = data["tenant_access_token"]
    _token_cache["expire_at"] = now + data.get("expire", 7200)
    return _token_cache["token"]


def _headers(config):
    return {
        "Authorization": f"Bearer {get_token(config)}",
        "Content-Type": "application/json",
    }


def create_bitable_app(config, name="163邮件同步"):
    """创建多维表格 App，返回 app_token"""
    resp = requests.post(
        f"{FEISHU_BASE_URL}/bitable/v1/apps",
        headers=_headers(config),
        json={"name": name},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"创建多维表格失败: {data}")
    return data["data"]["app"]["app_token"]


def create_table(config, app_token, table_name="邮件"):
    """创建表，返回 table_id"""
    resp = requests.post(
        f"{FEISHU_BASE_URL}/bitable/v1/apps/{app_token}/tables",
        headers=_headers(config),
        json={"table": {"name": table_name}},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"创建表失败: {data}")
    return data["data"]["table_id"]


def create_field(config, app_token, table_id, field_name, field_type, ui_type=None, property_=None):
    """创建字段"""
    body = {"field_name": field_name, "type": field_type}
    if ui_type:
        body["ui_type"] = ui_type
    if property_:
        body["property"] = property_
    resp = requests.post(
        f"{FEISHU_BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
        headers=_headers(config),
        json=body,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"创建字段 '{field_name}' 失败: {data}")
    return data["data"]["field"]["field_id"]


def list_fields(config, app_token, table_id):
    """列出表的所有字段名"""
    resp = requests.get(
        f"{FEISHU_BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
        headers=_headers(config),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"获取字段列表失败: {data}")
    return [f["field_name"] for f in data["data"]["items"]]


def record_exists_by_email_id(config, app_token, table_id, message_id):
    """通过邮件ID查询记录是否存在"""
    params = {
        "filter": f'CurrentValue.[邮件ID]="{message_id}"',
        "page_size": 1,
    }
    resp = requests.get(
        f"{FEISHU_BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
        headers=_headers(config),
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        return False
    return data["data"]["total"] > 0


def count_records_by_email(config, app_token, table_id, from_email):
    """统计同一发件人邮箱的记录数（用于计算交流次数）"""
    params = {
        "filter": f'CurrentValue.[发件人邮箱]="{from_email}"',
        "page_size": 1,
    }
    resp = requests.get(
        f"{FEISHU_BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
        headers=_headers(config),
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        return 0
    return data["data"]["total"]


def create_record(config, app_token, table_id, fields):
    """新增一条记录"""
    resp = requests.post(
        f"{FEISHU_BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
        headers=_headers(config),
        json={"fields": fields},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"新增记录失败: {data}")
    return data["data"]["record"]["record_id"]


def send_notification(config, message):
    """发飞书私信通知给 receiver_open_id"""
    open_id = config["feishu"]["receiver_open_id"]
    resp = requests.post(
        f"{FEISHU_BASE_URL}/im/v1/messages?receive_id_type=open_id",
        headers=_headers(config),
        json={
            "receive_id": open_id,
            "msg_type": "text",
            "content": f'{{"text": "{message}"}}',
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        print(f"发送通知失败: {data}")
