#!/bin/bash

source .venv/bin/activate
source .env

sudo docker run -it --network=host --device=/dev/kfd --device=/dev/dri --group-add=video --ipc=host --cap-add=SYS_PTRACE --security-opt seccomp=unconfined --shm-size 8G -v ./:/src -w /src rocm/pytorch
