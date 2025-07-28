"""Email service stub."""

from typing import Optional


class EmailService:
    """Email service for sending notifications."""

    @staticmethod
    def send_email(
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> bool:
        """
        Send email (stub implementation).
        
        In production, this would integrate with an email service
        like SendGrid, AWS SES, or similar.
        """
        print(f"Email would be sent to: {to}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        return True

    @staticmethod
    def send_password_reset_email(
        email: str,
        reset_url: str,
        verification_code: str,
    ) -> bool:
        """Send password reset email."""
        subject = "パスワードリセットのご案内"
        body = f"""
パスワードリセットが要求されました。

リセットURL: {reset_url}
確認コード: {verification_code}

このリンクは1時間有効です。

このメールに心当たりがない場合は、無視してください。
        """
        
        return EmailService.send_email(email, subject, body)

    @staticmethod
    def send_mfa_setup_email(
        email: str,
        device_name: str,
    ) -> bool:
        """Send MFA setup confirmation email."""
        subject = "多要素認証が設定されました"
        body = f"""
お使いのアカウントで多要素認証が設定されました。

デバイス名: {device_name}

この操作に心当たりがない場合は、すぐにサポートにご連絡ください。
        """
        
        return EmailService.send_email(email, subject, body)

    @staticmethod
    def send_new_device_alert(
        email: str,
        device_info: dict,
        ip_address: str,
    ) -> bool:
        """Send new device login alert."""
        subject = "新しいデバイスからのログイン"
        body = f"""
新しいデバイスからログインがありました。

デバイス: {device_info.get('browser', 'Unknown')} on {device_info.get('os', 'Unknown')}
IPアドレス: {ip_address}

このログインに心当たりがない場合は、パスワードを変更してください。
        """
        
        return EmailService.send_email(email, subject, body)