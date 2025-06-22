# Docker config
IMAGE_NAME = mongodb-keda-worker
TAG = latest
DOCKER_USERNAME = adiganesh2004
FULL_IMAGE_NAME = $(DOCKER_USERNAME)/$(IMAGE_NAME):$(TAG)
DOCKERFILE_PATH = app/Dockerfile
CONTEXT = app

.PHONY: build push

build:
	docker build -f $(DOCKERFILE_PATH) -t $(FULL_IMAGE_NAME) $(CONTEXT)

push: build
	docker push $(FULL_IMAGE_NAME)
