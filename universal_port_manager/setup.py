#!/usr/bin/env python3
"""
Universal Port Manager 설치 스크립트
==================================

다양한 의존성 시나리오를 지원하는 유연한 설치 시스템
"""

from setuptools import setup, find_packages
from pathlib import Path

# README 파일 읽기
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "Universal Port Manager - 다중 프로젝트 포트 충돌 방지 도구"

# 최소 의존성 (기본 기능만)
minimal_requirements = [
    "click>=8.0.0",
]

# 전체 의존성 (모든 기능)
full_requirements = minimal_requirements + [
    "psutil>=5.9.0",
    "PyYAML>=6.0",
    "requests>=2.28.0",
]

# 개발 의존성
dev_requirements = full_requirements + [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "flake8>=5.0.0",
]

setup(
    name="universal-port-manager",
    version="2.0.0",
    author="Claude Code Team",
    author_email="support@anthropic.com",
    description="다중 프로젝트 포트 충돌 방지 및 자동 할당 도구",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    
    # 기본 설치 (최소 의존성)
    install_requires=minimal_requirements,
    
    # 추가 기능 그룹
    extras_require={
        "full": full_requirements,
        "minimal": minimal_requirements,
        "dev": dev_requirements,
        "docker": ["PyYAML>=6.0"],
        "advanced": ["psutil>=5.9.0", "PyYAML>=6.0"],
    },
    
    # CLI 엔트리 포인트
    entry_points={
        "console_scripts": [
            "universal-port-manager=universal_port_manager.cli:cli",
            "upm=universal_port_manager.cli:cli",  # 짧은 별칭
        ],
    },
    
    # 패키지 데이터
    package_data={
        "universal_port_manager": [
            "templates/*.yml",
            "templates/*.yaml", 
            "templates/*.json",
        ],
    },
    
    # 분류자
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Tools",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
    ],
    
    # 키워드
    keywords="port-management docker-compose multi-project development-tools networking",
    
    # 프로젝트 URL
    project_urls={
        "Bug Reports": "https://github.com/anthropics/claude-code/issues",
        "Source": "https://github.com/anthropics/universal-port-manager",
        "Documentation": "https://docs.anthropic.com/en/docs/claude-code",
    },
)