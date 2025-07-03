from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                            QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit)
from PyQt6.QtCore import Qt, QSize
import boto3
import qtawesome as qta
from typing import Optional, Tuple
import os
import tempfile
from dotenv import load_dotenv
from pathlib import Path
from fastapi import APIRouter
from datetime import datetime

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

router = APIRouter()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION")
)

bucket_name = os.getenv("AWS_S3_BUCKET")

@router.get("/api/s3-ss3-tree")
async def get_s3_tree():
    paginator = s3.get_paginator("list_objects_v2")
    result = []

    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            if not obj['Key'].lower().endswith(".dcm"):
                continue

            path_parts = obj['Key'].split('/')
            current = result

            for i, part in enumerate(path_parts):
                existing = next((item for item in current if item["name"] == part), None)
                if existing:
                    current = existing.setdefault("children", [])
                else:
                    node = {
                        "name": part,
                        "type": "folder" if i < len(path_parts) - 1 else "file",
                        "size": obj['Size'] if i == len(path_parts) - 1 else None,
                        "last_modified": obj['LastModified'].isoformat() if i == len(path_parts) - 1 else None
                    }
                    current.append(node)
                    current = node.setdefault("children", []) if node["type"] == "folder" else []
    return result


class S3Browser(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_file = None
        self.s3_client = None
        self.bucket_name = bucket_name

        self._init_ui()
        self._connect_to_s3()

    def _init_ui(self):
        self.setWindowTitle("S3 DICOM Browser")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: Not Connected")
        status_layout.addWidget(self.status_label)
        self.refresh_button = QPushButton()
        self.refresh_button.setIcon(qta.icon('fa5s.sync', color='#ffffff'))
        self.refresh_button.setIconSize(QSize(16, 16))
        self.refresh_button.clicked.connect(self._refresh_files)
        status_layout.addWidget(self.refresh_button)
        layout.addLayout(status_layout)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.textChanged.connect(self._filter_items)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Size", "Last Modified"])
        self.tree.setColumnWidth(0, 300)
        self.tree.itemDoubleClicked.connect(self._item_double_clicked)
        layout.addWidget(self.tree)

        # Buttons
        button_layout = QHBoxLayout()
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.accept)
        self.select_button.setEnabled(False)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Style
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #ffffff; }
            QLabel, QTreeWidget { color: #ffffff; }
            QPushButton {
                background-color: #3b3b3b;
                color: #ffffff;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #454545; }
            QPushButton:pressed { background-color: #505050; }
            QPushButton:disabled { background-color: #2b2b2b; color: #666666; }
            QLineEdit {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #505050;
                padding: 5px;
                border-radius: 4px;
            }
            QTreeWidget {
                background-color: #3b3b3b;
                border: 1px solid #505050;
                border-radius: 4px;
            }
            QTreeWidget::item { color: #ffffff; }
            QTreeWidget::item:selected { background-color: #505050; }
        """)

    def _connect_to_s3(self):
        try:
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            aws_region = os.getenv('AWS_DEFAULT_REGION')

            if not all([aws_access_key, aws_secret_key, aws_region, self.bucket_name]):
                raise ValueError("Missing required AWS credentials in .env file")

            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )

            self.status_label.setText("Status: Connected")
            self._refresh_files()
        except Exception as e:
            self.status_label.setText(f"Status: Connection Error - {str(e)}")

    def _refresh_files(self):
        self.tree.clear()
        if not self.s3_client or not self.bucket_name:
            return

        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name):
                for obj in page.get('Contents', []):
                    if not obj['Key'].lower().endswith('.dcm'):
                        continue

                    path_parts = obj['Key'].split('/')
                    current_item = self.tree.invisibleRootItem()

                    for i, part in enumerate(path_parts):
                        found = False
                        for j in range(current_item.childCount()):
                            if current_item.child(j).text(0) == part:
                                current_item = current_item.child(j)
                                found = True
                                break

                        if not found:
                            item = QTreeWidgetItem([part])
                            if i == len(path_parts) - 1:
                                size_mb = obj['Size'] / (1024 * 1024)
                                item.setText(1, f"{size_mb:.2f} MB")
                                item.setText(2, obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S'))
                            current_item.addChild(item)
                            current_item = item

        except Exception as e:
            self.status_label.setText(f"Status: Error loading files - {str(e)}")

    def _filter_items(self, text):
        def filter_tree_item(item: QTreeWidgetItem, filter_text: str) -> bool:
            if filter_text.lower() in item.text(0).lower():
                return True
            for i in range(item.childCount()):
                if filter_tree_item(item.child(i), filter_text):
                    return True
            return False

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setHidden(not filter_tree_item(item, text))

    def _item_double_clicked(self, item: QTreeWidgetItem, column: int):
        if item.childCount() == 0:
            self.selected_file = self._get_full_path(item)
            self.select_button.setEnabled(True)

    def _get_full_path(self, item: QTreeWidgetItem) -> str:
        path_parts = []
        while item is not None:
            path_parts.insert(0, item.text(0))
            item = item.parent()
        return '/'.join(path_parts)

    def get_selected_file(self) -> Tuple[bool, Optional[str]]:
        if not self.selected_file:
            return False, None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dcm') as tmp_file:
                self.s3_client.download_file(
                    self.bucket_name,
                    self.selected_file,
                    tmp_file.name
                )
                return True, tmp_file.name
        except Exception as e:
            print(f"Error downloading file: {str(e)}")
            return False, None