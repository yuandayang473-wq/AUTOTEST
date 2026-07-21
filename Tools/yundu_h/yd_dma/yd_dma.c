
#include "yd_dma.h"
#include "dmaengine.h"
MODULE_DESCRIPTION("YunDu PCIe Switch DMA Engine");
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Chen Hao");

#define YD_DMA_DEVICE_VENDOR	0x205e
#define YD_DMA_DEVICE1_ID		0x0000 //-EP0
#define YD_DMA_DEVICE2_ID		0x0000	//DMA-EP1

#define YD_DMA_CONFIG_BAR_ID	0
#define YD_DMA_CHANNEL_CNT	8
#define YD_DMA_CHANNEL_CFG_OFFSET	0x200
#define YD_DMA_DESC_NUM	512
#define YD_DMA_TRANSFER_SIZE	0xffffffff

enum yd_chan_state{
	YD_CHAN_STATUS_IDLE,
	YD_CHAN_STATUS_RUNNING,
	YD_CHAN_STATUS_PAUSED,
	YD_CHAN_STATUS_WAITTING,
	YD_CHAN_STATUS_ABORT,
};

enum yd_dma_err{
	YD_DMA_NO_ERR,
	YD_DMA_LL_CPL_UR_ERR = 0x1,
	YD_DMA_LL_CPL_CA_ERR = 0x2,
	YD_DMA_LL_CPL_EP_ERR = 0x3,
	YD_DMA_DATA_CPL_TIMEOUT_ERR = 0x8,
	YD_DMA_DATA_CPL_UR_ERR = 0x9,
	YD_DMA_DATA_CPL_CA_ERR = 0xa,
	YD_DMA_DATA_CPL_EP_ERR = 0xb,
	YD_DMA_MWR_ERR = 0xc,
	YD_DMA_MAX_ERR_NUM,
};

typedef struct {
	uint32_t err_num;
	char *err_desc;
}yd_dma_err_desc_t;

yd_dma_err_desc_t yd_dma_err_desc[YD_DMA_MAX_ERR_NUM] = {
	[YD_DMA_LL_CPL_UR_ERR] = {YD_DMA_LL_CPL_UR_ERR, "ll cpl ur err"},
	[YD_DMA_LL_CPL_CA_ERR] = {YD_DMA_LL_CPL_CA_ERR, "ll cpl ca err"},
	[YD_DMA_LL_CPL_EP_ERR] = {YD_DMA_LL_CPL_EP_ERR, "ll cpl ep err"},
	[YD_DMA_DATA_CPL_TIMEOUT_ERR] = {YD_DMA_DATA_CPL_TIMEOUT_ERR, "data cpl timeout err"},
	[YD_DMA_DATA_CPL_UR_ERR] = {YD_DMA_DATA_CPL_UR_ERR, "data cpl ur err"},
	[YD_DMA_DATA_CPL_CA_ERR] = {YD_DMA_DATA_CPL_CA_ERR, "data cpl ca err"},
	[YD_DMA_DATA_CPL_EP_ERR] = {YD_DMA_DATA_CPL_EP_ERR, "data cpl ep err"},
	[YD_DMA_MWR_ERR] = {YD_DMA_MWR_ERR, "data mwr err"},

};

typedef struct yd_dma_chan{
	const char *name;
	struct dma_chan dchan;
	dma_ep_reg_t *reg;
	uint8_t chan_id;
	struct tasklet_struct tasklet;
	struct yd_dmac_tx *ydtx;
	uint32_t irq;
	enum yd_chan_state state;
	size_t total_len;
	size_t residue;
	spinlock_t lock;
	struct dma_slave_config	config;
	enum yd_dma_err err_num;
}yd_dma_chan_t;

typedef struct yd_dma_desc{
	__le32 saddr_lo;
	__le32 saddr_hi;
	__le32 daddr_lo;
	__le32 daddr_hi;
	size_t size;
	uint32_t control;
}yd_dma_desc_t;

/*yd dma desc control*/
#define YD_DMA_DESC_CTRL_END	(BIT(0))

struct yd_dmac_tx{
	struct yd_dma_desc *desc;
	uint32_t desc_num;
	struct list_head node;
	struct list_head tx_list;
	struct dma_async_tx_descriptor tx;
};

typedef struct yd_dma_data_back{
	uint32_t mask;
	uint32_t msi_addr_lo;
	uint32_t msi_addr_hi;
	uint32_t msi_data;
}yd_dma_data_back_t;

typedef struct yd_dmac_dev{
	struct dma_device	dma;
	/* channels */
	struct yd_dma_chan	*sw_chan;
	struct pci_dev *pdev;
	uint32_t irq;
	void __iomem *bar;
	yd_dma_data_back_t back;
	struct work_struct cts_work;
}yd_dmac_dev_t;

static yd_dmac_dev_t *g_ydd = NULL;
int int_flag=0;

