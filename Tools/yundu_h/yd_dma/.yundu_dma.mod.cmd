savedcmd_/root/yd_dma/yundu_dma.mod := printf '%s\n'   yd_dma.o | awk '!x[$$0]++ { print("/root/yd_dma/"$$0) }' > /root/yd_dma/yundu_dma.mod
