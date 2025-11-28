#!/bin/bash
set -e

# 檢查配置文件
if [ ! -f "/app/config/config.yaml" ] || [ ! -f "/app/config/frequency_words.txt" ]; then
    echo "❌ 配置文件缺失"
    exit 1
fi

# 保存環境變量
env >> /etc/environment

case "${RUN_MODE:-cron}" in
"once")
    echo "🔄 單次執行"
    exec /usr/local/bin/python main.py
    ;;
"cron")
    # 生成 crontab
    echo "${CRON_SCHEDULE:-*/30 * * * *} cd /app && /usr/local/bin/python main.py" > /tmp/crontab
    
    echo "📅 生成的crontab內容:"
    cat /tmp/crontab

    if ! /usr/local/bin/supercronic -test /tmp/crontab; then
        echo "❌ crontab格式驗證失敗"
        exit 1
    fi

    # 立即執行一次（如果配置了）
    if [ "${IMMEDIATE_RUN:-false}" = "true" ]; then
        echo "▶️ 立即執行一次"
        /usr/local/bin/python main.py
    fi

    echo "⏰ 啓動supercronic: ${CRON_SCHEDULE:-*/30 * * * *}"
    echo "🎯 supercronic 將作爲 PID 1 運行"
    
    exec /usr/local/bin/supercronic -passthrough-logs /tmp/crontab
    ;;
*)
    exec "$@"
    ;;
esac