#include <linux/delay.h>
static void yd_dma_cts_work(struct work_struct *work)
{
	struct pci_dev *pdev = NULL;
	int err, i;
	yd_dma_chan_t *sw_dchan = NULL;
	dma_ep_reg_t *reg		= NULL;
	yd_dmac_dev_t *ydd = container_of(work,struct yd_dmac_dev,cts_work);

	int int_flag=0;
	if(!ydd)
	{
		printk("ydd no find\n");
		return ;
	}
	pdev=ydd->pdev;

	if(pdev->msi_enabled)
	{
		int_flag=1;
	}
	else{
		int_flag=0;
	}


	pci_save_state(pdev);
	pci_clear_master(pdev);
	//printk("will flr");
	err = pcie_flr(pdev);
	if (err)
	{
		printk("flr failed\n");
		return;
	}
	err=pcim_enable_device(pdev);
	pci_restore_state(pdev);

	uint32_t tmp_val=0;
	if(int_flag)
	{
		for(i = 0; i < YD_DMA_CHANNEL_CNT;i++)
		{
			sw_dchan = &ydd->sw_chan[i];
			reg = sw_dchan->reg = ydd->bar + 0x100 + (i * YD_DMA_CHANNEL_CFG_OFFSET);
			writel(DMA_INT_ALL_MASK, &reg->DMA_INT_SETUP_OFF_CH);
			sw_dchan->state = YD_CHAN_STATUS_IDLE;

			writel(ydd->back.msi_addr_lo, &reg->DMA_MSI_STOP_LOW_OFF_CH);
			writel(ydd->back.msi_addr_hi, &reg->DMA_MSI_STOP_HIGH_OFF_CH);
			writel(ydd->back.msi_addr_lo, &reg->DMA_MSI_WATERMARK_LOW_OFF_CH);
			writel(ydd->back.msi_addr_hi, &reg->DMA_MSI_WATERMARK_HIGH_OFF_CH);
			writel(ydd->back.msi_addr_lo, &reg->DMA_MSI_ABORT_LOW_OFF_CH);
			writel(ydd->back.msi_addr_hi, &reg->DMA_MSI_ABORT_HIGH_OFF_CH);
			writel(ydd->back.msi_data, &reg->DMA_MSI_MSGD_OFF_CH);

			//printk("i=%d data=0x%x, addr = %llx", i, readl(&reg->DMA_STATUS_OFF_CH), &reg->DMA_STATUS_OFF_CH);

		}
	}
	else
	{

		for(i = 0; i < YD_DMA_CHANNEL_CNT;i++)
		{
			sw_dchan = &ydd->sw_chan[i];
			reg = sw_dchan->reg = ydd->bar + 0x100 + (i * YD_DMA_CHANNEL_CFG_OFFSET);
			writel(0x70, &reg->DMA_INT_SETUP_OFF_CH);
			tmp_val = readl(&reg->DMA_STATUS_OFF_CH) | 0x1;
			writel(tmp_val, &reg->DMA_INT_CLEAR_OFF_CH);
			sw_dchan->state = YD_CHAN_STATUS_IDLE;
			//printk("i=%d data=0x%x, addr = %llx", i, readl(&reg->DMA_STATUS_OFF_CH), &reg->DMA_STATUS_OFF_CH);

		}

	}
	printk("flr success\n");
}


static void yd_dma_start_transfer(yd_dma_chan_t *sw_dchan);

static struct yd_dma_chan *to_yd_dma_chan(struct dma_chan *dchan)
{
	return container_of(dchan, struct yd_dma_chan, dchan);
}

static struct yd_dma_chan *tasket_to_yd_dma_chan(struct tasklet_struct *tasklet)
{
	return container_of(tasklet, struct yd_dma_chan, tasklet);
}

#if 0
static struct yd_dmac_tx *yd_tx_to_desc(struct dma_async_tx_descriptor *tx)
{
	return container_of(tx, struct yd_dmac_tx, tx);
}
#endif

static struct device *sw_chan_to_chan_dev(yd_dma_chan_t *sw_dchan)
{
    return &sw_dchan->dchan.dev->device;
}


/*static void yd_dma_change_rp_conf(struct pci_dev *pdev)
{
        struct pci_dev *rp_pdev = NULL;
        uint32_t offset, reg;
        rp_pdev = pcie_find_root_port(pdev);
        if(!rp_pdev)
        {
                printk("not find rp");
                return;

        }
        printk("rp bus is 0x%x, devfn is 0x%x\n", rp_pdev->bus->number, rp_pdev->devfn);

        offset = pci_find_capability(rp_pdev, PCI_CAP_ID_EXP);
        if(!offset)
        {

                return;
        }

        pci_read_config_dword(rp_pdev, offset + PCI_EXP_DEVCTL2, &reg);
        printk("val is 0x%x", reg);
        reg &= ~BIT(4);
        printk("val is 0x%x", reg);
        pci_write_config_dword(rp_pdev, offset + PCI_EXP_DEVCTL2, reg);


}*/


/*如果用户关注还剩下多少字节没传，就输入txstate字段，但是根据设计只能给出大概长度*/
/*如果需要关注精细了，需要把4G降到够低得粒度*/
static enum dma_status yd_dma_tx_status(struct dma_chan *dchan,
		dma_cookie_t cookie, struct dma_tx_state *txstate)
{
	yd_dma_chan_t *sw_dchan = to_yd_dma_chan(dchan);
	enum dma_status		ret;
	ret = dma_cookie_status(dchan, cookie, txstate);
	if (ret == DMA_COMPLETE)
		return ret;
	spin_lock_bh(&sw_dchan->lock);
	/*如果应用关注txstate，停止状态和进行状态应该来个大约剩余多少字节得数*/
	if(txstate)
	{
		switch (sw_dchan->state)
		{
		case YD_CHAN_STATUS_RUNNING:

			ret = DMA_IN_PROGRESS;
			dma_set_tx_state(txstate, dchan->completed_cookie, dchan->cookie, sw_dchan->residue);
			break;
		case YD_CHAN_STATUS_PAUSED:
			ret = DMA_PAUSED;
			dma_set_tx_state(txstate, dchan->completed_cookie, dchan->cookie, sw_dchan->residue);
			break;
		case YD_CHAN_STATUS_ABORT:
			/*terminate*/
			ret = DMA_COMPLETE;
			dma_set_tx_state(txstate, dchan->completed_cookie, dchan->cookie, 0);
			break;
		default:
			ret = DMA_ERROR;
			break;
		}
	}
	spin_unlock_bh(&sw_dchan->lock);
	return ret;
}

static void yd_dma_channel_reset(yd_dma_chan_t *sw_dchan)
{
	//yd_dma_chan_t *sw_dchan = to_yd_dma_chan(dchan);
	//dma_ep_reg_t *reg = sw_dchan->reg;
	//writel(DMA_DOORBELL_STOP, &reg->DMA_DOORBELL_OFF_CH);
	//writel(DMA_REG_ZERO, &reg->DMA_DOORBELL_OFF_CH);

}


