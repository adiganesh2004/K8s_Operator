# Variables
REGISTRY ?= docker.io/adiganesh2004
WORKER_IMAGE := $(REGISTRY)/worker-app:latest
WATCHER_IMAGE := $(REGISTRY)/watcher:latest
OPERATOR_IMAGE := $(REGISTRY)/rawdata-operator:1.1

# Default target
.PHONY: all
all: build-worker build-watcher build-operator push-worker push-watcher push-operator

# Build targets
.PHONY: build-worker
build-worker:
	docker build -t $(WORKER_IMAGE) ./worker

.PHONY: build-watcher
build-watcher:
	docker build -t $(WATCHER_IMAGE) ./watcher

.PHONY: build-operator
build-operator:
	docker build -t $(OPERATOR_IMAGE) ./controller

# Push targets
.PHONY: push-worker
push-worker: build-worker
	docker push $(WORKER_IMAGE)

.PHONY: push-watcher
push-watcher: build-watcher
	docker push $(WATCHER_IMAGE)

.PHONY: push-operator
push-operator: build-operator
	docker push $(OPERATOR_IMAGE)


