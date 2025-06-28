#!/usr/bin/env python3
"""
Universal Port Manager CLI Entry Point
======================================

모듈을 python -m universal_port_manager 형태로 실행할 수 있게 해주는 엔트리 포인트
"""

from .cli import cli

if __name__ == '__main__':
    cli()