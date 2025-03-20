#!/bin/bash

# Script file path: /root/redis_memory_monitor.sh
# Log file path: /var/log/redis_memory.log
 # https://www.groundcover.com/blog/monitor-redis
 # https://kloudvm.medium.com/simple-bash-script-to-monitor-cpu-memory-and-disk-usage-on-linux-in-10-lines-of-code-e4819fe38bf1

# This script monitors Redis memory usage and takes action if it exceeds a specified threshold.
# The main command is built with multiple pipes to dig through the redis-cli info memory output to extract the rss memory usage -
# 1. redis-cli info memory: This command retrieves memory information from Redis. 
# 2. grep used_memory_rss_human: This filters the output to find the line containing the RSS memory usage. 
# 3. awk -F ':': This splits the line at the colon value - after which is the memory usage value 
# 4. tr -d '\r': translate -d removes any carriage return characters from the output and also we remove the space
# 5. A series of sed pipes are used to conver the provided mem value up to the correct format of megabytes
# 6. bc piped to to preform calc


LOG_FILE="/var/log/redis_memory.log"
THRESHOLD_MB=1024  # 1GB limit 

# Convert Redis RSS memory usage to MB
# Redis rss memory usage is used to check the memory usage by whole Redis process - data and proc
# run redis cli info memory to get the memory usage by listening with grep and awk
REDIS_MEMORY=$(redis-cli info memory | grep used_memory_rss_human | awk -F ':' '{print $2}' | tr -d '\r' | tr -d ' ' | sed 's/K/*0.001/g' | sed 's/M//g' | sed 's/G/*1024/g' | bc)

# Log memory usage to log file for tracking
echo "$(date) - Redis RSS Memory Usage: ${REDIS_MEMORY} MB" >> $LOG_FILE

# Check if memory exceeds threshold set 
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
