
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


#define DMA_CV_MAX_CHAN_CNT 8



struct yd_dma_chan_desc{
	const char *name;
};

enum yd_dma_tran_type{
    YD_DMA_MEM_TO_MEM = 1,
    YD_DMA_MEM_TO_DEV,      /*0x404*/
    YD_DMA_DEV_TO_MEM,      /*0x40c*/
    YD_DMA_DEV_TO_DEV,      /*0x414 0x41c*/
};

struct cv_cb_info{
    struct device *dev;
    struct dma_chan *dchan;
    dma_cookie_t cookie;
    struct completion comp;
    int run_cnt;
    enum yd_dma_tran_type type;
    char *s_ptr;
    char *d_ptr;
    size_t len;
    dma_addr_t src;
    dma_addr_t dst;
    char chan_name[32];
    unsigned long res_start;
    void __iomem *bar;
};

static int yd_dma_cv_release_resource(enum yd_dma_tran_type type, struct cv_cb_info *cb_info);
static struct  cv_cb_info *yd_dma_one_chan_gen(struct device *dev, enum yd_dma_tran_type type, unsigned long res_start, void __iomem *bar, const char *chan_name, struct cv_cb_info *cb_info, int run_cnt, uint32_t asign_len);

static const struct yd_dma_chan_desc chan_desc[] = {
	{.name = "tx"},
	{.name = "rx"},
	{.name = "test1"},
	{.name = "test2"},
	{.name = "test3"},
	{.name = "test4"},
	{.name = "test5"},
	{.name = "test6"},
};
#include <linux/delay.h>



void yd_pci_reset_secondary_bus(struct pci_dev *dev)
{
	u16 ctrl;

	pci_read_config_word(dev, PCI_BRIDGE_CONTROL, &ctrl);
	ctrl |= PCI_BRIDGE_CTL_BUS_RESET;
	pci_write_config_word(dev, PCI_BRIDGE_CONTROL, ctrl);


	msleep(2);

	ctrl &= ~PCI_BRIDGE_CTL_BUS_RESET;
	pci_write_config_word(dev, PCI_BRIDGE_CONTROL, ctrl);

	ssleep(1);
}


#define YD_DMA_DSP_DEVICE_VENDOR	0x1357
#define YD_DMA_DSP_DEVICE1_ID		0x1234//DMA-EP0


static struct pci_dev *yd_dma_get_dma_dsp_dev(void)
{
    struct pci_dev *dev = NULL;
    dev = pci_get_device(YD_DMA_DSP_DEVICE_VENDOR, YD_DMA_DSP_DEVICE1_ID, dev);
    return dev;
}


static int yd_dma_hot_reset_deal(void)
{

	struct pci_dev *pdev = NULL;
	pdev = yd_dma_get_dma_dsp_dev();
	if(!pdev)
	{
		printk("get dma dsp pdev failed\n");
		return -1;
	}

    yd_pci_reset_secondary_bus(pdev);
	return 0;
}


#define DMA_TEST_DEV_NAME   "SudoNtbEP"
struct completion g_comp;
static int g_over_cnt = 0;

static void dma_complete_callback(void *data)
{
    struct cv_cb_info *cb_info = NULL;

    struct dma_chan *dchan = NULL;
    struct dma_tx_state state;
    enum dma_status dstatus;
    uint32_t val;
    printk("[%s]: %d: enter \n", __func__, __LINE__);
    if(data)
    {


        cb_info = (struct cv_cb_info *)data;

        printk("[%s]: %d: enter \n", __func__, __LINE__);

        dchan = cb_info->dchan;
        dstatus = dmaengine_tx_status(dchan, cb_info->cookie, &state);
        printk("[%s]: %d: dstatus = %d, residue = %d", __func__, __LINE__, dstatus, state.residue);

        if(!cb_info->type)
        {
            goto final;
        }
        switch(cb_info->type)
        {
            case YD_DMA_MEM_TO_MEM:
                printk("[%s]: YD_DMA_MEM_TO_MEM strncmp = %d\n", __func__, strncmp(cb_info->s_ptr, cb_info->d_ptr, cb_info->len));
            break;
        case YD_DMA_MEM_TO_DEV:
                val = readl(cb_info->bar + 0x724);
                if(val == *(uint32_t *)(cb_info->s_ptr))
                {
                    printk("[%s]: YD_DMA_MEM_TO_DEV strncmp = %d\n", __func__, 0);
                }
                else{
                    printk("[%s]: YD_DMA_MEM_TO_DEV strncmp = %d\n", __func__, -1);
                }

            break;
        case YD_DMA_DEV_TO_MEM:
                val = readl(cb_info->bar + 0x720);
                if(val == *(uint32_t *)(cb_info->d_ptr))
                {
                    printk("[%s]: YD_DMA_DEV_TO_MEM strncmp = %d\n", __func__, 0);
                }
                else{
                    printk("[%s]: YD_DMA_DEV_TO_MEM strncmp = %d\n", __func__, -1);
                }
            break;
        case YD_DMA_DEV_TO_DEV:
                if(readl(cb_info->bar + 0x728) == readl(cb_info->bar + 0x72c))
                {
                    printk("[%s]: YD_DMA_DEV_TO_DEV strncmp = %d\n", __func__, 0);
                }
                else{
                    printk("[%s]: YD_DMA_DEV_TO_DEV strncmp = %d\n", __func__, -1);
                }
        }
        cb_info->run_cnt--;
        g_over_cnt--;
        printk("[%s]: %d: g_over_cnt cnt = %d\n", __func__, __LINE__, g_over_cnt);

       /*
        cb_info->run_cnt--;
        printk("[%s]: %d: run cnt = %d\n", __func__, __LINE__, cb_info->run_cnt);
        yd_dma_cv_release_resource(cb_info->type, cb_info);
        if(cb_info->run_cnt)
        {
            cb_info = yd_dma_one_chan_gen(cb_info->dev, cb_info->type, cb_info->res_start, cb_info->bar, cb_info->chan_name, cb_info, cb_info->run_cnt);
            if(cb_info == NULL)
            {
                printk("[%s]: %d: yd_dma_one_chan_gen null\n", __func__, __LINE__);
                return;
            }
            printk("[%s]: %d: chan name = %s pending\n", __func__, __LINE__, cb_info->chan_name);
            dma_async_issue_pending(cb_info->dchan);
        }
        else{
            g_over_cnt--;
            printk("[%s]: %d: g_over_cnt cnt = %d\n", __func__, __LINE__, g_over_cnt);
            vfree(cb_info);
        }
        */
    }
final:
    if(g_over_cnt == 0)
    {
        printk("[%s]: %d: enter \n", __func__, __LINE__);
        complete(&g_comp);
    }


}

