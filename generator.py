
import os
import requests
import resend
import html

# Load the Resend API key from an environment variable.
resend.api_key = os.getenv("RESEND_API_KEY", "")



def generate_outreach_email(
    business_name="Business",
    business_type="",
    website="",
    additional_context=""
):
    return f"""
Subject: Helping {business_name} Grow Its Business

Hello {business_name} Team,

I came across your business and wanted to introduce
our professional digital solutions.

We help businesses improve their online presence,
customer engagement and operational efficiency.

Website: {website}

{additional_context}

Would you be available for a brief discussion?

Best regards,
JohnnyEdge Limited
JEdge Connect
"""


def generate_followup_email(
    business_name="Business",
    previous_message="",
    additional_context=""
):
    return f"""
Subject: Following Up – {business_name}

Hello {business_name} Team,

I am following up on my previous message.

{previous_message}

{additional_context}

Please let me know if you would be interested
in discussing how we can help your business.

Best regards,
JohnnyEdge Limited
JEdge Connect
"""


def send_outreach_email(
    recipient_email,
    subject,
    email_body,
    sender=None
):
    if not resend.api_key:
        return False, "RESEND_API_KEY is not configured."

    try:
        params = {
            "from": sender or "JEdge Connect <connect@johnnyedgelimited.com>",
            "to": [recipient_email],
            "subject": subject,
            "html": f"""
            <div style="font-family:Arial,sans-serif;color:#333;line-height:1.6;">

                <div style="text-align:center;padding:20px;background:#f5f7fa;">
                    <img
                        src="https://raw.githubusercontent.com/udochukwu13/ai-lead-generator/main/jedge_logo.png"
                        alt="JEdge Connect"
                        width="180"
                        style="max-width:100%;height:auto;"
                    >
                </div>

                <div style="padding:20px;">
                    {email_body.replace(chr(10), '<br>')}
                </div>

                <hr style="border:0;border-top:1px solid #ddd;">

                <p style="text-align:center;font-size:12px;color:#777;">
                    Powered by JEdge Connect<br>
                    Smart Lead Generation • Business Growth
                </p>
            </div>
            """
        }

        result = resend.Emails.send(params)
        return True, result

    except Exception as error:
        return False, str(error)

def analyze_website_health(url):
    if not url:
        return {"success": False, "error": "Website URL is required."}

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        return {

            "success": True,
            "url": url,
            "status_code": response.status_code,
            "https": url.startswith("https://"),
            "load_time_seconds": response.elapsed.total_seconds(),
            "page_title": (
                html.escape(response.text.split("<title>")[1].split("</title>")[0])
                if "<title>" in response.text.lower()
                else "Title not detected"
            )
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "url": url,
            "error": str(error)
        }


def send_audit_email(
    client_email,
    client_name,
    audit_report_html
):
    if not resend.api_key:
        return False, "RESEND_API_KEY is not configured."

    try:
        params = {
            "from": "JEdge Connect <connect@johnnyedgelimited.com>",
            "to": [client_email],
            "subject": f"Website & SEO Audit Report for {client_name}",
            "html": audit_report_html
        }

        result = resend.Emails.send(params)
        return True, result

    except Exception as error:
        return False, str(error)


def generate_audit_html(
    target_url,
    seo_score,
    load_speed,
    has_https
):
    https_status = (
        "Secure (HTTPS)"
        if has_https
        else "Missing HTTPS (Not Secure)"
    )

    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;
                margin:auto;padding:20px;color:#333;">

        <h2>Website Audit Report</h2>

        <p>Hello,</p>

        <p>We reviewed your website:
        <strong>{html.escape(target_url)}</strong></p>

        <div style="background:#f8fafc;padding:15px;">
            <p><strong>SEO Health Score:</strong> {seo_score}/100</p>
            <p><strong>Server Status:</strong> Online</p>
            <p><strong>Load Speed:</strong> {html.escape(str(load_speed))}</p>
            <p><strong>HTTPS Security:</strong> {https_status}</p>
        </div>

        <p>Best regards,<br>
        <strong>JEdge Connect Team</strong><br>
        johnnyedgelimited.com</p>

    </div>
    """

          

