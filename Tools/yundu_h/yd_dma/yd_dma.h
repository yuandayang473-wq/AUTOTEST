#ifndef __YD_EP_H
#define __YD_EP_H
#include <linux/pci.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/timer.h>
#include <asm/delay.h>
#include <linux/dmaengine.h>



typedef struct dma_ep_reg{
    uint32_t    DMA_EN_OFF_CH;                          /*0x100*/
    uint32_t    DMA_DOORBELL_OFF_CH;                    /*0x104*/
    uint32_t    DMA_ELEM_PF_OFF_CH;                     /*0x108*/
    uint32_t    DMA_HANDSHAKE_OFF_CH;                   /*0x10c*/
    uint32_t    DMA_LLP_LOW_OFF_CH;                     /*0x110*/
    uint32_t    DMA_LLP_HIGH_OFF_CH;                    /*0x114*/
    uint32_t    DMA_CYCLE_OFF_CH;                       /*0x118*/
    uint32_t    DMA_XFERSIZE_OFF_CH;                    /*0x11c*/
    uint32_t    DMA_SAR_LOW_OFF_CH;                     /*0x120*/
    uint32_t    DMA_SAR_HIGH_OFF_CH;                    /*0x124*/
    uint32_t    DMA_DAR_LOW_OFF_CH;                     /*0x128*/
    uint32_t    DMA_DAR_HIGH_OFF_CH;                    /*0x12c*/
    uint32_t    DMA_WATERMARK_EN_OFF_CH;                /*0x130*/
    uint32_t    DMA_CONTROL1_OFF_CH;                    /*0x134*/
    uint32_t    DMA_FUNC_NUM_OFF_CH;                    /*0x138*/
    uint32_t    DMA_QOS_OFF_CH;                         /*0x13c*/
    uint32_t    resv[16];
    uint32_t    DMA_STATUS_OFF_CH;                      /*0x180*/   /*###########*/
    uint32_t    DMA_INT_STATUS_OFF_CH;                  /*0x184*/
    uint32_t    DMA_INT_SETUP_OFF_CH;                   /*0x188*/
    uint32_t    DMA_INT_CLEAR_OFF_CH;                   /*0x18c*/
    uint32_t    DMA_MSI_STOP_LOW_OFF_CH;                /*0x190*/
    uint32_t    DMA_MSI_STOP_HIGH_OFF_CH;               /*0x194*/
    uint32_t    DMA_MSI_WATERMARK_LOW_OFF_CH;           /*0x198*/
    uint32_t    DMA_MSI_WATERMARK_HIGH_OFF_CH;          /*0x19c*/
    uint32_t    DMA_MSI_ABORT_LOW_OFF_CH;               /*0x1a0*/
    uint32_t    DMA_MSI_ABORT_HIGH_OFF_CH;              /*0x1a4*/
    uint32_t    DMA_MSI_MSGD_OFF_CH;                    /*0x1a8*/
}dma_ep_reg_t;
typedef struct dma_lli{
	uint32_t resv1;
	uint32_t src_addr_lo;
	uint32_t src_addr_hi;
	uint32_t dst_addr_lo;
	uint32_t dst_addr_hi;
	uint32_t lli_lo;
	uint32_t lli_hi;
	uint32_t resv2;
}dma_lli_t;


/*DMA_DOORBELL_OFF_CH_i*/
#define DMA_DOORBELL_STOP   (BIT(1))
#define DMA_DOORBELL_START  (BIT(0))

/*DMA_ELEM_PF_OFF_CH_i*/
#define DMA_ELEM_PF_BITS    (GENMASK(6 ,0))

/*DMA_CYCLE_OFF_CH_i*/
#define DMA_CYCLE_STATE(x)  ((x && BIT(1)) >> 1)
#define DMA_CYCLE_BIT(x)    (x && BIT(0))

/*DMA_WATERMARK_EN_OFF_CH_i*/
#define DMA_WATERMARK_LWIE_ENABLE   (BIT(1))
#define DMA_WATERMARK_RWIE_ENABLE   (BIT(0))