static int gen_test(struct pci_dev *pdev)
{
    int ret;
    printk("[%s]: %d: enter\n", __func__, __LINE__);
	ret = pcim_enable_device(pdev);
	if (ret)
		return ret;


	printk("[%s]: %d: enter\n", __func__, __LINE__);
	ret = pci_set_dma_mask(pdev, DMA_BIT_MASK(64));
	if (ret)
		ret = pci_set_dma_mask(pdev, DMA_BIT_MASK(32));  /*64位不行就再检查下32位*/
	if (ret)
		return ret;

	printk("[%s]: %d: enter\n", __func__, __LINE__);
	ret = pci_set_consistent_dma_mask(pdev, DMA_BIT_MASK(64));
	if (ret)
		ret = pci_set_consistent_dma_mask(pdev, DMA_BIT_MASK(32));
	if (ret)
		return ret;
	printk("[%s]: %d: enter\n", __func__, __LINE__);
	pci_set_master(pdev);
    return 0;
}



static int yd_dma_cv_alloc_coherent(struct device *dev, size_t size, dma_addr_t *dma_addr, char **mem_addr)
{
    printk("[%s]: %d: enter\n", __func__, __LINE__);
    *mem_addr = dma_alloc_coherent(dev, size, dma_addr,
					      GFP_KERNEL);

    printk("[%s]: %d: mem -add r = %llx\n", __func__, __LINE__, (unsigned long long)*mem_addr);
    if(*mem_addr)
    {
        return 0;
    }
    printk("[%s]: %d: enter\n", __func__, __LINE__);
    return -1;
}

static void yd_dma_cv_free_coherent(struct device *dev, size_t size, dma_addr_t dma_addr, char *mem_addr)
{
    printk("[%s]: %d: enter\n", __func__, __LINE__);
    dma_free_coherent(dev, size, mem_addr, dma_addr);
    printk("[%s]: %d: enter\n", __func__, __LINE__);

}

static void *yd_dma_cv_map_single(struct device *dev, size_t size, dma_addr_t *dma_handle, enum dma_data_direction dir)
{
    void *buffer = kmalloc(size, GFP_KERNEL);
    if(!buffer)
    {
        printk("[%s]: %d: kmalloc error\n", __func__, __LINE__);
        return NULL;
    }
    *dma_handle = dma_map_single(dev, buffer, size, dir);
    if (dma_mapping_error(dev, *dma_handle)) {
        printk("[%s]: %d: mapping error\n", __func__, __LINE__);
		kfree(buffer);
		return NULL;
	}
    return buffer;

}

static void yd_dma_cv_free_map_single(struct device *dev, size_t size, void *buffer, dma_addr_t dma_handle)
{
    dma_unmap_single(dev, dma_handle, size, DMA_FROM_DEVICE);
	kfree(buffer);
}
#define YD_DMA_ALLOC_COR 1
static void yd_dma_cv_gen_free(struct device *dev, size_t size, void *buffer, dma_addr_t dma_handle)
{
#ifdef YD_DMA_ALLOC_COR
    yd_dma_cv_free_coherent(dev, size, dma_handle, buffer);
#else
    yd_dma_cv_free_map_single(dev, size, buffer, dma_handle);
#endif
}

