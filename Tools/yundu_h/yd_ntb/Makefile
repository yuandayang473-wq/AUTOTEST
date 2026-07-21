TARGET = sudo_ntb
obj-m := $(TARGET).o
DIR :=  $(shell uname -r)
$(TARGET)-objs = yd_ntb_common.o \
			yd_ntb_db_msg.o \
			yd_ntb_lut_dir.o \
			yd_reqid.o \
			yd_ntb.o \
			yd_ntb_api.o \
			yd_ntb_msi.o \
			yd_ntb_ntf.o 
KERNEL := /lib/modules/$(DIR)/build
PWD :=$(shell pwd)
modules :
	$(MAKE) -C $(KERNEL) M=$(PWD) modules
.PHONEY:clean
clean :  
	rm -f *.o *.ko  