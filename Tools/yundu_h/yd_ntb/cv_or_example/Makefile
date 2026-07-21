TARGET = sudo_test
obj-m := $(TARGET).o


DIR :=  $(shell uname -r)
$(TARGET)-objs = test.o
KERNEL := /lib/modules/$(DIR)/build
PWD :=$(shell pwd)
KBUILD_EXTRA_SYMBOLS += $(PWD)/../Module.symvers
modules :
	$(MAKE) -C $(KERNEL) M=$(PWD) modules
.PHONEY:clean
clean :  
	rm -f *.o *.ko  