static int yd_dma_cv_common(struct device *dev, char *name, dma_addr_t src, dma_addr_t dst, size_t len, int max_burst)
{
    struct dma_slave_config config;
    struct dma_async_tx_descriptor *tx = NULL;
    dma_cookie_t cookie;
    long timeout = 55000;
    struct dma_chan *dchan = NULL;
    int ret = 0;
    struct dma_tx_state state;
    enum dma_status dstatus;
    dchan = dma_request_chan(dev, name);
    if(!dchan)
    {
        printk("[%s]: dma_request_chan failed\n", __func__);
        ret = -1;
        return ret;
    }

    memset(&config, 0, sizeof(struct dma_slave_config));
    if(max_burst)
    {
        printk("[%s]: %d: max_burst has num = %d\n", __func__, __LINE__, max_burst);
        config.src_maxburst = max_burst;
        printk("[%s]: %d: start dmaengine_slave_config\n", __func__, __LINE__);
        ret = dmaengine_slave_config(dchan, &config);
        if(ret)
        {
            printk("[%s]: dmaengine_slave_config failed\n", __func__);
            ret = -1;
            goto chan_err;
        }
    }

    printk("[%s]: %d: start dmaengine_prep_dma_memcpy, dst = 0x%llx, src = 0x%llx\n", __func__, __LINE__, dst, src);
    tx = dmaengine_prep_dma_memcpy(dchan, dst, src, len, 0);
    if(!tx)
    {
        printk("[%s]: dmaengine_prep_dma_memcpy failed\n", __func__);
        ret = -1;
        goto chan_err;
    }

    tx->callback = dma_complete_callback;
    cookie = dmaengine_submit(tx);

    printk("[%s]: %d: start dma_async_issue_pending\n", __func__, __LINE__);
    dma_async_issue_pending(dchan);
    int w_cnt = 0;
wait_comp:
    printk("[%s]: %d: start wait_for_completion_timeout\n", __func__, __LINE__);
    if(!wait_for_completion_timeout(&g_comp, msecs_to_jiffies(timeout))) {
        printk("[%s]: wait_for_completion_timeout timeout\n", __func__);
	w_cnt++;
        ret = -1;
    }
    dstatus = dmaengine_tx_status(dchan, cookie, &state);
    printk("[%s]: %d: the residue = %d\n", __func__, __LINE__, state.residue);
    if(state.residue)
    {

 	if(w_cnt < 3)
        	goto wait_comp;
    }
chan_err:
    dma_release_channel(dchan);
    return ret;
}
static int yd_dma_cv_testcase_04(struct device *dev)  //配置一个dma通道的传输（memcpy)，看传输后是否内容真正被拷贝过去  mem-to-mem
{

    char *s_ptr = NULL, *d_ptr = NULL;
    unsigned long s_phys, d_phys;
    int ret = -1;

    s_ptr = kmalloc(4, GFP_KERNEL);
    if(!s_ptr)
    {
        printk("[%s]: s_ptr = null\n", __func__);
        return -1;
    }
    s_phys = virt_to_phys(s_ptr);

    d_ptr = kmalloc(4, GFP_KERNEL);
    if(!d_ptr)
    {
        kfree(s_ptr);
        printk("[%s]: d_ptr = null\n", __func__);
        return -1;
    }
    d_phys = virt_to_phys(d_ptr);

    memset(d_ptr, 0, 4);
    strcpy(s_ptr, "chen");
    g_over_cnt = 0;
    if(!yd_dma_cv_common(dev, "tx", s_phys, d_phys, 4, 0))
    {
        printk("[%s]: %d: s ptr = %s, d ptr = %s\n", __func__, __LINE__, s_ptr, d_ptr);
        ret = 0;
    }
     printk("[%s]: %d: s ptr = %s, d ptr = %s\n", __func__, __LINE__, s_ptr, d_ptr);
    kfree(s_ptr);
    kfree(d_ptr);
    return ret;
}

static int yd_dma_cv_testcase_05(struct device *dev, unsigned long src, unsigned long dst, void __iomem *bar)  //配置一个dma通道的传输（memcpy)，看传输后是否内容真正被拷贝过去 dev-to-dev
{


    int ret = -1;
    g_over_cnt = 0;
    if(!yd_dma_cv_common(dev, "rx", src, dst, 4, 0))
    {
        printk("[%s]: %d: src = %u, dst = %u\n", __func__, __LINE__, readl(bar + 0x120), readl(bar + 0x128));
        ret = 0;
    }
    return ret;
}

static int yd_dma_cv_testcase_06(struct device *dev, unsigned long src, void __iomem *bar)  //配置一个dma通道的传输（memcpy)，看传输后是否内容真正被拷贝过去 dev-to-mem
{
    char *d_ptr = NULL;
    unsigned long d_phys;
    int ret = -1;

   

    d_ptr = kmalloc(4, GFP_KERNEL);
    if(!d_ptr)
    {
        printk("[%s]: d_ptr = null\n", __func__);
        return -1;
    }
    d_phys = virt_to_phys(d_ptr);

    memset(d_ptr, 0, 4);
    g_over_cnt = 0;
    if(!yd_dma_cv_common(dev, "rx", src, d_phys, 4, 0))
    {
        printk("[%s]: %d: src = %u, dst = %u\n", __func__, __LINE__, readl(bar + 0x320), *(uint32_t *)d_ptr);
        ret = 0;
    }

    kfree(d_ptr);
    return ret;
}

static int yd_dma_cv_testcase_07(struct device *dev, unsigned long dst, void __iomem *bar)  //配置一个dma通道的传输（memcpy)，看传输后是否内容真正被拷贝过去 mem-to-dev
{


    int ret = -1;

    char *s_ptr = NULL;
    unsigned long s_phys;

    s_ptr = kmalloc(4, GFP_KERNEL);
    if(!s_ptr)
    {
        printk("[%s]: s_ptr = null\n", __func__);
        return -1;
    }
    s_phys = virt_to_phys(s_ptr);

    memset(s_ptr, 0, 4);
    memcpy(s_ptr, "chen", 4);
    g_over_cnt = 0;
    if(!yd_dma_cv_common(dev, "rx", s_phys, dst, 4, 0))
    {
        printk("[%s]: %d: src = %u, dst = %u\n", __func__, __LINE__, *(uint32_t *)s_ptr, readl(bar + 0x520));
        ret = 0;
    }
    kfree(s_ptr);
    return ret;
}