static int yd_dma_chan_slave_config(struct dma_chan *dchan,
					struct dma_slave_config *config)
{
	yd_dma_chan_t *sw_dchan = to_yd_dma_chan(dchan);
	if(!sw_dchan)
		return -1;
	memcpy(&sw_dchan->config, config, sizeof(*config));

	return 0;
}

static int yd_dma_resume(struct dma_chan *dchan)
{
	yd_dma_chan_t *sw_dchan	= to_yd_dma_chan(dchan);
#ifdef YD_DMA_LINK_LIST
	dma_ep_reg_t *reg		= sw_dchan->reg;
	//int retry				= DMA_PAUSE_RESUME_RETRY;

	uint32_t tmp;
#endif
	int ret;

	spin_lock(&sw_dchan->lock);
#ifdef YD_DMA_LINK_LIST
	tmp = readl(&reg->DMA_STATUS_OFF_CH) & DMA_STATUS_MASK;
	if(tmp != DMA_STATUS_RUNNING)
	{
		pci_dbg("[%s]: %d: chan not running\n", __func__, __LINE__);
		spin_unlock(&sw_dchan->lock);
		return 0;
	}
	tmp = readl(&reg->DMA_DOORBELL_OFF_CH);
	tmp &= ~DMA_DOORBELL_STOP;
	tmp |= DMA_DOORBELL_START;

	writel(tmp, &reg->DMA_DOORBELL_OFF_CH);
	ret = 0;

	tmp = readl(&reg->DMA_STATUS_OFF_CH) & DMA_STATUS_MASK; //不能这样匹配，万一delay中间完成，就不会是running状态了

	if(tmp == DMA_STATUS_RUNNING)
	{
		ret = 0;

	}
#endif
	if(sw_dchan->state != YD_CHAN_STATUS_PAUSED)
	{
		spin_unlock(&sw_dchan->lock);
		return -1;
	}
	sw_dchan->state = YD_CHAN_STATUS_RUNNING;
	yd_dma_start_transfer(sw_dchan);
	spin_unlock(&sw_dchan->lock);
	return ret;
}

static int yd_dma_pause(struct dma_chan *dchan)
{
    yd_dma_chan_t *sw_dchan	= to_yd_dma_chan(dchan);
#ifdef YD_DMA_LINK_LIST
	dma_ep_reg_t *reg		= sw_dchan->reg;
	uint32_t tmp;
	int retry = DMA_PAUSE_RESUME_RETRY;
#endif
	int ret;

	spin_lock(&sw_dchan->lock);
#ifdef YD_DMA_LINK_LIST
	tmp = readl(&reg->DMA_STATUS_OFF_CH) & DMA_STATUS_MASK;
	if(tmp != DMA_STATUS_RUNNING)
	{

		spin_unlock(&sw_dchan->lock);
		return 0;
	}
	tmp = readl(&reg->DMA_DOORBELL_OFF_CH);
	tmp |= DMA_DOORBELL_STOP;

	writel(tmp, &reg->DMA_DOORBELL_OFF_CH);

	//ret = -EIO;
	ret = 0;
	tmp = readl(&reg->DMA_STATUS_OFF_CH) & DMA_STATUS_MASK;

	if(tmp == DMA_STATUS_STOPPED)
	{

		//ret = 0;

	}
#endif
	if(sw_dchan->state != YD_CHAN_STATUS_RUNNING)
	{
		spin_unlock(&sw_dchan->lock);
		return -1;
	}
	sw_dchan->state = YD_CHAN_STATUS_PAUSED;

	spin_unlock(&sw_dchan->lock);
	return ret;
}

static int yd_dma_terminate_all(struct dma_chan *dchan)
{
	yd_dma_chan_t *sw_dchan	= to_yd_dma_chan(dchan);
	spin_lock(&sw_dchan->lock);
	yd_dma_channel_reset(sw_dchan);
	sw_dchan->state = YD_CHAN_STATUS_ABORT;
	spin_unlock(&sw_dchan->lock);
	return 0;
}

static void yd_dma_synchronize(struct dma_chan *dchan)
{
	yd_dma_chan_t *sw_dchan	= to_yd_dma_chan(dchan);
	spin_lock(&sw_dchan->lock);
	tasklet_kill(&sw_dchan->tasklet);
	spin_unlock(&sw_dchan->lock);
}

#define YD_DMA_RADL_CHANNEL_ENABLE	0x1
/*开始传输，因为根据文档描述，没有可以现在宽度及对齐得寄存器，所以不做配置判断*/
static void yd_dma_start_transfer(yd_dma_chan_t *sw_dchan)
{
	uint32_t tmp;
	dma_ep_reg_t *reg			= sw_dchan->reg;

	struct yd_dmac_tx *ydtx		= sw_dchan->ydtx;
	uint32_t desc_num			= ydtx->desc_num;
	struct yd_dma_desc *desc	= NULL;

	if(!ydtx->desc)
	{
		return;
	}
	desc						= &ydtx->desc[desc_num];

	writel(desc->size, &reg->DMA_XFERSIZE_OFF_CH);

	writel(desc->saddr_lo, &reg->DMA_SAR_LOW_OFF_CH);
	writel(desc->saddr_hi, &reg->DMA_SAR_HIGH_OFF_CH);
	writel(desc->daddr_lo, &reg->DMA_DAR_LOW_OFF_CH);
	writel(desc->daddr_hi, &reg->DMA_DAR_HIGH_OFF_CH);

	writel(YD_DMA_RADL_CHANNEL_ENABLE, &reg->DMA_EN_OFF_CH);

	tmp = readl(&reg->DMA_CONTROL1_OFF_CH);
	tmp &= ~DMA_CONTROL1_LLEN;
	writel(tmp, &reg->DMA_CONTROL1_OFF_CH);

	tmp = readl(&reg->DMA_DOORBELL_OFF_CH);
	tmp |= DMA_DOORBELL_START;
	writel(tmp, &reg->DMA_DOORBELL_OFF_CH);
	sw_dchan->state = YD_CHAN_STATUS_RUNNING;


}
static void yd_dma_issue_pending(struct dma_chan *dchan)
{
	yd_dma_chan_t *sw_dchan = to_yd_dma_chan(dchan);

	spin_lock_bh(&sw_dchan->lock);

	yd_dma_start_transfer(sw_dchan);

	spin_unlock_bh(&sw_dchan->lock);
}

