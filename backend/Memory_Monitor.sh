#!/bin/bash

# Script file path: /root/redis_memory_monitor.sh
# Log file path: /var/log/redis_memory.log
# Memory threshold: 1024MB (1GB)

LOG_FILE="/var/log/redis_memory.log"
THRESHOLD_MB=1024  # 1GB limit for testing

# Convert Redis RSS memory usage to MB
REDIS_MEMORY=$(redis-cli info memory | grep used_memory_rss_human | awk -F ':' '{print $2}' | tr -d '\r' | tr -d ' ' | sed 's/K/*0.001/g' | sed 's/M//g' | sed 's/G/*1024/g' | bc)

# Log memory usage
echo "$(date) - Redis RSS Memory Usage: ${REDIS_MEMORY} MB" >> $LOG_FILE

# Check if memory exceeds threshold
if (( $(echo "$REDIS_MEMORY > $THRESHOLD_MB" | bc -l) == 1 )); then
    echo "$(date) - WARNING: Redis memory usage exceeded ${THRESHOLD_MB} MB!" >> $LOG_FILE
    
    
    redis-cli memory purge
    echo "$(date) - Executed MEMORY PURGE to free unused memory." >> $LOG_FILE

    # Check memory again
    sleep 5  # Allow time
    FINAL_REDIS_MEMORY=$(redis-cli info memory | grep used_memory_rss_human | awk -F ':' '{print $2}' | tr -d '\r' | tr -d ' ' | sed 's/K/*0.001/g' | sed 's/M//g' | sed 's/G/*1024/g' | bc)

    # If memory is still above threshold, restart Redis
    if (( $(echo "$FINAL_REDIS_MEMORY > $THRESHOLD_MB" | bc -l) )); then
        echo "$(date) - CRITICAL: Memory still high after all attempts. Restarting Redis..." >> $LOG_FILE
        systemctl restart redis
    else
        echo "$(date) - Memory usage reduced after purge. No restart needed." >> $LOG_FILE
    fi

# If memory is below threshold, log a normal status
else
    echo "$(date) - Memory OK: Redis memory is within limits." >> $LOG_FILE
fi