static int yd_dma_cv_testcase_08(struct device *dev)  //pause and resume
{
    char *s_ptr = NULL, *d_ptr = NULL;
    dma_addr_t d_phys_addr = 0, s_phys_addr = 0, dst, src;
    int ret = -1;
    uint32_t i;

    struct dma_slave_config config;
    struct dma_async_tx_descriptor *tx = NULL;
    dma_cookie_t cookie;
    long timeout = 5000;
    struct dma_chan *dchan = NULL;
    struct dma_tx_state state;
    enum dma_status dstatus;

    struct cv_cb_info *cb_info = NULL;



    if(yd_dma_cv_alloc_coherent(dev, 512, &d_phys_addr, &d_ptr))
    {
        printk("[%s]: %d: yd_dma_cv_alloc_coherent failed\n", __func__, __LINE__);
        return -1;
    }

    if(yd_dma_cv_alloc_coherent(dev, 512, &s_phys_addr, &s_ptr))
    {
        yd_dma_cv_free_coherent(dev, 512, d_phys_addr, d_ptr);
        printk("[%s]: %d: yd_dma_cv_alloc_coherent failed\n", __func__, __LINE__);
        return -1;
    }




    memset(d_ptr, 0, 512);

    for(i = 0; i < 512; i++)
    {
        s_ptr[i] = i % 10;
    }


    dchan = dma_request_chan(dev, "tx");
    if(!dchan)
    {
        printk("[%s]: dma_request_chan failed\n", __func__);
        ret = -1;
        goto malloc_err;
    }

    memset(&config, 0, sizeof(struct dma_slave_config));

    config.src_maxburst = 64;
    printk("[%s]: %d: start dmaengine_slave_config\n", __func__, __LINE__);
    ret = dmaengine_slave_config(dchan, &config);
    if(ret)
    {
        printk("[%s]: dmaengine_slave_config failed\n", __func__);
        ret = 0;
        goto chan_err;
    }

    tx = dmaengine_prep_dma_memcpy(dchan, d_phys_addr, s_phys_addr, 512, 0);
    if(!tx)
    {
        printk("[%s]: dmaengine_prep_dma_memcpy failed\n", __func__);
        ret = -1;
        goto chan_err;
    }

    tx->callback = dma_complete_callback;
    cookie = dmaengine_submit(tx);




    //tx->callback_param = cb_info;
    g_over_cnt = 0;
    printk("[%s]: %d: start dma_async_issue_pending\n", __func__, __LINE__);
    dma_async_issue_pending(dchan);

    //usleep(100);
    //dmaengine_pause(dchan);
    printk("[%s]: %d: start wait_for_completion_timeout\n", __func__, __LINE__);
    if(!wait_for_completion_timeout(&g_comp, msecs_to_jiffies(timeout))) {
        printk("[%s]: wait_for_completion_timeout timeout\n", __func__);
        ret = -1;
    }
    dstatus = dmaengine_tx_status(dchan, cookie, &state);
    printk("[%s]: %d: no pause dstatus = %d, residue = %d", __func__, __LINE__, dstatus, state.residue);


    dmaengine_pause(dchan);
    printk("[%s]: %d: start wait_for_completion_timeout\n", __func__, __LINE__);
    if(!wait_for_completion_timeout(&g_comp, msecs_to_jiffies(timeout))) {
        printk("[%s]: wait_for_completion_timeout timeout\n", __func__);
        ret = -1;
    }
    dstatus = dmaengine_tx_status(dchan, cookie, &state);
    printk("[%s]: %d: start pause dstatus = %d, residue = %d", __func__, __LINE__, dstatus, state.residue);

    printk("[%s]: %d: start resume\n", __func__, __LINE__);
    dmaengine_resume(dchan);
    if(!wait_for_completion_timeout(&g_comp, msecs_to_jiffies(timeout))) {
        printk("[%s]: wait_for_completion_timeout timeout\n", __func__);
        ret = -1;
    }

    ssleep(5);
malloc_err:
    yd_dma_cv_free_coherent(dev, 512, d_phys_addr, d_ptr);
    yd_dma_cv_free_coherent(dev, 512, s_phys_addr, s_ptr);
chan_err:
    dma_release_channel(dchan);
    return ret;

}

static int yd_dma_cv_testcase_09(struct device *dev)  //terminate_all ,附带测试salve config长度，多中断的处理方式
{
    char *s_ptr = NULL, *d_ptr = NULL;
    unsigned long s_phys, d_phys;
    int ret = -1;

    struct dma_slave_config config;
    struct dma_async_tx_descriptor *tx = NULL;
    dma_cookie_t cookie;
    long timeout = 5000;
    struct dma_chan *dchan = NULL;
    struct cv_cb_info *cb_info = NULL;

    s_ptr = kmalloc(512, GFP_KERNEL);
    if(!s_ptr)
    {
        printk("[%s]: s_ptr = null\n", __func__);
        return -1;
    }
    s_phys = virt_to_phys(s_ptr);

    d_ptr = kmalloc(512, GFP_KERNEL);
    if(!d_ptr)
    {
        kfree(s_ptr);
        printk("[%s]: d_ptr = null\n", __func__);
        return -1;
    }
    d_phys = virt_to_phys(d_ptr);

    memset(d_ptr, 0, 512);




    dchan = dma_request_chan(dev, "tx");
    if(!dchan)
    {
        printk("[%s]: dma_request_chan failed\n", __func__);
        ret = -1;
        goto malloc_err;
    }

    memset(&config, 0, sizeof(struct dma_slave_config));

    config.src_maxburst = 64;
    printk("[%s]: %d: start dmaengine_slave_config\n", __func__, __LINE__);
    ret = dmaengine_slave_config(dchan, &config);
    if(ret)
    {
        printk("[%s]: dmaengine_slave_config failed\n", __func__);
        ret = -1;
        goto chan_err;
    }
    printk("[%s]: %d: start dmaengine_prep_dma_memcpy\n", __func__, __LINE__);
    tx = dmaengine_prep_dma_memcpy(dchan, d_phys, s_phys, 512, 0);
    if(!tx)
    {
        printk("[%s]: dmaengine_prep_dma_memcpy failed\n", __func__);
        ret = -1;
        goto chan_err;
    }
    g_over_cnt = 0;
    tx->callback = dma_complete_callback;
    cookie = dmaengine_submit(tx);

    printk("[%s]: %d: start dma_async_issue_pending\n", __func__, __LINE__);

    dma_async_issue_pending(dchan);

    //dmaengine_terminate_all(dchan);

    printk("[%s]: %d: start wait_for_completion_timeout\n", __func__, __LINE__);
    if(!wait_for_completion_timeout(&g_comp, msecs_to_jiffies(timeout))) {
        printk("[%s]: wait_for_completion_timeout timeout\n", __func__);
        ret = 0;
    }

    printk("[%s]: %d: start terminate\n", __func__, __LINE__);
    dmaengine_terminate_all(dchan);

    printk("[%s]: %d: start wait_for_completion_timeout\n", __func__, __LINE__);
    if(!wait_for_completion_timeout(&g_comp, msecs_to_jiffies(timeout))) {
        printk("[%s]: wait_for_completion_timeout timeout\n", __func__);
        ret = 0;
    }
    printk("[%s]: %d: end terminate\n", __func__, __LINE__);
    //vfree(cb_info);
malloc_err:
    kfree(s_ptr);
    kfree(d_ptr);
chan_err:
    dma_release_channel(dchan);
    return ret;

}