static dma_cookie_t yd_dma_tx_submit(struct dma_async_tx_descriptor *tx)
{
	//yd_dma_chan_t *sw_dchan = to_yd_dma_chan(tx->chan);

	//struct yd_dma_desc *desc = yd_tx_to_desc(tx);
	dma_cookie_t cookie = -EINVAL;
	cookie = dma_cookie_assign(tx);
	return cookie;
}



static struct yd_dmac_tx *yd_dma_alloc_descriptor(yd_dma_chan_t *sw_dchan)
{
	struct yd_dmac_tx *ydtx				= NULL;
	struct dma_async_tx_descriptor *tx	= NULL;
	struct dma_chan *dchan				= &sw_dchan->dchan;


	ydtx = kmalloc(sizeof(struct yd_dmac_tx), GFP_KERNEL);
	if(!ydtx)
	{

		return NULL;
	}

	tx	= &ydtx->tx;

	dma_async_tx_descriptor_init(tx, dchan);
	tx->tx_submit = yd_dma_tx_submit;
	tx->cookie = DMA_COMPLETE;

	return ydtx;
}
static int yd_dma_alloc_chan_resources(struct dma_chan *dchan)
{

	yd_dma_chan_t *sw_dchan = to_yd_dma_chan(dchan);
	if(!sw_dchan)
	{
		return -ENOMEM;
	}

	sw_dchan->ydtx = yd_dma_alloc_descriptor(sw_dchan);
	if(!sw_dchan->ydtx)
	{
		return -ENOMEM;
	}
	sw_dchan->ydtx->desc = kcalloc(YD_DMA_DESC_NUM, sizeof(struct yd_dma_desc), GFP_NOWAIT);
	if (!sw_dchan->ydtx->desc)
	{
		return -ENOMEM;
	}

	spin_lock_bh(&sw_dchan->lock);
	yd_dma_channel_reset(sw_dchan);
	sw_dchan->state = YD_CHAN_STATUS_WAITTING;

	spin_unlock_bh(&sw_dchan->lock);
	return 0;
}

static void yd_dma_free_chan_resources(struct dma_chan *dchan)
{
	yd_dma_chan_t *sw_dchan = to_yd_dma_chan(dchan);


	if(!sw_dchan)
	{
		return;
	}
	spin_lock_bh(&sw_dchan->lock);

	yd_dma_channel_reset(sw_dchan);

	sw_dchan->state = YD_CHAN_STATUS_IDLE;
	if(sw_dchan->ydtx)
	{
		if(sw_dchan->ydtx->desc)
		{
			kfree(sw_dchan->ydtx->desc);
		}
		kfree(sw_dchan->ydtx);
	}
	memset(&sw_dchan->config, 0, sizeof(struct dma_slave_config));
	spin_unlock_bh(&sw_dchan->lock);

}




/*暂时实现了memcpy,但是可超过4G上线*/
static struct dma_async_tx_descriptor *yd_dma_prep_memcpy(
		struct dma_chan *dchan, dma_addr_t dma_dst, dma_addr_t dma_src,
		size_t len, unsigned long flags)
{
	yd_dma_chan_t *sw_dchan		= to_yd_dma_chan(dchan);

	struct yd_dmac_tx *ydtx		= sw_dchan->ydtx;
	struct yd_dma_desc *desc	= NULL;
	size_t copy, transfer_size;
	uint32_t i;

	if(sw_dchan->state != YD_CHAN_STATUS_WAITTING)
	{

		return NULL;
	}
	spin_lock_bh(&sw_dchan->lock);

/*
	ydtx = yd_dma_alloc_descriptor(sw_dchan);
	if(!ydtx)
	{
		spin_unlock_bh(&sw_dchan->lock);
		return NULL;
	}
*/
	sw_dchan->total_len = len;
	sw_dchan->residue = len;
	do{
		desc = &ydtx->desc[i];
		if(sw_dchan->config.src_maxburst)
		{
			transfer_size = sw_dchan->config.src_maxburst;
		}
		else{
			transfer_size = YD_DMA_TRANSFER_SIZE;
		}

		copy = min_t(size_t, len, transfer_size);
		desc->saddr_lo = cpu_to_le32(lower_32_bits(dma_src));
		desc->saddr_hi = cpu_to_le32(upper_32_bits(dma_src));
		desc->daddr_lo = cpu_to_le32(lower_32_bits(dma_dst));
		desc->daddr_hi = cpu_to_le32(upper_32_bits(dma_dst));
		desc->size = copy;
		dma_src += copy;
		dma_dst += copy;
		len -= copy;
		i++;

		if(i >= YD_DMA_DESC_NUM)
		{
			spin_unlock_bh(&sw_dchan->lock);

			return NULL;
		}
	}while(len);

	desc->control |= YD_DMA_DESC_CTRL_END;
	ydtx->tx.flags = flags;

	spin_unlock_bh(&sw_dchan->lock);

	return &ydtx->tx;
}



