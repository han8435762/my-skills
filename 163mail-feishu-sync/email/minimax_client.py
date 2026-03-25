import requests
import json


MINIMAX_API_URL = "https://api.minimax.io/v1/text/chatcompletion_v2"

SYSTEM_PROMPT = """你是邮件分析助手，专注于泵行业外贸邮件。请根据邮件内容提取关键信息，返回严格的JSON格式，不要包含任何其他文字。"""

USER_PROMPT_TEMPLATE = """请分析以下邮件，返回JSON格式（所有字段必须存在）：
{{
  "pump_type_in_subject": "从邮件标题中提取的泵类型文本（如'离心泵'、'centrifugal pump'），标题中没有泵相关词汇则返回空字符串",
  "country": "客户所在国家（中文名称，如'印度尼西亚'、'美国'，无法判断则返回空字符串）",
  "contact_name": "联系人姓名（从发件人名称或正文签名提取，无法识别则返回空字符串）",
  "product_type": "产品/泵类型（从正文内容识别，如'离心泵'、'潜水泵'，无法识别则返回空字符串）",
  "quality_grade": "质检等级：A=严重问题影响使用，B=一般问题可维修，C=咨询/询价类。必须返回A、B或C之一",
  "repair_count": 0,
  "notes": "关键需求摘要（100字以内的中文摘要，描述客户的核心需求）",
  "chinese_content": "邮件内容的中文翻译（若已是中文则直接返回，保留关键信息，限1000字以内）"
}}

邮件标题：{subject}
发件人：{from_name} <{from_email}>
邮件正文：
{body}"""


def extract_ai_fields(config, subject, from_name, from_email, body):
    """
    调用 MiniMax API 一次性提取所有 AI 字段。
    返回 dict，失败时返回默认值。
    """
    api_key = config["minimax"]["api_key"]
    model = config["minimax"].get("model", "abab6.5s-chat")

    body_preview = body[:3000] if body else ""
    user_prompt = USER_PROMPT_TEMPLATE.format(
        subject=subject,
        from_name=from_name,
        from_email=from_email,
        body=body_preview,
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(MINIMAX_API_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"]

        # 提取JSON部分（防止模型输出额外文字）
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            content = content[json_start:json_end]

        result = json.loads(content)
        return _normalize_ai_result(result)

    except Exception as e:
        print(f"MiniMax AI提取失败: {e}")
        return _default_ai_result()


def _normalize_ai_result(result):
    defaults = _default_ai_result()
    for key, default_val in defaults.items():
        if key not in result:
            result[key] = default_val

    # 确保 quality_grade 是 A/B/C
    if result["quality_grade"] not in ("A", "B", "C"):
        result["quality_grade"] = "C"

    # 确保 repair_count 是数字
    try:
        result["repair_count"] = int(result["repair_count"])
    except (ValueError, TypeError):
        result["repair_count"] = 0

    return result


def _default_ai_result():
    return {
        "pump_type_in_subject": "",
        "country": "",
        "contact_name": "",
        "product_type": "",
        "quality_grade": "C",
        "repair_count": 0,
        "notes": "",
        "chinese_content": "",
    }
