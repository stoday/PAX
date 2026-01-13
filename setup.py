from setuptools import setup, find_packages
import os

# 讀取 README
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Pax - 便利工作助手"

# 讀取依賴套件
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="pax",
    version="2.0.0",
    author="ClockMate Team",
    author_email="support@clockmate.com",
    description="便利工作助手",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://gitlab-devops.iii.org.tw/iiidevops/p2025-clockmate.git",  # devops URL
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            # 主命令：直接啟動 SSH 服務（封裝於套件內路徑）
            "clockmate=clockmate.start_services:start_ssh_server",
            # 新別名：Pax
            "pax=clockmate.start_services:start_ssh_server",
            # 取得登入相關 Cookie/Token 的指令（與 .env.example 說明一致）
            "clockmate-token=clockmate.get_token:get_tokens_from_browser",
            "pax-token=clockmate.get_token:get_tokens_from_browser",
        ],
    },
    include_package_data=True,
    package_data={
        "clockmate": ["*.txt", "*.md"],
    },
)