/*描述符传输完成处理，看链表后面还有要传输得不*/
static void yd_dma_intr_stop_handler(yd_dma_chan_t *sw_dchan)
{
	struct yd_dma_desc *desc = NULL;
	uint32_t desc_num;
	struct device *chan_dev = sw_chan_to_chan_dev(sw_dchan);
	struct dmaengine_desc_callback cb;
	struct dmaengine_result tx_result;


	desc_num = sw_dchan->ydtx->desc_num;
	desc = &(sw_dchan->ydtx->desc[desc_num]);
	if(sw_dchan->err_num != 0)
	{
		dmaengine_desc_get_callback(&sw_dchan->ydtx->tx, &cb);
		switch(sw_dchan->err_num)
		{
			case YD_DMA_DATA_CPL_TIMEOUT_ERR:
				return;
			case YD_DMA_LL_CPL_CA_ERR:
			case YD_DMA_LL_CPL_EP_ERR:
			case YD_DMA_LL_CPL_UR_ERR:
			case YD_DMA_DATA_CPL_CA_ERR:
			case YD_DMA_DATA_CPL_EP_ERR:

			case YD_DMA_DATA_CPL_UR_ERR:
				tx_result.result = DMA_TRANS_READ_FAILED;
				sw_dchan->err_num=0;
				break;
			case YD_DMA_MWR_ERR:
				tx_result.result = DMA_TRANS_WRITE_FAILED;
				sw_dchan->err_num=0;
				break;
			default:
				break;
		}
		tx_result.residue = desc->size;
		dmaengine_desc_callback_invoke(&cb, &tx_result);
	}
	if(desc->control & YD_DMA_DESC_CTRL_END || sw_dchan->state == YD_CHAN_STATUS_ABORT)
	{

		dma_cookie_complete(&sw_dchan->ydtx->tx);
		dmaengine_desc_get_callback(&sw_dchan->ydtx->tx, &cb);
		tx_result.result = DMA_TRANS_NOERROR;
		tx_result.residue = 0;

		dmaengine_desc_callback_invoke(&cb, &tx_result);
		dev_dbg(chan_dev, "this channel transfer over\n");
	}
	else{

		dev_dbg(chan_dev, "this channel transfer not over, then run next desc, desc num = %d\n", desc_num);
		sw_dchan->ydtx->desc_num++;
		sw_dchan->residue -= desc->size;

		/*用于测试停止通道功能用，后续删除这段回调*/
		dmaengine_desc_get_callback(&sw_dchan->ydtx->tx, &cb);
		tx_result.result = DMA_TRANS_NOERROR;
		tx_result.residue = desc->size;
		dmaengine_desc_callback_invoke(&cb, &tx_result);
		/*添加结束*/
		spin_lock_bh(&sw_dchan->lock);
		if(sw_dchan->state == YD_CHAN_STATUS_RUNNING)  //只有状态对才继续传输，如果状态不是运行中，证明被停止了
		{
			dev_dbg(chan_dev, "chan state is YD_CHAN_STATUS_RUNNING\n");
			yd_dma_start_transfer(sw_dchan);
		}

		spin_unlock_bh(&sw_dchan->lock);
	}
}

static irqreturn_t yd_dma_irq_handler(int irq, void *data)
{
	yd_dmac_dev_t *ydd = (yd_dmac_dev_t *)data;
	yd_dma_chan_t *sw_dchan	= NULL;
	struct device *chan_dev	= NULL;
	dma_ep_reg_t *reg		= NULL;
	uint32_t status, tmp;
	uint8_t i = 0;
	void *cts_p = ydd->bar + 0x200;
	void *cts_p1 = ydd->bar + 0x204;
	void *cts_p2 = ydd->bar + 0x208;
	void *cts_p3 = ydd->bar + 0x20c;
	//printk("eneter dma stop intr");

	//printk("cpl reg =%x %x %x %x\n",readl(cts_p),readl(cts_p1),readl(cts_p2),readl(cts_p3));

	if(readl(cts_p))
	{
		//printk("cts_p =%x\n",readl(cts_p));
		writel(0x1, cts_p2);
		schedule_work(&ydd->cts_work);
	}

	/*if(int_flag)
	{
		if(readl(cts_p))
		{
			printk("cts_p =%x\n",readl(cts_p));
			schedule_work(&ydd->cts_work);
		}
	}
	else
	{
		if(readl(cts_p1))
		{
			printk("cts_p1 =%x\n",readl(cts_p1));
			schedule_work(&ydd->cts_work);
		}
	}*/


	for(i = 0; i < YD_DMA_CHANNEL_CNT;i++)
	{
		sw_dchan = &ydd->sw_chan[i];
		reg = sw_dchan->reg;
		chan_dev = sw_chan_to_chan_dev(sw_dchan);
		status = readl(&reg->DMA_INT_STATUS_OFF_CH);
		if(!status)
		{
			continue;
		}
		tmp = readl(&reg->DMA_INT_CLEAR_OFF_CH);
                writel((tmp | DMA_INT_ALL_CLEAR), &reg->DMA_INT_CLEAR_OFF_CH);

		if(status & DMA_INT_ERROR_STATUS)
		{
			tmp = (status & DMA_INT_ERROR_STATUS) >> 3;
			dev_err(chan_dev, "%s", yd_dma_err_desc[tmp].err_desc);
			sw_dchan->err_num = tmp;
			tasklet_schedule(&sw_dchan->tasklet);
		}
		if(status & DMA_INT_ABORT_STATUS)
		{
			dev_err(chan_dev, "status = DMA_INT_ABORT_STATUS\n");
		}

		/*表示一段传输完成了，但是本设计实现了非lli模式也能多段传输，所以要检查下链表*/
		if(status & DMA_INT_WATERMARK_STATUS)
		{
			//tasklet_schedule(&sw_dchan->tasklet);
			//yd_dma_intr_watermark_handler(sw_dchan);
			dev_dbg(chan_dev, "status = DMA_INT_WATERMARK_STATUS\n");
		}

		/*根据de描述，stopbit不会自动清零，需要中断里手动清一波*/
		if(status & DMA_INT_STOP_STATUS)
		{

			tmp = readl(&reg->DMA_DOORBELL_OFF_CH);
			tmp &= ~DMA_DOORBELL_STOP;
			writel(tmp, &reg->DMA_DOORBELL_OFF_CH);
			dev_dbg(chan_dev, "status = DMA_INT_STOP_STATUS\n");
			tasklet_schedule(&sw_dchan->tasklet);

		}

	}

	return IRQ_HANDLED;
}

