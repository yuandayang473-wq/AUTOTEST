TARGET = yddma_test
obj-m := $(TARGET).o
DIR :=  $(shell uname -r)
$(TARGET)-objs = dma_test.o
KERNEL := /lib/modules/$(DIR)/build
PWD :=$(shell pwd)
modules :
	$(MAKE) -C $(KERNEL) M=$(PWD) modules
.PHONEY:clean
clean :  
	rm -f *.o *.ko  