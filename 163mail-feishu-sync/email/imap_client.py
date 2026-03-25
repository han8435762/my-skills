import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import re
from datetime import datetime, timedelta, timezone


def decode_str(header_value):
    if not header_value:
        return ""
    decoded_list = decode_header(header_value)
    result = ""
    for content, encoding in decoded_list:
        if isinstance(content, bytes):
            try:
                result += content.decode(encoding or "utf-8", errors="ignore")
            except (LookupError, TypeError):
                result += content.decode("utf-8", errors="ignore")
        else:
            result += str(content)
    return result


def clean_email_address(from_str):
    match = re.search(r"<(.+?)>", from_str)
    if match:
        return match.group(1).strip()
    return from_str.strip()


def get_from_name(from_str):
    match = re.search(r"<(.+?)>", from_str)
    if match:
        name = from_str[: from_str.index("<")].strip().strip('"')
        return name if name else clean_email_address(from_str).split("@")[0]
    return from_str.split("@")[0]


def get_email_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        body += payload.decode(charset, errors="ignore")
                except Exception:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="ignore")
        except Exception:
            pass
    return body.strip()


def get_email_attachments(msg):
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    attachments.append(decode_str(filename))
    return attachments


def parse_email_date(date_str):
    try:
        dt = parsedate_to_datetime(date_str)
        return int(dt.timestamp() * 1000)
    except Exception:
        return int(datetime.now().timestamp() * 1000)


def connect_imap(config):
    imap = imaplib.IMAP4_SSL(config["imap"]["server"], config["imap"]["port"])
    imap.login(config["imap"]["email"], config["imap"]["password"])

    # 163邮箱要求发送IMAP ID，避免被封
    imaplib.Commands["ID"] = ("AUTH",)
    args = ("name", "IMAPClient", "version", "1.0", "vendor", "python")
    imap._simple_command("ID", '("' + '" "'.join(args) + '")')

    return imap


def fetch_emails(config, days=None, hours=None):
    """
    从163邮箱获取邮件列表。
    days: 获取最近N天的邮件
    hours: 获取最近N小时的邮件
    返回 list of dict，每个 dict 包含邮件信息。
    """
    imap = connect_imap(config)
    imap.select("INBOX")

    if days is not None:
        since_dt = datetime.now(timezone.utc) - timedelta(days=days)
    elif hours is not None:
        since_dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    else:
        since_dt = datetime.now(timezone.utc) - timedelta(hours=6)

    since_str = since_dt.strftime("%d-%b-%Y")
    status, messages = imap.search(None, f'SINCE "{since_str}"')

    if status != "OK":
        imap.close()
        imap.logout()
        return []

    email_ids = messages[0].split()
    print(f"找到 {len(email_ids)} 封邮件（SINCE {since_str}）")

    results = []
    for eid in email_ids:
        try:
            status, msg_data = imap.fetch(eid, "(RFC822)")
            if status != "OK":
                continue

            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            from_raw = decode_str(msg.get("From", ""))
            subject = decode_str(msg.get("Subject", ""))
            message_id = msg.get("Message-ID", "").strip()
            date_str = msg.get("Date", "")

            body = get_email_body(msg)
            attachments = get_email_attachments(msg)

            results.append(
                {
                    "message_id": message_id,
                    "subject": subject,
                    "from_raw": from_raw,
                    "from_name": get_from_name(from_raw),
                    "from_email": clean_email_address(from_raw),
                    "date_str": date_str,
                    "timestamp_ms": parse_email_date(date_str),
                    "body": body,
                    "attachments": attachments,
                }
            )
        except Exception as e:
            print(f"解析邮件失败: {e}")
            continue

    imap.close()
    imap.logout()
    return results
