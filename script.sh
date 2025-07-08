#!/bin/bash

NAMESPACE=default
TOTAL_DIFF=0
COUNT=0

echo "Fetching mongo-worker pods in namespace: $NAMESPACE"

# Get pods starting with mongo-worker
PODS=$(kubectl get pods -n "$NAMESPACE" --no-headers | awk '/^mongo-worker/ {print $1}')

for POD in $PODS; do
    echo "Processing pod: $POD"
    EVENTS=$(kubectl describe pod "$POD" -n "$NAMESPACE")

    # Extract the Age values for Scheduled and Started
    SCHEDULED_AGE=$(echo "$EVENTS" | awk '/Scheduled/ && !seen++ {print $(NF-2)}')
    STARTED_AGE=$(echo "$EVENTS" | awk '/Started/ && !seen++ {print $(NF-2)}')

    # Skip if either is missing
    if [[ -z "$SCHEDULED_AGE" || -z "$STARTED_AGE" ]]; then
        echo "  Skipping (missing Scheduled/Started age)"
        continue
    fi

    # Function to convert age (e.g., 4d2h, 1m20s) to seconds
    age_to_seconds() {
        local age="$1"
        local total=0
        if [[ "$age" =~ ([0-9]+)d ]]; then
            total=$((total + ${BASH_REMATCH[1]} * 86400))
        fi
        if [[ "$age" =~ ([0-9]+)h ]]; then
            total=$((total + ${BASH_REMATCH[1]} * 3600))
        fi
        if [[ "$age" =~ ([0-9]+)m ]]; then
            total=$((total + ${BASH_REMATCH[1]} * 60))
        fi
        if [[ "$age" =~ ([0-9]+)s ]]; then
            total=$((total + ${BASH_REMATCH[1]}))
        fi
        echo "$total"
    }

    SCHED_SECS=$(age_to_seconds "$SCHEDULED_AGE")
    START_SECS=$(age_to_seconds "$STARTED_AGE")

    DIFF=$((SCHED_SECS - START_SECS))
    if (( DIFF < 0 )); then
        DIFF=$(( -DIFF ))
    fi

    echo "  Scheduled age: $SCHEDULED_AGE ($SCHED_SECS s), Started age: $STARTED_AGE ($START_SECS s), Diff: $DIFF s"

    TOTAL_DIFF=$((TOTAL_DIFF + DIFF))
    COUNT=$((COUNT + 1))
done

echo "---------------------------------------------------"
if [[ $COUNT -gt 0 ]]; then
    AVG=$((TOTAL_DIFF / COUNT))
    echo "Average startup delay (Scheduled → Started): $AVG seconds across $COUNT pods"
else
    echo "No valid mongo-worker pods found with event ages."
fi