static void yd_dma_chan_release(yd_dmac_dev_t *ydd)
{
	dma_ep_reg_t *reg		= NULL;
	yd_dma_chan_t *sw_dchan	= NULL;
	struct pci_dev *pdev	= NULL;
	uint32_t i;
	pdev = ydd->pdev;
	for(i = 0;i < YD_DMA_CHANNEL_CNT;i++)
	{
		sw_dchan = &ydd->sw_chan[i];
		reg = sw_dchan->reg;

		//devm_free_irq(&pdev->dev, sw_dchan->irq, sw_dchan);
		/*先把通道都停止了*/
		writel(DMA_DOORBELL_STOP, &reg->DMA_DOORBELL_OFF_CH);
		/*把msi中断相关寄存器初始化，防止发中断*/
		writel(DMA_REG_ZERO, &reg->DMA_MSI_STOP_LOW_OFF_CH);
		writel(DMA_REG_ZERO, &reg->DMA_MSI_STOP_HIGH_OFF_CH);
		writel(DMA_REG_ZERO, &reg->DMA_MSI_WATERMARK_LOW_OFF_CH);
		writel(DMA_REG_ZERO, &reg->DMA_MSI_WATERMARK_HIGH_OFF_CH);
		writel(DMA_REG_ZERO, &reg->DMA_MSI_ABORT_LOW_OFF_CH);
		writel(DMA_REG_ZERO, &reg->DMA_MSI_ABORT_HIGH_OFF_CH);
		writel(DMA_REG_ZERO, &reg->DMA_MSI_MSGD_OFF_CH);
		tasklet_kill(&sw_dchan->tasklet);
	}
}

//static void yd_dma_tasklet(struct tasklet_struct *tasklet)
static void yd_dma_tasklet(long unsigned int data)
{
	struct tasklet_struct *tasklet = (struct tasklet_struct *)data;

	yd_dma_chan_t *sw_dchan = tasket_to_yd_dma_chan(tasklet);
	//spin_lock(&sw_dchan->lock);
	yd_dma_intr_stop_handler(sw_dchan);
	//spin_unlock(&sw_dchan->lock);
	//dmaengine_desc_get_callback_invoke(&mxs_chan->desc, NULL);
}


static bool yd_dma_filter_fn(struct dma_chan *dchan, void *param)
{
	yd_dma_chan_t *sw_dchan = to_yd_dma_chan(dchan);
	const char *p = param;

	if(sw_dchan && sw_dchan->state != YD_CHAN_STATUS_IDLE)
	{
		return false;
	}
	return !strcmp(sw_dchan->name, p);
}

/*结构体第一个元素对应得是pci device这个dev name，第二个是通道name*/
static const struct dma_slave_map yd_dma_map[] = {
	{ "SudoNtbEP", "rx", "ydchan0" },
	{ "SudoNtbEP", "tx", "ydchan1" },
	{ "SudoNtbEP", "test1", "ydchan2" },
	{ "SudoNtbEP", "test2", "ydchan3" },
	{ "SudoNtbEP", "test3", "ydchan4" },
	{ "SudoNtbEP", "test4", "ydchan5" },
	{ "SudoNtbEP", "test5", "ydchan6" },
	{ "SudoNtbEP", "test6", "ydchan7" },
};
struct yd_dma_chan_desc{
	const char *name;
};

static const struct yd_dma_chan_desc chan_desc[] = {
	{.name = "ydchan0"},
	{.name = "ydchan1"},
	{.name = "ydchan2"},
	{.name = "ydchan3"},
	{.name = "ydchan4"},
	{.name = "ydchan5"},
	{.name = "ydchan6"},
	{.name = "ydchan7"},
};

#define PCIE_MSI_CAP_CTRL_BIT64	BIT(7)

#include <linux/msi.h>

static int yd_dma_intx_chan_init(yd_dmac_dev_t *ydd)
{
	void __iomem *bar = 0;
	uint32_t i;
	//uint32_t msi_addr_lo, msi_addr_hi, msi_data, msi_ctrl;
	dma_ep_reg_t *reg		= NULL;
	yd_dma_chan_t *sw_dchan = NULL;
	uint32_t irq;
	struct pci_dev *pdev	= ydd->pdev;
	struct device *dev		= &pdev->dev;
	struct dma_chan *dchan;
	int ret;
	unsigned long res_start, res_len;

    res_start = pci_resource_start(pdev, YD_DMA_CONFIG_BAR_ID);
    res_len = pci_resource_len(pdev, YD_DMA_CONFIG_BAR_ID);
    if(!devm_request_mem_region(dev, res_start, res_len, KBUILD_MODNAME))
    {
		pci_dbg(pdev, "devm_request_mem_region failed\n");
        return -ENOMEM;
    }

    bar = (void *)devm_ioremap(dev, res_start, res_len);
    if(!bar)
    {
		pci_dbg(pdev, "devm_ioremap failed\n");
        return -ENOMEM;
    }

	irq = pci_irq_vector(pdev, 0);
	if (irq < 0) {
		ret = irq;
		pci_dbg(pdev, "pci_irq_vector  irq < 0\n");
		goto error;
	}

	ydd->irq = irq;
	ret = request_irq(irq, yd_dma_irq_handler, IRQF_SHARED,
			      KBUILD_MODNAME, ydd);
	if(ret)
	{
		pci_dbg(pdev, "request_irq  failed\n");
		goto error;
	}
	/*初始化每个通道，主要是把通道得msi信息、cookie、通道名称初始化*/
	/*get msi cap addree and data*/
	ydd->back.mask = 0x70;
	ydd->back.msi_addr_lo = 0;
	ydd->back.msi_addr_hi = 0;
	ydd->back.msi_data = 0;
	for(i = 0; i < YD_DMA_CHANNEL_CNT;i++)
	{
		sw_dchan = &ydd->sw_chan[i];
		reg = sw_dchan->reg = bar + 0x100 + (i * YD_DMA_CHANNEL_CFG_OFFSET);
		writel(0x70, &reg->DMA_INT_SETUP_OFF_CH);
		sw_dchan->state = YD_CHAN_STATUS_IDLE;

		sw_dchan->irq = irq;   //临时加上，后期删除
		sw_dchan->name = chan_desc[i].name;

		dma_cookie_init(&sw_dchan->dchan);
		//tasklet_setup(&sw_dchan->tasklet, yd_dma_tasklet);
		tasklet_init(&sw_dchan->tasklet, yd_dma_tasklet, (long unsigned int)&sw_dchan->tasklet);
		dchan = &sw_dchan->dchan;
		dchan->device = &ydd->dma;
		list_add_tail(&dchan->device_node, &ydd->dma.channels);

		spin_lock_init(&sw_dchan->lock);
	}
	ydd->bar = bar;
	return 0;
error:
	/*
	for(;i >= 0;i--)
	{
		sw_dchan = &ydd->sw_chan[i];
		if(sw_dchan->irq)
			devm_free_irq(dev, sw_dchan->irq, sw_dchan);
	}
	*/
	return ret;
}

