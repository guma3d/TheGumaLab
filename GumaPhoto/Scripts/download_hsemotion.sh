#!/bin/bash
mkdir -p /root/.hsemotion
curl -L -A "Mozilla/5.0" "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b0_8_best_vgaf.pt" -o "/root/.hsemotion/enet_b0_8_best_vgaf.pt"
ls -la /root/.hsemotion
