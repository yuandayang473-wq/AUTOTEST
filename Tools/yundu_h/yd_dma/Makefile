TARGET = yundu_dma
obj-m := $(TARGET).o
DIR :=  $(shell uname -r)
$(TARGET)-objs = yd_dma.o
KERNEL := /lib/modules/$(DIR)/build
PWD :=$(shell pwd)
modules :
	$(MAKE) -C $(KERNEL) M=$(PWD) modules
.PHONEY:clean
clean :  
	rm -f *.o *.ko  