static int yd_dma_chan_init(yd_dmac_dev_t *ydd)
{
	void __iomem *bar = 0;
	uint32_t pos, i;
	uint32_t msi_addr_lo, msi_addr_hi, msi_data, msi_ctrl;
	dma_ep_reg_t *reg		= NULL;
	yd_dma_chan_t *sw_dchan = NULL;
	uint32_t irq;
	struct pci_dev *pdev	= ydd->pdev;
	struct device *dev		= &pdev->dev;
	struct dma_chan *dchan;
	int ret;
	unsigned long res_start, res_len;

    res_start = pci_resource_start(pdev, YD_DMA_CONFIG_BAR_ID);
    res_len = pci_resource_len(pdev, YD_DMA_CONFIG_BAR_ID);
    if(!devm_request_mem_region(dev, res_start, res_len, KBUILD_MODNAME))
    {
		pci_dbg(pdev, "devm_request_mem_region failed\n");
        return -ENOMEM;
    }

    bar = (void *)devm_ioremap(dev, res_start, res_len);
    if(!bar)
    {
		pci_dbg(pdev, "devm_ioremap failed\n");
        return -ENOMEM;
    }

	pos = pci_find_capability(pdev, PCI_CAP_ID_MSI);
	if(!pos)
	{
		pci_dbg(pdev, "pci_find_capability failed\n");
		return -ENOMEM;
	}

	pci_read_config_dword(pdev, pos, &msi_ctrl);
	if(!msi_ctrl)
	{
		pci_dbg(pdev, "pci_read_config_dword  msi ctrl failed\n");
		return -ENOMEM;
	}
	if((msi_ctrl >> 16) & PCIE_MSI_CAP_CTRL_BIT64)
	{
		i = 0xc;

	}
	else{
		i = 0x8;
	}

	pci_read_config_dword(pdev, pos + 4, &msi_addr_lo);
	if(!msi_addr_lo)
	{
		pci_dbg(pdev, "pci_read_config_dword  msi_addr_lo failed\n");
		return -ENOMEM;
	}

	pci_read_config_dword(pdev, pos + i, &msi_data);

	msi_data &= DMA_MSI_CAP_DATA;


	irq = pci_irq_vector(pdev, 0);
	if (irq < 0) {
		ret = irq;
		pci_dbg(pdev, "pci_irq_vector  irq < 0\n");
		goto error;
	}

	ydd->irq = irq;
	ret = request_irq(irq, yd_dma_irq_handler, IRQF_SHARED,
			      KBUILD_MODNAME, ydd);
	if(ret)
	{
		pci_dbg(pdev, "request_irq  failed\n");
		goto error;
	}
	/*初始化每个通道，主要是把通道得msi信息、cookie、通道名称初始化*/
	/*get msi cap addree and data*/
	ydd->back.mask = DMA_INT_ALL_MASK;
	ydd->back.msi_addr_lo = msi_addr_lo;
	ydd->back.msi_addr_hi = msi_addr_hi;
	ydd->back.msi_data = msi_data;
	for(i = 0; i < YD_DMA_CHANNEL_CNT;i++)
	{
		sw_dchan = &ydd->sw_chan[i];
		reg = sw_dchan->reg = bar + 0x100 + (i * YD_DMA_CHANNEL_CFG_OFFSET);
		writel(DMA_INT_ALL_MASK, &reg->DMA_INT_SETUP_OFF_CH); //is need?
		sw_dchan->state = YD_CHAN_STATUS_IDLE;

		writel(msi_addr_lo, &reg->DMA_MSI_STOP_LOW_OFF_CH);
		writel(msi_addr_hi, &reg->DMA_MSI_STOP_HIGH_OFF_CH);
		writel(msi_addr_lo, &reg->DMA_MSI_WATERMARK_LOW_OFF_CH);
		writel(msi_addr_hi, &reg->DMA_MSI_WATERMARK_HIGH_OFF_CH);
		writel(msi_addr_lo, &reg->DMA_MSI_ABORT_LOW_OFF_CH);
		writel(msi_addr_hi, &reg->DMA_MSI_ABORT_HIGH_OFF_CH);
		writel(msi_data, &reg->DMA_MSI_MSGD_OFF_CH);

		sw_dchan->irq = irq;   //临时加上，后期删除
		sw_dchan->name = chan_desc[i].name;

		dma_cookie_init(&sw_dchan->dchan);
		//tasklet_setup(&sw_dchan->tasklet, yd_dma_tasklet);
		tasklet_init(&sw_dchan->tasklet, yd_dma_tasklet, (long unsigned int)&sw_dchan->tasklet);
		dchan = &sw_dchan->dchan;
		dchan->device = &ydd->dma;
		list_add_tail(&dchan->device_node, &ydd->dma.channels);

		spin_lock_init(&sw_dchan->lock);
	}
	ydd->bar = bar;
	return 0;
error:
	/*
	for(;i >= 0;i--)
	{
		sw_dchan = &ydd->sw_chan[i];
		if(sw_dchan->irq)
			devm_free_irq(dev, sw_dchan->irq, sw_dchan);
	}
	*/
	return ret;
}

#define YD_DMA0_DEV_INIT_NAME    "SudoDma0EP"
#define YD_DMA1_DEV_INIT_NAME    "SudoDma1EP"

