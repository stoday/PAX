from setuptools import setup, find_packages
import os

# 讀取 README
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "ClockMate - 工時填報助手"

# 讀取依賴套件
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="clockmate",
    version="1.0.0",
    author="ClockMate Team",
    author_email="support@clockmate.com",
    description="工時填報自動化助手",
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
        ],
    },
    include_package_data=True,
    package_data={
        "clockmate": ["*.txt", "*.md"],
    },
)