static int yd_dma_cv_testcase_12(struct device *dev)
{
    dma_addr_t s_dma_addr = 0, d_dma_addr = 0;
    char *s_mem_addr, *d_mem_addr;
    uint8_t i;
    int ret = 0;
    size_t len[] = {4, 8, 16, 32, 64, 128, 256, 512, 1024, 1024 * 1024, 1024 * 1024 *4};
    //size_t len[] = {2048};
    for(i = 0; i < sizeof(len)/sizeof(size_t); i++)
    {

        printk("[%s]: %d: i = %d\n", __func__, __LINE__, i);
        ret = yd_dma_cv_alloc_coherent(dev, len[i], &s_dma_addr, &s_mem_addr);
        if(ret)
        {
            printk("[%s]: %d: size = %lu, yd_dma_cv_alloc_coherent src failed\n", __func__, __LINE__, len[i]);
            return ret;
        }

        ret = yd_dma_cv_alloc_coherent(dev, len[i], &d_dma_addr, &d_mem_addr);
        if(ret)
        {
            printk("[%s]: %d: size = %lu, yd_dma_cv_alloc_coherent dst failed\n", __func__, __LINE__, len[i]);
            yd_dma_cv_gen_free(dev, len[i], s_mem_addr, s_dma_addr);
            return ret;
        }
        printk("[%s]: %d:src mem = %p, dst mem = %p\n", __func__, __LINE__, s_mem_addr, d_mem_addr);
        strcpy(s_mem_addr, "chen");
        /*
        memset(s_mem_addr, 0, len[i]);
        for(i = 0; i< len[i];i++)
        {
            s_mem_addr[i] = i % 10;
        }
        */
        printk("[%s]: %d: enter\n", __func__, __LINE__);
        g_over_cnt = 0;
        ret = yd_dma_cv_common(dev, "rx", s_dma_addr, d_dma_addr, len[i], 0);

        printk("[%s]: %d: yd_dma_cv_common ret = %d, s addr = %s, d addr = %s, strncmp = %d", __func__, __LINE__, ret, s_mem_addr, d_mem_addr, strncmp(s_mem_addr, d_mem_addr, len[i]));
        yd_dma_cv_gen_free(dev, len[i], d_mem_addr, d_dma_addr);
        yd_dma_cv_gen_free(dev, len[i], s_mem_addr, s_dma_addr);
    }
    return 0;
}

static int yd_dma_cv_release_resource(enum yd_dma_tran_type type, struct cv_cb_info *cb_info)
{
    switch(type)
    {
        case YD_DMA_MEM_TO_MEM:
            yd_dma_cv_free_coherent(cb_info->dev, cb_info->len, cb_info->src, cb_info->s_ptr);
            yd_dma_cv_free_coherent(cb_info->dev, cb_info->len, cb_info->dst, cb_info->d_ptr);
            break;
        case YD_DMA_MEM_TO_DEV:
            yd_dma_cv_free_coherent(cb_info->dev, cb_info->len, cb_info->src, cb_info->s_ptr);
            break;
        case YD_DMA_DEV_TO_MEM:
            yd_dma_cv_free_coherent(cb_info->dev, cb_info->len, cb_info->dst, cb_info->d_ptr);
            break;
        default:
            return -1;
    }
    return 0;
}

static struct  cv_cb_info *yd_dma_one_chan_gen(struct device *dev, enum yd_dma_tran_type type, unsigned long res_start, void __iomem *bar, const char *chan_name, struct cv_cb_info *cb_info, int run_cnt, uint32_t asign_len)
{
    struct dma_async_tx_descriptor *tx;
    dma_cookie_t cookie;
    struct dma_chan *dchan;
    uint8_t i;