static int yd_dma_create(struct pci_dev *pdev)
{

	struct dma_device *dma	= NULL;
	struct device *dev		= &pdev->dev;
	int nr_vecs;
	int ret;
	yd_dmac_dev_t *ydd = NULL;


	ydd = devm_kzalloc(dev, sizeof(*ydd), GFP_KERNEL);
	if (!ydd)
	{
		pci_err(pdev, "devm_kcalloc ydd failed\n");
		return -ENOMEM;
	}

	g_ydd = ydd;

	if(pdev->device == YD_DMA_DEVICE1_ID)
	{
	//	dev->init_name = YD_DMA0_DEV_INIT_NAME;
	}
	else if(pdev->device == YD_DMA_DEVICE2_ID)
	{
	//	dev->init_name = YD_DMA1_DEV_INIT_NAME;
	}
	//dev->init_name = YD_DMA_DEV_INIT_NAME;


	ydd->sw_chan = devm_kcalloc(dev, YD_DMA_CHANNEL_CNT,
				sizeof(*ydd->sw_chan), GFP_KERNEL);
	if (!ydd->sw_chan)
	{
		pci_err(pdev, "devm_kcalloc sw_chan failed\n");
		ret = -ENOMEM;
		goto err_sw_dchan_alloc;
	}

	ydd->pdev = pdev;
	INIT_WORK(&ydd->cts_work, yd_dma_cts_work);
	nr_vecs = pci_msi_vec_count(pdev);
	if(nr_vecs < 1)
	{
		pci_err(pdev, "pci_msi_vec_count failed");
		ret = -ENOMEM;
		goto err_msi_vc_cnt;
	}


	ret = pci_alloc_irq_vectors(pdev, 1, YD_DMA_CHANNEL_CNT, PCI_IRQ_ALL_TYPES);
	if (ret < 0)
	{
		ret = -ENOMEM;
		pci_err(pdev, "pci_alloc_irq_vectors failed");
		goto err_msi_vc_cnt;
	}

	dma = &ydd->dma;

	INIT_LIST_HEAD(&dma->channels);

	if(pdev->msi_enabled)
	{
		int_flag=1;
		ret = yd_dma_chan_init(ydd);
	}
	else{
		int_flag=0;
		ret = yd_dma_intx_chan_init(ydd);
	}

	if(ret < 0)
	{
		pci_err(pdev, "yd_dma_chan_init failed");
		goto err_sw_dchan_init;
	}

	//tasklet_init(&ydd->tasklet, yd_dma_cts_tasklet, (long unsigned int)ydd);

	dma_cap_set(DMA_MEMCPY, dma->cap_mask);
	dma_cap_set(DMA_SLAVE, dma->cap_mask);
	dma_cap_set(DMA_PRIVATE, dma->cap_mask);

	dma->dev = get_device(dev);
	dma->chancnt = YD_DMA_CHANNEL_CNT;
	dma->device_alloc_chan_resources	= yd_dma_alloc_chan_resources;
	dma->device_free_chan_resources		= yd_dma_free_chan_resources;
	dma->device_prep_dma_memcpy			= yd_dma_prep_memcpy;
	dma->device_issue_pending			= yd_dma_issue_pending;
	dma->device_tx_status				= yd_dma_tx_status;
	dma->device_pause					= yd_dma_pause;
	dma->device_resume					= yd_dma_resume;
	dma->device_config					= yd_dma_chan_slave_config;
	dma->device_terminate_all			= yd_dma_terminate_all;
	dma->device_synchronize				= yd_dma_synchronize;
	/*device_terminate_all*/

	/*dma_request_chan得时候通过dev init_name和通道name就能申请到,因为此处建立了slave map*/
	dma->filter.mapcnt = YD_DMA_CHANNEL_CNT;
	dma->filter.map = yd_dma_map;
	dma->filter.fn = yd_dma_filter_fn;


	ret = dma_async_device_register(dma);
	if (ret) {
		pci_err(pdev, "Failed to register dma device: %d\n", ret);
	}
	else{
		pci_set_drvdata(pdev, ydd);
		return 0;
	}

err_sw_dchan_init:
	pci_free_irq_vectors(pdev);
err_msi_vc_cnt:
	devm_kfree(dev, ydd->sw_chan);
err_sw_dchan_alloc:
	devm_kfree(dev, ydd);
	return ret;
}

static int yd_dma_probe(struct pci_dev *pdev,
			       const struct pci_device_id *id)
{
	int ret;

	ret = pcim_enable_device(pdev);
	if (ret)
	{
		pci_err(pdev, "pcim_enable_device failed\n");
		return ret;
	}


	pci_set_master(pdev);

	ret = yd_dma_create(pdev);

	if (ret)
	{
		pci_err(pdev, "yd DMA Channels Registered failed\n");
		return ret;
	}
	pci_info(pdev, "yd DMA Channels Registered\n");

	return ret;
}

static void yd_dma_remove(struct pci_dev *pdev)
{
	struct yd_dmac_dev *ydd	= pci_get_drvdata(pdev);
	struct device *dev 		= &ydd->pdev->dev;

	free_irq(ydd->irq, ydd);

    pci_free_irq_vectors(pdev);

    if(ydd)
	{
    	yd_dma_chan_release(ydd);
		//devm_kfree(dev, ydd->sw_chan);
    	dma_async_device_unregister(&ydd->dma);
		//devm_kfree(dev, ydd);
	}
    put_device(dev);
	cancel_work_sync(&ydd->cts_work);
    pci_info(pdev, "yd DMA Channels Unregistered\n");
}



static const struct pci_device_id yd_dma_ids[] = {
	{ YD_DMA_DEVICE_VENDOR, YD_DMA_DEVICE1_ID, 0x205e, 0x2005, 0, 0, 0 },
	{ YD_DMA_DEVICE_VENDOR, YD_DMA_DEVICE2_ID, 0x205e, 0x2005, 0, 0, 0 },
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
	.probe		= yd_dma_probe,
	.remove		= yd_dma_remove,
	.id_table	= yd_dma_ids,
};


module_pci_driver(yd_dma_pci_driver);