/*DMA_CONTROL1_OFF_CH_i*/
#define DMA_CONTROL1_ST         (GENMASK(26, 19))
#define DMA_CONTROL1_PH         (GENMASK(18, 17))
#define DMA_CONTROL1_TH         (BIT(16))
#define DMA_CONTROL1_AT         (GENMASK(6, 5))
#define DMA_CONTROL1_RO         (BIT(4))
#define DMA_CONTROL1_DST_SNOOP  (BIT(3))
#define DMA_CONTROL1_SRC_SNOOP  (BIT(2))
#define DMA_CONTROL1_MEM_TYPE   (BIT(1))
#define DMA_CONTROL1_LLEN       (BIT(0))

/*DMA_FUNC_NUM_OFF_CH_i*/
#define DMA_FUNC_NUM_VF         (GENMASK(24, 17))
#define DMA_FUNC_NUM_VF_EN      (BIT(16))
#define DMA_FUNC_NUM_PF         (GENMASK(4, 0))

/*DMA_QOS_OFF_CH_i*/
#define DMA_QOS_PF_DEPTH        (GENMASK(25, 16))
#define DMA_QOS_WEIGHT          (GENMASK(7, 3))
#define DMA_QOS_TC              (GENMASK(2, 0))

/*DMA_STATUS_OFF_CH_i*/
#define DMA_STATUS_MASK     (GENMASK(2, 0))
#define DMA_STATUS_RUNNING  (0x1)
#define DMA_STATUS_ABORTED  (0x2)
#define DMA_STATUS_STOPPED  (0x3)


/*DMA_INT_STATUS_OFF_CH_i about*/
#define DMA_INT_ERROR_STATUS        (GENMASK(6, 3))
#define DMA_INT_ABORT_STATUS        (BIT(2))
#define DMA_INT_WATERMARK_STATUS    (BIT(1))
#define DMA_INT_STOP_STATUS         (BIT(0))

/*DMA_INT_SETUP_OFF_CH_i*/
#define DMA_INT_ALL_MASK    DMA_INT_LAIE_ENABLE | \
                            DMA_INT_RAIE_ENABLE | \
                            DMA_INT_LSIE_ENABLE | \
                            DMA_INT_RSIE_ENABLE | \
                            DMA_INT_ABORT_MASK_ENABLE | \
                            DMA_INT_WATERMARK_MASK_ENABLE | \
                            DMA_INT_STOP_MASK_ENABLE

#define DMA_INT_INTX_MASK   DMA_INT_LAIE_ENABLE | \
                            DMA_INT_RAIE_ENABLE | \
                            DMA_INT_LSIE_ENABLE | \
                            DMA_INT_ABORT_MASK_ENABLE | \
                            DMA_INT_WATERMARK_MASK_ENABLE | \
                            DMA_INT_STOP_MASK_ENABLE

#define DMA_INT_LAIE_ENABLE             (BIT(6))
#define DMA_INT_RAIE_ENABLE             (BIT(5))
#define DMA_INT_LSIE_ENABLE             (BIT(4))
#define DMA_INT_RSIE_ENABLE             (BIT(3))
#define DMA_INT_ABORT_MASK_ENABLE       (BIT(2))
#define DMA_INT_WATERMARK_MASK_ENABLE   (BIT(1))
#define DMA_INT_STOP_MASK_ENABLE        (BIT(0))

/*DMA_INT_CLEAR_OFF_CH_i*/
#define DMA_INT_ALL_CLEAR       DMA_INT_ABORT_CLEAR | \
                                DMA_INT_WATERMARK_CLEAR | \
                                DMA_INT_STOP_CLEAR
#define DMA_INT_ABORT_CLEAR     (BIT(2))
#define DMA_INT_WATERMARK_CLEAR (BIT(1))
#define DMA_INT_STOP_CLEAR      (BIT(0))

#define DMA_MSI_CAP_DATA    (GENMASK(15, 0))

#define DMA_PAUSE_RESUME_RETRY 100

#define DMA_REG_ZERO   0x0

int cv_case1(unsigned long bar);
#endif