    uint32_t len = 1024*32;
    dma_addr_t d_phys_addr = 0, s_phys_addr = 0, dst, src;
    char *s_ptr = NULL, tmp_sptr;
    char *d_ptr = NULL;
    char msg[] = "chenhaochenhaochenhaochenhao";
    if(!cb_info)
    {
        printk("[%s]: %d: enter cb_info == NULL\n", __func__, __LINE__);
        cb_info = vmalloc(sizeof(struct cv_cb_info));
        if(!cb_info)
        {
            printk("[%s]: %d: cb info == null\n", __func__, __LINE__);
            return NULL;
        }
        memset(cb_info, 0, sizeof(struct cv_cb_info));
        strcpy(cb_info->chan_name, chan_name);
    }
    if(asign_len)
    {
        len = asign_len;
    }
    switch(type)
    {
        case YD_DMA_MEM_TO_MEM:
            if(yd_dma_cv_alloc_coherent(dev, len, &d_phys_addr, &d_ptr))
            {
                printk("[%s]: %d: yd_dma_cv_alloc_coherent failed\n", __func__, __LINE__);
                vfree(cb_info);
                return NULL;
            }

            if(yd_dma_cv_alloc_coherent(dev, len, &s_phys_addr, &s_ptr))
            {
                printk("[%s]: %d: yd_dma_cv_alloc_coherent failed\n", __func__, __LINE__);
                yd_dma_cv_free_coherent(dev, len, d_phys_addr, d_ptr);
                vfree(cb_info);
                return NULL;
            }
            printk("[%s]: %d: alloc ok, s_ptr = %p d_ptr = %p\n", __func__, __LINE__, s_ptr, d_ptr);
            //memset(s_ptr, 0, len);
            if(!s_ptr || !d_ptr)
            {
                printk("[%s]: %d: !s_ptr || !d_ptr\n", __func__, __LINE__);
                return -1;
            }


            printk("[%s]: %d: enter\n", __func__, __LINE__);

            strcpy(s_ptr, "chenahfaihgaishgajgjaigjaigajgiajgaijg");
            /*
            for(i = 0; i< len;i++)
            {
                //printk("[%s]: %d: enter\n", __func__, __LINE__);
                s_ptr[i] = i % 10;
            }
            */
            printk("[%s]: %d: enter\n", __func__, __LINE__);
            dst = d_phys_addr;
            src = s_phys_addr;
            printk("[%s]: %d: enter\n", __func__, __LINE__);
            break;
        case YD_DMA_MEM_TO_DEV:

            len = 4;
            if(yd_dma_cv_alloc_coherent(dev, len, &s_phys_addr, &s_ptr))
            {
                printk("[%s]: %d: yd_dma_cv_alloc_coherent failed\n", __func__, __LINE__);
                vfree(cb_info);
                return NULL;
            }
            printk("[%s]: %d: enter\n", __func__, __LINE__);
            *(uint32_t *)s_ptr = 0x12345678;
            printk("[%s]: %d: enter\n", __func__, __LINE__);
            src = s_phys_addr;
            dst = res_start + 0x724;

            break;
        case YD_DMA_DEV_TO_MEM:
            len = 4;
            if(yd_dma_cv_alloc_coherent(dev, len, &d_phys_addr, &d_ptr))
            {
                printk("[%s]: %d: yd_dma_cv_alloc_coherent failed\n", __func__, __LINE__);
                vfree(cb_info);
                return NULL;
            }
            printk("[%s]: %d: enter\n", __func__, __LINE__);
            writel(0x87654321, bar + 0x720);
            printk("[%s]: %d: enter\n", __func__, __LINE__);
            dst = d_phys_addr;
            src = res_start + 0x720;

            break;
        case YD_DMA_DEV_TO_DEV:
            writel(0x11224455, bar + 0x728);
            printk("[%s]: %d: enter\n", __func__, __LINE__);
            src = res_start + 0x728;
            dst = res_start + 0x72c;
            len = 4;
            break;
        default:
            return NULL;
    }
    printk("[%s]: %d: enter\n", __func__, __LINE__);
    dchan = dma_request_chan(dev, chan_name);
    if(!dchan)
    {
        printk("[%s]: i = %d, dma_request_chan failed\n", __func__, i);
        if(s_phys_addr){
            yd_dma_cv_free_coherent(dev, len, s_phys_addr, s_ptr);
        }
        if(d_phys_addr)
        {
            yd_dma_cv_free_coherent(dev, len, d_phys_addr, d_ptr);
        }
        vfree(cb_info);
        return NULL;
    }

    tx = dmaengine_prep_dma_memcpy(dchan, dst, src, len, 0);
    if(!tx)
    {
        printk("[%s]: i = %d, dma_request_chan failed\n", __func__, i);
        if(s_phys_addr){
            yd_dma_cv_free_coherent(dev, len, s_phys_addr, s_ptr);
        }
        if(d_phys_addr)
        {
            yd_dma_cv_free_coherent(dev, len, d_phys_addr, d_ptr);
        }

        vfree(cb_info);
        dma_release_channel(dchan);
        return NULL;
    }

    tx->callback = dma_complete_callback;
    cb_info->dchan = dchan;

    cb_info->type = type;
    cb_info->src = src;
    cb_info->dst = dst;
    cb_info->s_ptr = s_ptr;
    cb_info->d_ptr = d_ptr;
    cb_info->len = len;
    cb_info->bar = bar;
    cb_info->res_start = res_start;
    tx->callback_param = cb_info;
    cb_info->run_cnt = run_cnt;
    cb_info->dev = dev;
    cookie = dmaengine_submit(tx);
    cb_info->cookie = cookie;
    return cb_info;

}


static int yd_dma_cv_testcase_14(struct device *dev, unsigned long res_start, void __iomem *bar) //all channel run
{

    struct dma_chan *dchan;
    uint8_t i;
    struct cv_cb_info *cb_info;
    long timeout = 255000;
    unsigned long start_j, end_j, time;
    printk("[%s]: start test all channel run\n", __func__);


    g_over_cnt = 1;
    start_j = jiffies;
    cb_info = yd_dma_one_chan_gen(dev, YD_DMA_MEM_TO_MEM, 0, 0, chan_desc[1].name, NULL, 1, 1024 * 1024);
    if(!cb_info)
    {
        printk("[%s]: %d: cbinfo null\n", __func__, __LINE__);
        return -1;
    }
    dchan =  cb_info->dchan;

    dma_async_issue_pending(dchan);


    if(!wait_for_completion_timeout(&g_comp, msecs_to_jiffies(timeout))) {
        printk("[%s]: wait_for_completion_timeout timeout\n", __func__);

    }


    dma_release_channel(dchan);
    yd_dma_cv_release_resource(cb_info->type, cb_info);
    end_j = jiffies;
    time = jiffies_to_msecs(end_j - start_j);
    printk("1m need %d ms\n", time);


    printk("[%s]: %d: over\n", __func__, __LINE__);

    return 0;
}


