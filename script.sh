#!/bin/bash

NAMESPACE=default  # Change this if your pods are in a different namespace
TOTAL_DIFF=0
COUNT=0

echo "Fetching mongo-worker pod startup delays..."

# Get pods starting with mongo-worker
PODS=$(oc get pods -n "$NAMESPACE" --no-headers | awk '/^mongo-worker/ {print $1}')

for POD in $PODS; do
    echo "Processing pod: $POD"
    DESCRIBE=$(oc describe pod "$POD" -n "$NAMESPACE")

    SCHEDULED=$(echo "$DESCRIBE" | grep "Scheduled" | head -1 | awk '{print $(NF-1), $NF}')
    STARTED=$(echo "$DESCRIBE" | grep "Started" | head -1 | awk '{print $(NF-1), $NF}')

    if [[ -z "$SCHEDULED" || -z "$STARTED" ]]; then
        echo "  Skipping $POD due to missing times."
        continue
    fi

    # Convert to epoch seconds
    SCHED_EPOCH=$(date -d "$SCHEDULED" +%s)
    START_EPOCH=$(date -d "$STARTED" +%s)

    DIFF=$((START_EPOCH - SCHED_EPOCH))

    echo "  Time diff (s): $DIFF"

    TOTAL_DIFF=$((TOTAL_DIFF + DIFF))
    COUNT=$((COUNT + 1))
done

if [ "$COUNT" -gt 0 ]; then
    AVG=$((TOTAL_DIFF / COUNT))
    echo "---------------------------------"
    echo "Average startup delay: $AVG seconds"
else
    echo "No valid mongo-worker pods found."
fi
