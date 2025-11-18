# Columba Design Document

**Language**: Python 

**Introduction**: Columba is a lightweight and user-friendly Python library for email notifications. Through simple configuration, it quickly integrates email sending functionality, supporting text/HTML emails, attachments, self-notification, and other common scenarios.

---

## Core Class: `Columba`

### 1. Initialization Method

```python
def __init__(
    self,
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    use_tls: bool = True,
    timeout: int = 30
)
```

**Parameter Description**:
- `smtp_host` (str): SMTP server address, e.g., "smtp.163.com"
- `smtp_port` (int): SMTP server port, typically 465 (SSL) or 587 (TLS)
- `username` (str): Sender's email account
- `password` (str): Email authorization code (not login password)
- `use_tls` (bool, optional): Whether to enable TLS encryption, default is True
- `timeout` (int, optional): Connection timeout in seconds, default is 30

**Function**: Initializes the email client and establishes SMTP server connection configuration. **It is recommended to store sensitive information using environment variables or configuration files**.

---

### 2. Send Notification

```python
def send(
    self,
    to: str | list[str],
    subject: str,
    content: str,
    content_type: str = "plain",
    attachments: list[str] | None = None,
    cc: str | list[str] | None = None,
    bcc: str | list[str] | None = None
) -> dict
```

**Parameter Description**:
- `to` (str or list): Recipient's email account(s), supports single string or list
- `subject` (str): Email subject
- `content` (str): Email body content
- `content_type` (str, optional): Content type, "plain" for plain text (default), "html" for HTML format
- `attachments` (list, optional): List of attachment file paths
- `cc` (str or list, optional): CC (Carbon Copy) email account(s)
- `bcc` (str or list, optional): BCC (Blind Carbon Copy) email account(s)

**Return Value**: `dict` containing send result
- `success`: bool type, indicating success or failure
- `message`: str type, success or error message
- `msg_id`: str type (when successful), email message ID

**Exception**: `ColumbaSendError` is raised when sending fails

---

### 3. Send Notification to Self

```python
def send_to_self(
    self,
    subject: str,
    content: str,
    content_type: str = "plain",
    attachments: list[str] | None = None
) -> dict
```

**Parameter Description**:
- `subject` (str): Email subject
- `content` (str): Email body content
- `content_type` (str, optional): Content type, "plain" for plain text (default), "html" for HTML format
- `attachments` (list, optional): List of attachment file paths

**Return Value and Exception**: Same as `send()` method

**Function**: Quickly send an email to the sender's own email account configured during initialization, suitable for system self-monitoring and log alert scenarios.

---

---

## Usage Examples

### Basic Usage
```python
from columba import Columba

# Initialize
email = Columba(
    smtp_host="smtp.163.com",
    smtp_port=465,
    username="your-email@163.com",
    password="your-auth-code"  # 163 email authorization code
)

# Send plain text email
result = email.send(
    to="user@example.com",
    subject="System Alert",
    content="Server CPU usage exceeded 90%!"
)

# Send HTML email
html_content = "<h1>System Report</h1><p style='color: red;'>Please check attachment promptly</p>"
result = email.send(
    to=["user1@example.com", "user2@example.com"],
    subject="Daily Report",
    content=html_content,
    content_type="html",
    attachments=["/path/to/report.pdf"]
)

# Self notification
email.send_to_self(
    subject="Backup Complete",
    content="Database backup executed successfully"
)
```

---

## Exception Handling

```python
from columba import Columba, ColumbaSendError

try:
    email = Columba(...)
    result = email.send(...)
except ColumbaSendError as e:
    print(f"Email sending failed: {e}")
    # Log error or trigger fallback strategy
```

---