static int yd_dma_cv_testcase_10(struct device *dev, unsigned long res_start, void __iomem *bar) //all channel run
{

    struct dma_chan *dchan[DMA_CV_MAX_CHAN_CNT];
    uint8_t i;
    struct cv_cb_info *cb_info[DMA_CV_MAX_CHAN_CNT];
    long timeout = 255000;
    printk("[%s]: start test all channel run\n", __func__);

    for(i = 0; i< 5;i++)
    {
        printk("[%s]: %d: i = %d", __func__, __LINE__, i);
        cb_info[i] = yd_dma_one_chan_gen(dev, YD_DMA_MEM_TO_MEM, 0, 0, chan_desc[i].name, NULL, 1, 0);
        if(!cb_info[i])
        {
            printk("[%s]: %d: i = %d", __func__, __LINE__, i);
            return -1;
        }
        dchan[i] =  cb_info[i]->dchan;
    }
    printk("[%s]: %d: i = %d", __func__, __LINE__, i);
    cb_info[i] = yd_dma_one_chan_gen(dev, YD_DMA_DEV_TO_MEM, res_start, bar, chan_desc[i].name, NULL, 1, 0);
    if(!cb_info[i])
    {

        return -1;
    }
    dchan[i] = cb_info[i]->dchan;
    i++;

    cb_info[i] = yd_dma_one_chan_gen(dev, YD_DMA_MEM_TO_DEV, res_start, bar, chan_desc[i].name, NULL, 1, 0);
    if(!cb_info[i])
    {

        return -1;
    }
    dchan[i] = cb_info[i]->dchan;
    i++;


    g_over_cnt = 8;
    cb_info[i] = yd_dma_one_chan_gen(dev, YD_DMA_DEV_TO_DEV, res_start, bar, chan_desc[i].name, NULL, 1, 0);
    if(!cb_info[i])
    {

        return -1;
    }
    dchan[i] = cb_info[i]->dchan;
    for(i = 0; i< DMA_CV_MAX_CHAN_CNT;i++)
    {

        dma_async_issue_pending(dchan[i]);
    }

    if(!wait_for_completion_timeout(&g_comp, msecs_to_jiffies(timeout))) {
        printk("[%s]: wait_for_completion_timeout timeout\n", __func__);

    }

    for(i = 0; i< DMA_CV_MAX_CHAN_CNT;i++)
    {

        dma_release_channel(dchan[i]);
        yd_dma_cv_release_resource(cb_info[i]->type, cb_info[i]);
    }

    printk("[%s]: %d: over\n", __func__, __LINE__);

    return 0;
}


static int yd_dma_cv_testcase_11(struct device *dev, unsigned long res_start, void __iomem *bar) //all channel run
{

    struct dma_chan *dchan[DMA_CV_MAX_CHAN_CNT];
    uint32_t i;
    struct cv_cb_info *cb_info[DMA_CV_MAX_CHAN_CNT];
    long timeout = 255000;
    printk("[%s]: start test all channel run\n", __func__);

    for(i = 0; i < 300; i++)
    {
        if(yd_dma_cv_testcase_10(dev, res_start, bar))
        {
            printk("[%s]: %d: yd_dma_cv_testcase_10 failed\n", __func__, __LINE__);
        }
    }

    return 0;
    for(i = 0; i< 5;i++)
    {

        cb_info[i] = yd_dma_one_chan_gen(dev, YD_DMA_MEM_TO_MEM, 0, 0, chan_desc[i].name, NULL, 100, 0);
        if(!cb_info[i])
        {

            return -1;
        }
        dchan[i] =  cb_info[i]->dchan;
    }

    cb_info[i] = yd_dma_one_chan_gen(dev, YD_DMA_MEM_TO_DEV, res_start, bar, chan_desc[i].name, NULL, 100, 0);
    if(!cb_info[i])
    {

        return -1;
    }
    dchan[i] = cb_info[i]->dchan;
    i++;

    cb_info[i] = yd_dma_one_chan_gen(dev, YD_DMA_MEM_TO_DEV, res_start, bar, chan_desc[i].name, NULL, 100, 0);
    if(!cb_info[i])
    {

        return -1;
    }
    dchan[i] = cb_info[i]->dchan;
    i++;


    g_over_cnt = 8;
    cb_info[i] = yd_dma_one_chan_gen(dev, YD_DMA_DEV_TO_DEV, res_start, bar, chan_desc[i].name, NULL, 100, 0);
    if(!cb_info[i])
    {

        return -1;
    }
    dchan[i] = cb_info[i]->dchan;
    for(i = 0; i< DMA_CV_MAX_CHAN_CNT;i++)
    {

        dma_async_issue_pending(dchan[i]);
    }

    if(!wait_for_completion_timeout(&g_comp, msecs_to_jiffies(timeout))) {
        printk("[%s]: wait_for_completion_timeout timeout\n", __func__);

    }
    printk("[%s]: %d: over\n", __func__, __LINE__);

    return 0;
}


#define DMA_DEV_VENDOR_ID   0x1357
#define DMA0_DEV_DEVICE_ID   0x1234

#include <linux/pci.h>

static struct pci_dev *ntb_cv_get_dma0_dev(void)
{
    struct pci_dev *dev = NULL;
    dev = pci_get_device(DMA_DEV_VENDOR_ID, DMA0_DEV_DEVICE_ID, dev);
    return dev;
    return NULL;
}

static int yd_dma_cv_testcase_13(struct device *dev)
{
    long timeout = 15000;
    int ret;
    struct cv_cb_info *cb_info = NULL;
    struct dma_chan *ep0_dchan = NULL, *ep1_dchan = NULL;
    cb_info = yd_dma_one_chan_gen(dev, YD_DMA_MEM_TO_MEM, 0, 0, chan_desc[0].name, NULL, 1, 0);
    ep0_dchan = cb_info->dchan;
    printk("[%s]: %d: ep0_dhcan = %p\n", __func__, __LINE__, ep0_dchan);
    //cb_info = yd_dma_one_chan_gen(&ntb_cv_get_dma0_dev->dev, YD_DMA_MEM_TO_MEM, 0, 0, chan_desc[0].name, NULL, 1, 0);
    ep1_dchan = cb_info->dchan;
    printk("[%s]: %d: ep1_dhcan = %p\n", __func__, __LINE__, ep1_dchan);
    g_over_cnt = 2;
    dma_async_issue_pending(ep0_dchan);

    dma_async_issue_pending(ep1_dchan);

    if(!wait_for_completion_timeout(&g_comp, msecs_to_jiffies(timeout))) {
        printk("[%s]: wait_for_completion_timeout timeout\n", __func__);
        ret = 0;
    }
    return 0;

}


