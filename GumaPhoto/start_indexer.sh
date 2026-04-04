#!/bin/bash
export LD_LIBRARY_PATH=/usr/local/lib/python3.11/dist-packages/nvidia/cudnn/lib:/usr/local/lib/python3.11/dist-packages/nvidia/cublas/lib:/usr/local/nvidia/lib:/usr/local/nvidia/lib64
python -u /app/Scripts/vector_indexer.py > /app/data/indexer_log.txt 2>&1
