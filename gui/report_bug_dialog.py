from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from tools.logger import get_logger
import os
import shutil
import time
import zipfile
import smtplib
from email.message import EmailMessage

logger = get_logger("ReportBugDialog")


class ReportBugDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Report Bug")
        self.resize(600, 400)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Describe the problem:"))
        self.desc = QTextEdit()
        layout.addWidget(self.desc)

        self.attach_button = QPushButton("Attach Additional File")
        self.send_button = QPushButton("Create Report")
        self.open_reports_button = QPushButton("Open Reports Folder")

        btn_h = QHBoxLayout()
        btn_h.addWidget(self.attach_button)
        btn_h.addStretch()
        btn_h.addWidget(self.open_reports_button)
        btn_h.addWidget(self.send_button)
        layout.addLayout(btn_h)

        self.attach_paths = []
        self.attach_button.clicked.connect(self._attach_file)
        self.send_button.clicked.connect(self._create_report)
        self.open_reports_button.clicked.connect(self._open_reports_folder)

        # Add upload/email options
        self.send_email_button = QPushButton("Send via Email")
        self.upload_github_button = QPushButton("Create GitHub Discussion")
        btn_h.addWidget(self.send_email_button)
        btn_h.addWidget(self.upload_github_button)
        self.send_email_button.clicked.connect(self._send_report_via_email)
        self.upload_github_button.clicked.connect(self._open_github_discussion)

    def _attach_file(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Attach file")
        if fp:
            self.attach_paths.append(fp)

    def _collect_logs(self, dest_dir):
        logs_dir = os.path.join(os.getcwd(), "logs")
        if os.path.isdir(logs_dir):
            for f in os.listdir(logs_dir):
                full = os.path.join(logs_dir, f)
                try:
                    shutil.copy2(full, dest_dir)
                except Exception as e:
                    logger.warning(f"Failed to copy log file {full}: {e}")

    def _create_report(self):
        text = self.desc.toPlainText().strip()
        if not text and not self.attach_paths:
            QMessageBox.warning(self, "Empty", "Please add a description or attach files.")
            return

        reports_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        ts = int(time.time())
        report_base = os.path.join(reports_dir, f"report_{ts}")
        os.makedirs(report_base, exist_ok=True)

        # save description
        try:
            with open(os.path.join(report_base, "description.txt"), "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            logger.error(f"Failed to write description: {e}")

        # copy logs
        try:
            self._collect_logs(report_base)
        except Exception as e:
            logger.warning(f"Failed to collect logs: {e}")

        # copy attachments
        for p in self.attach_paths:
            try:
                shutil.copy2(p, report_base)
            except Exception as e:
                logger.warning(f"Failed to copy attachment {p}: {e}")

        # create zip
        zip_path = shutil.make_archive(report_base, 'zip', report_base)
        QMessageBox.information(self, "Report Created", f"Report saved: {zip_path}")
        # Optionally upload if configured
        cfg = getattr(self.parent(), 'config', {})
        upload_url = cfg.get('report', {}).get('upload_url') if isinstance(cfg, dict) else None
        if upload_url:
            try:
                import requests

                with open(zip_path, 'rb') as fh:
                    files = {'file': fh}
                    resp = requests.post(upload_url, files=files, timeout=30)
                    if resp.status_code == 200:
                        QMessageBox.information(self, "Uploaded", "Report uploaded successfully.")
                    else:
                        QMessageBox.warning(self, "Upload Failed", f"Server responded: {resp.status_code}")
            except Exception as e:
                logger.error(f"Report upload failed: {e}")
                QMessageBox.warning(self, "Upload Failed", "Failed to upload report (see logs).")

        self.accept()

    def _send_report_via_email(self):
        # Create report first
        self._create_report()
        reports_dir = os.path.join(os.getcwd(), "reports")
        latest = sorted([p for p in os.listdir(reports_dir)], reverse=True)[0]
        zip_path = os.path.join(reports_dir, latest + ".zip")
        cfg = getattr(self.parent(), 'config', {})
        email_cfg = cfg.get('report', {}).get('email') if isinstance(cfg, dict) else None
        if not email_cfg:
            QMessageBox.information(self, "Email Not Configured", "No SMTP/email settings found in config.yaml. Report saved locally.")
            return
        try:
            msg = EmailMessage()
            msg['Subject'] = f"Bug Report - {os.path.basename(zip_path)}"
            msg['From'] = email_cfg.get('from')
            msg['To'] = email_cfg.get('to')
            msg.set_content(self.desc.toPlainText())
            with open(zip_path, 'rb') as fh:
                data = fh.read()
                msg.add_attachment(data, maintype='application', subtype='zip', filename=os.path.basename(zip_path))
            server = smtplib.SMTP(email_cfg.get('smtp_host', 'localhost'), int(email_cfg.get('smtp_port', 25)))
            if email_cfg.get('starttls'):
                server.starttls()
            if email_cfg.get('username'):
                server.login(email_cfg.get('username'), email_cfg.get('password'))
            server.send_message(msg)
            server.quit()
            QMessageBox.information(self, "Email Sent", "Report emailed successfully.")
        except Exception as e:
            logger.error(f"Failed to send report via email: {e}")
            QMessageBox.warning(self, "Email Failed", "Failed to send report via email. See logs.")

    def _open_github_discussion(self):
        # Create report first then open a new discussion page where user can paste details or attach file.
        self._create_report()
        try:
            QDesktopServices.openUrl(QUrl("https://github.com/BlackNodePacker/Girl-Packer/discussions/new"))
        except Exception:
            QMessageBox.information(self, "Open Browser", "Please open https://github.com/BlackNodePacker/Girl-Packer/discussions/new to create a discussion and attach the report zip.")

    def _open_reports_folder(self):
        reports_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        try:
            import webbrowser

            webbrowser.open(reports_dir)
        except Exception:
            QMessageBox.information(self, "Open Folder", f"Reports folder: {reports_dir}")
