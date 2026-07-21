#include "yd_ntb.h"

#define YD_NTB_MIN_IRQ  3
#define YD_NTB_MAX_IRQ  32 /*idb:2, 3, 4; ibmsg:1; pcie_cap:0 */
#define YD_NTB_PCIE_CAP_IRQ_OFFSET  0
#define YD_NTB_IBMSG_IRQ_OFFSET 1
#define YD_NTB_IDB1_IRQ_OFFSET  2
#define YD_NTB_IDB2_IRQ_OFFSET  3
#define YD_NTB_IDB3_IRQ_OFFSET  4


#include <linux/irqdomain.h>
static int yd_ntb_init_isr(struct yd_ntb_dev *yd_ndev)
{
    int nvecs;
    int tmp_irq;
    int ret;
  
    nvecs = pci_alloc_irq_vectors(yd_ndev->pdev, 1, YD_NTB_MAX_IRQ, PCI_IRQ_ALL_TYPES);
    if (nvecs < 1)
    {
        pci_err(yd_ndev->pdev, "[%s]: pci_alloc_irq_vectors failed\n", __func__);
        return nvecs;
    }

    tmp_irq = pci_irq_vector(yd_ndev->pdev, 0);
    if(tmp_irq < 0)
    {
        pci_err(yd_ndev->pdev, "[%s]: pci_irq_vector failed\n", __func__);
        ret = tmp_irq;
        goto error;
    }

    yd_ndev->ibmsg_irq = tmp_irq;
#ifdef MUL_DW_PACKET
    yd_ntb_msi_init(yd_ndev);
#endif
    return 0;
error:
    pci_free_irq_vectors(yd_ndev->pdev);
    return ret;
}

static int yd_ntb_device_add(struct pci_dev *pdev)
{
    struct yd_ntb_dev *yd_ndev = NULL;
   
    int ret;

    yd_ndev = pci_get_drvdata(pdev);
    if(!yd_ndev)
    {
        pci_err(pdev, "[%s]: pci_get_drvdata failed\n", __func__);
        return -1; 
    }
    
    if(yd_ld_init_lut(yd_ndev))
    {
        pci_err(pdev, "[%s]: yd_ld_init_lut failed\n", __func__);
        ret = -1;
        goto lut_init_error;
    }
    
    if(yd_ld_init_dir(yd_ndev))
    {
        pci_err(pdev, "[%s]: yd_ld_init_dir failed\n", __func__);
        ret = -2;
        goto dir_init_error;
    }

    if(yd_ntb_init_db_msg(yd_ndev))
    {
        pci_err(pdev, "[%s]: yd_ntb_init_db_msg failed\n", __func__);
        ret = -3;
        goto db_msg_error;
    }
    
    yd_common_set_global_ndev(yd_ndev);
    
    yd_topo_init_live_station();

    yd_ndev->station_id = yd_common_init_local_station_id();

    ntf_usp_res_init();
    return 0;
    
lut_init_error:
    yd_ld_exit_lut(yd_ndev);
dir_init_error:
    yd_ld_exit_dir(yd_ndev);
db_msg_error:
    yd_ntb_exit_db_msg(yd_ndev);
    
    return ret;
}

static int yd_ntb_device_del(struct pci_dev *pdev)
{
    struct yd_ntb_dev *yd_ndev = NULL;

    yd_ndev = pci_get_drvdata(pdev);
    if(!yd_ndev)
    {
        pci_err(pdev, "[%s]: pci_get_drvdata failed\n", __func__);
        return -1; 
    }

    yd_ld_exit_lut(yd_ndev);
   
    yd_ld_exit_dir(yd_ndev);
    
    yd_ntb_exit_db_msg(yd_ndev);
    
    yd_common_set_global_ndev(NULL);
    return 0;
}

#define YD_NTB_CONFIG_BAR_ID    0
#define YD_NTB_WIN1_BAR_ID  2
#define YD_NTB_WIN2_BAR_ID  3
#define YD_NTB_DEV_INIT_NAME    "SudoNtbEP"