static int yd_dma_test_probe(struct pci_dev *pdev,
			       const struct pci_device_id *id)
{

    unsigned long res_start, res_len;
    struct device *dev = &pdev->dev;
    void __iomem *bar = NULL;
    int ret;
    if(gen_test(pdev))
    {
        return -1;
    }

    res_start = pci_resource_start(pdev, 0);
    res_len = pci_resource_len(pdev, 0);
    if(!devm_request_mem_region(dev, res_start, res_len, KBUILD_MODNAME))
    {
        return -1;
    }

    bar = devm_ioremap(dev, res_start, res_len);  /*nocache*/

    dev->init_name = DMA_TEST_DEV_NAME;


    init_completion(&g_comp);
    if(yd_dma_cv_testcase_04(dev))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_04 failed\n", __func__, __LINE__);
    }


    writel(0x12345678, (void *)(bar + 0x120));
    if(yd_dma_cv_testcase_05(dev, res_start + 0x120, res_start + 0x128, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_05 failed\n", __func__, __LINE__);
    }

    writel(0x66666666, (void *)(bar + 0x320));
    if(yd_dma_cv_testcase_06(dev, res_start + 0x320, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_06 failed\n", __func__, __LINE__);
    }
    if(yd_dma_cv_testcase_07(dev, res_start + 0x520, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_07 failed\n", __func__, __LINE__);
    }
    if(yd_dma_cv_testcase_11(dev, res_start, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_11 failed\n", __func__, __LINE__);
    }
    if(yd_dma_cv_testcase_12(dev))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_04 failed\n", __func__, __LINE__);
    }
    
    if(yd_dma_cv_testcase_08(dev))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_08 failed\n", __func__, __LINE__);
    }
    
    if(yd_dma_cv_testcase_09(dev))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_09 failed\n", __func__, __LINE__);
    }
     if(yd_dma_cv_testcase_14(dev, res_start, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_12 failed\n", __func__, __LINE__);
    }
    return 0;


    /*****************************************************************************/
    /*h cv case 07*/
    if(yd_dma_cv_testcase_12(dev))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_04 failed\n", __func__, __LINE__);
    }
   


        /*h cv case 04*/
    iowrite32(0x12345677, (bar + 0x404));
    if(yd_dma_cv_testcase_05(dev, res_start + 0x404, res_start + 0x40c, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_05 failed\n", __func__, __LINE__);
    }


    /*h cv case 05*/
    writel(0x778899, bar + 0x418);
    if(yd_dma_cv_testcase_06(dev, res_start + 0x418, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_06 failed\n", __func__, __LINE__);
    }
  


    /*h cv case 06*/
    if(yd_dma_cv_testcase_07(dev, res_start + 0x520, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_07 failed\n", __func__, __LINE__);
    }


    /*h cv case 08*/
    if(yd_dma_cv_testcase_10(dev, res_start, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_10 failed\n", __func__, __LINE__);
    }

    /*h cv case 09*/
    if(yd_dma_cv_testcase_11(dev, res_start, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_11 failed\n", __func__, __LINE__);
    }

    if(yd_dma_cv_testcase_08(dev))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_08 failed\n", __func__, __LINE__);
    }
    return 0;
    /*   if(yd_dma_cv_testcase_09(dev))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_09 failed\n", __func__, __LINE__);
    }*/


    /*printk("[%s]: %d: start cv test 14\n", __func__, __LINE__);

     if(yd_dma_cv_testcase_14(dev, res_start, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_12 failed\n", __func__, __LINE__);
    }*/
	
    /*printk("[%s]: %d: start test cv case04-------------------------\n", __func__, __LINE__);
    if(yd_dma_cv_testcase_04(dev))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_04 failed\n", __func__, __LINE__);
    }*/

   /* printk("[%s]: %d: start test cv case05-------------------------\n", __func__, __LINE__);
    if(yd_dma_cv_testcase_05(dev, res_start + 0x120, res_start + 0x128, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_05 failed\n", __func__, __LINE__);
    }

    printk("[%s]: %d: start test cv case06-----------------------------\n", __func__, __LINE__);
    if(yd_dma_cv_testcase_06(dev, res_start + 0x120, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_06 failed\n", __func__, __LINE__);
    }

    printk("[%s]: %d: start test cv case07--------------------------\n", __func__, __LINE__);
    if(yd_dma_cv_testcase_07(dev, res_start + 0x124, bar))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_07 failed\n", __func__, __LINE__);
    }*/

    printk("[%s]: %d: start test cv case08--------------------------\n", __func__, __LINE__);
    if(yd_dma_cv_testcase_08(dev))
    {
        printk("[%s]: %d: yd_dma_cv_testcase_08 failed\n", __func__, __LINE__);
    }


 


    return 0;
}

static void yd_dma_remove(struct pci_dev *pdev)
{



}

#define YD_DMA_DEVICE_VENDOR	0x9011
#define YD_DMA_DEVICE1_ID		0x5678//DMA-EP0
#define YD_DMA_DEVICE2_ID		0x1336	//DMA-EP1

static const struct pci_device_id yd_dma_ids[] = {
	{ YD_DMA_DEVICE_VENDOR, YD_DMA_DEVICE1_ID, PCI_ANY_ID, PCI_ANY_ID, 0, 0, 0 },
	{ YD_DMA_DEVICE_VENDOR, YD_DMA_DEVICE2_ID, PCI_ANY_ID, PCI_ANY_ID, 0, 0, 0 },
	{ 0, }
};

MODULE_DEVICE_TABLE(pci, yd_dma_ids);

static const struct pci_device_id yd_dma_pci_tbl[] = {
	{PCI_DEVICE(YD_DMA_DEVICE_VENDOR, YD_DMA_DEVICE1_ID)},
	{PCI_DEVICE(YD_DMA_DEVICE_VENDOR, YD_DMA_DEVICE2_ID)},
	{0},
};


static struct pci_driver yd_dma_pci_driver = {
	.name       = KBUILD_MODNAME,
	.probe		= yd_dma_test_probe,
	.remove		= yd_dma_remove,
	.id_table	= yd_dma_ids,
};


//module_pci_driver(yd_dma_pci_driver);

module_pci_driver(yd_dma_pci_driver);
