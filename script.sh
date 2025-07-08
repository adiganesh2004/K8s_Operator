#!/bin/bash

NAMESPACE=default
TOTAL_DIFF=0
COUNT=0

echo "Fetching mongo-worker pods in namespace: $NAMESPACE"

# Get all pod names starting with mongo-worker
PODS=$(oc get pods -n "$NAMESPACE" --no-headers | awk '/^mongo-worker/ {print $1}')

for POD in $PODS; do
    echo "Processing pod: $POD"
    EVENTS=$(oc describe pod "$POD" -n "$NAMESPACE" | awk '/^Events:/,/^$/')

    # Extract Scheduled and Started timestamps
    SCHEDULED_TIME=$(echo "$EVENTS" | grep 'Scheduled' | awk '{print $(NF-1)}' | head -n1)
    STARTED_TIME=$(echo "$EVENTS" | grep 'Started' | awk '{print $(NF-1)}' | head -n1)

    # Skip if any timestamp missing
    if [[ -z "$SCHEDULED_TIME" || -z "$STARTED_TIME" ]]; then
        echo "  Skipping $POD (missing Scheduled or Started)"
        continue
    fi

    # Convert to epoch using `date -d`, works in Git Bash
    SCHEDULED_EPOCH=$(date -d "$SCHEDULED_TIME" +%s 2>/dev/null)
    STARTED_EPOCH=$(date -d "$STARTED_TIME" +%s 2>/dev/null)

    # Skip if time conversion failed
    if [[ -z "$SCHEDULED_EPOCH" || -z "$STARTED_EPOCH" ]]; then
        echo "  Skipping $POD (bad timestamp)"
        continue
    fi

    DIFF=$((STARTED_EPOCH - SCHEDULED_EPOCH))
    echo "  Time diff (Started - Scheduled): $DIFF sec"

    TOTAL_DIFF=$((TOTAL_DIFF + DIFF))
    COUNT=$((COUNT + 1))
done

echo "--------------------------------------------"
if [[ $COUNT -gt 0 ]]; then
    AVG=$((TOTAL_DIFF / COUNT))
    echo "Average startup delay across $COUNT pods: $AVG seconds"
else
    echo "No valid mongo-worker pods found with both timestamps."
fi