static int yd_ntb_pci_probe(struct pci_dev *pdev,
                   const struct pci_device_id *id)
{
    int ret;
    struct yd_ntb_dev *yd_ndev  = NULL;
    struct device *dev          = NULL;
    unsigned long res_start, res_len;
    void __iomem *bar = 0;
    int mem_type;
    dev = &pdev->dev;
   
    dev->init_name = YD_NTB_DEV_INIT_NAME;
    yd_ndev = devm_kzalloc(dev, sizeof(struct yd_ntb_dev), GFP_KERNEL);
    if(!yd_ndev)
    {
        return -1;
    }

    ret = pcim_enable_device(pdev);
    if(ret)
    {
        return ret;
    }

//    ret = pci_set_dma_mask(pdev, DMA_BIT_MASK(64));   
//	if (ret)
//    {
//		ret = pci_set_dma_mask(pdev, DMA_BIT_MASK(32));  /*64位不行就再检查下32位*/
//        {
//		    if (ret)
//            {
//                pci_err(pdev, "[%s]: pci_set_dma_mask 32 and 64 failed\n", __func__);
//			    return ret;
//            }
//        }
//    }
    
//    ret = pci_set_consistent_dma_mask(pdev, DMA_BIT_MASK(64));
//    if (ret)
//    {  
//        ret = pci_set_consistent_dma_mask(pdev, DMA_BIT_MASK(32));
//        if(ret)
//        {
//            pci_err(pdev, "[%s]: pci_set_consistent_dma_mask 32 and 64 failed\n", __func__);
//            return ret;
//        }
//    }

    pci_set_master(pdev);

    res_start = pci_resource_start(pdev, YD_NTB_CONFIG_BAR_ID);
    res_len = pci_resource_len(pdev, YD_NTB_CONFIG_BAR_ID);
    if(!devm_request_mem_region(dev, res_start, res_len, KBUILD_MODNAME))
    {
        pci_err(pdev, "[%s]: devm_request_mem_region failed\n", __func__);
        return -1;
    }
    bar = (void *)ioremap(res_start, res_len);
    if(!bar)
    {
        pci_err(pdev, "[%s]: ioremap failed\n", __func__);
	    return -1;
    }
    yd_ndev->cfg = (struct yd_ntb_reg *)bar;
   
    mem_type = pci_resource_flags(pdev, YD_NTB_WIN1_BAR_ID) & PCI_BASE_ADDRESS_MEM_TYPE_MASK;
    switch (mem_type)
    {
    case PCI_BASE_ADDRESS_MEM_TYPE_32:
        pci_dbg(pdev, "[%s]: mem type is 32 failed\n", __func__);
        yd_ndev->mem_type = YD_ADDR_TYPE_32;
        break;
    case PCI_BASE_ADDRESS_MEM_TYPE_64:
        pci_dbg(pdev, "[%s]: mem type is 64 failed\n", __func__);
        yd_ndev->mem_type = YD_ADDR_TYPE_64;
        break;
    default:
        return -1;
    }

    /*bar2为必选开窗bar,bar3在64位下用*/
    yd_ndev->bar2 = pci_resource_start(pdev, YD_NTB_WIN1_BAR_ID);
    if(!yd_ndev->bar2)
    {
        pci_err(pdev, "[%s]: pci_resource_start win1 bar failed\n", __func__);
        return -1;
    }
    yd_ndev->bar2_total_size = pci_resource_len(pdev, YD_NTB_WIN1_BAR_ID);
    yd_ndev->bar2_residue_size = yd_ndev->bar2_total_size;
/*
    yd_ndev->bar3_total_size = pci_resource_len(pdev, YD_NTB_WIN2_BAR_ID);
    yd_ndev->bar3_residue_size = yd_ndev->bar3_total_size;
    */
    yd_ndev->pdev = pdev;
    ret = yd_ntb_init_isr(yd_ndev);
    if(ret)
    {
        pci_err(pdev, "[%s]: yd_ntb_init_isr failed\n", __func__);
        return ret;
    }
    
    pci_set_drvdata(pdev, yd_ndev);

    return yd_ntb_device_add(pdev);
}
#include <linux/delay.h>
static void yd_ntb_pci_remove(struct pci_dev *pdev)
{
   
    struct yd_ntb_dev *yd_ndev  = pci_get_drvdata(pdev);
    
    yd_ntb_device_del(pdev);

    iounmap((volatile void __iomem *)yd_ndev->cfg);
    
    pci_free_irq_vectors(pdev);

    pci_info(pdev, "yd ntb remove\n");

}

#define YD_NTB_HEADER_VENDOR_ID    0x205e
#define YD_NTB_HEADER_DEVICE_ID    0x0010





static const struct pci_device_id yd_ntb_ids[] = {
	{ YD_NTB_HEADER_VENDOR_ID, YD_NTB_HEADER_DEVICE_ID, PCI_ANY_ID, PCI_ANY_ID, 0, 0, 0 },
	{ 0, }
};

MODULE_DEVICE_TABLE(pci, yd_ntb_ids);

static struct pci_driver yd_ntb_pci_driver = {
    .name        = KBUILD_MODNAME,
    .id_table    = yd_ntb_ids,
    .probe        = yd_ntb_pci_probe,
    .remove        = yd_ntb_pci_remove,
    //.err_handler    = &yd_pci_err_handler,
};


module_pci_driver(yd_ntb_pci_driver);


MODULE_LICENSE("GPL");
