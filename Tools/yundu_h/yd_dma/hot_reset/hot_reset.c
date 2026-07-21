
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/dmaengine.h>
#include <linux/platform_device.h>

#include <linux/completion.h>
#include <linux/dma-mapping.h>

#include <linux/pci.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/timer.h>
#include <asm/delay.h>
#include <linux/dmaengine.h>
MODULE_LICENSE("GPL");

#include <linux/delay.h>

void yd_pci_reset_secondary_bus(struct pci_dev *dev)
{
	u16 ctrl;

	pci_read_config_word(dev, PCI_BRIDGE_CONTROL, &ctrl);
	ctrl |= PCI_BRIDGE_CTL_BUS_RESET;
	pci_write_config_word(dev, PCI_BRIDGE_CONTROL, ctrl);

	/*
	 * PCI spec v3.0 7.6.4.2 requires minimum Trst of 1ms.  Double
	 * this to 2ms to ensure that we meet the minimum requirement.
	 */
	msleep(2);

	ctrl &= ~PCI_BRIDGE_CTL_BUS_RESET;
	pci_write_config_word(dev, PCI_BRIDGE_CONTROL, ctrl);

	/*
	 * Trhfa for conventional PCI is 2^25 clock cycles.
	 * Assuming a minimum 33MHz clock this results in a 1s
	 * delay before we can consider subordinate devices to
	 * be re-initialized.  PCIe has some ways to shorten this,
	 * but we don't make use of them yet.
	 */
	ssleep(1);
}


#define YD_DMA_DEVICE_VENDOR	0x1357
#define YD_DMA_DEVICE1_ID		0x1234//DMA-EP0
#define YD_DMA_DEVICE2_ID		0x1336	//DMA-EP1


static struct pci_dev *ntb_cv_get_dma_dsp_dev(void)
{
    struct pci_dev *dev = NULL;
    dev = pci_get_device(YD_DMA_DEVICE_VENDOR, YD_DMA_DEVICE1_ID, dev);
    return dev;
}


static int hot_reset_init(void)
{

	struct pci_dev *pdev = NULL;
	pdev = ntb_cv_get_dma_dsp_dev();
	if(!pdev)
	{
		printk("get dma dsp pdev failed\n");
		return -1;
	}

    	yd_pci_reset_secondary_bus(pdev);
	return 0;
}

static void hot_reset_exit(void)
{
	return;
}
module_init(hot_reset_init);
module_exit(hot_reset_exit);
