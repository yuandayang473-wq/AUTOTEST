TARGET = hr_test
obj-m := $(TARGET).o
DIR :=  $(shell uname -r)
$(TARGET)-objs = hot_reset.o
KERNEL := /lib/modules/$(DIR)/build
PWD :=$(shell pwd)
modules :
	$(MAKE) -C $(KERNEL) M=$(PWD) modules
.PHONEY:clean
clean :  
	rm -f *.o *.ko  