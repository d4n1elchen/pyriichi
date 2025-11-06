#!/bin/bash
# 在虛擬環境中運行測試的腳本

set -e

# 激活虛擬環境
source .venv/bin/activate

# 運行測試
if [ "$1" == "" ]; then
    # 運行所有測試
    python -m pytest tests/ -v
else
    # 運行指定的測試文件或測試用例
    python -m pytest "$@" -v
fi
