#ifndef __YD_NTB_COMMON_H_
#define __YD_NTB_COMMON_H_

#include <linux/module.h>
#include <linux/delay.h>
#include <linux/kthread.h>
#include <linux/interrupt.h>
#include <linux/ntb.h>
#include <linux/list.h>
#include <linux/rbtree.h>
#include <linux/slab.h>
#include <linux/aer.h>

#include <linux/ntb.h>
#include <linux/pci.h>
#include <linux/version.h>
#include <asm/io.h>
#include <linux/mutex.h>

//#define MUL_DW_PACKET 1

#define DEBUG   1

#ifndef ioread64
#define ioread64 _ioread64
static inline uint64_t _ioread64(void __iomem *mmio)
{
    uint64_t low, high;

    low = ioread32(mmio);
    high = ioread32(mmio + sizeof(u32));
    return low | (high << 32);
}
#endif

#ifndef iowrite64
#define iowrite64 _iowrite64
static inline void _iowrite64(uint64_t val, void __iomem *mmio)
{
    iowrite32(val, mmio);
    iowrite32(val >> 32, mmio + sizeof(uint32_t));
}
#endif
enum yd_mem_type {
    YD_ADDR_TYPE_32 = 0,
    YD_ADDR_TYPE_64,
};



#define NTF_MSG_MAX_LEN (8 * sizeof(uint32_t))




/*88888888888888888888*/

#define YD_MAX_STATION_ID  9
#define YD_MAX_ORG_CNT  16



#define YD_MAX_PIPE_CNT   32
#define YD_IBMSG_DATA_CNT   8

#define YD_LUT_ENTRY_CNT    32
#define YD_DIR_STATION_CNT  16
#define YD_ORG_ENTRY_NUM 256
/*------------------------------------------------------*/
typedef union {
    uint32_t value;
    struct {
        uint32_t NTB_en                         : 9;        /*0b0*/
        uint32_t                                : 8;
        uint32_t NTB_dev_num                    : 5;        /*0b17*/
        uint32_t ntb_dspep_bus_master_func_en   : 1;        /*0b22*/
        uint32_t nt_rx_incid_discard_func_en    : 1;        /*0b23*/
        uint32_t                                : 1;
        uint32_t cfg_ecrc_thr                   : 1;        /*0b25*/
        uint32_t                                : 3;
        uint32_t dbg0_en                        : 1;        /*0b29*/
        uint32_t dbg1_en                        : 1;        /*0b30*/
        uint32_t                                : 1;
    };
}group0_t; /*0x0*/


typedef union {
    uint32_t value;
    struct {
        uint32_t ORG_reqID  : 16;
        uint32_t Entry      : 8;
        uint32_t LID_v      : 1;
        uint32_t            : 7;
    };
}org_req_id_regs_t;

typedef union {
    struct {
        org_req_id_regs_t ori_regs[YD_ORG_ENTRY_NUM];
    };
}group1_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t tx_mdtlp_ecrc_thr      : 1;
        uint32_t rx_mdtlp_ecrc_thr      : 1;
        uint32_t                        : 30;
    };
}group0_roext_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t dsp_mode_en        : 1;
        uint32_t                    : 31;
    };
}group0_fabric_t;


typedef union{
    uint32_t value;
    struct{
        uint32_t                    : 5;
        uint32_t LUT_EN             : 1;
        uint32_t LUT_TD_base_L      : 26;
        uint32_t LUT_TD_base_H      : 26;
        uint32_t LUT_D_SID          : 4;
        uint32_t                    : 2;
    };
}yd_lut_entry_regs_t;

typedef union {
    struct {
        uint32_t LUT_UTD_base;      /*0x100*/
        uint32_t LUT_UTD_base_up;   /*0x104*/
        uint32_t LUT_fix_offset;    /*0x108*/ 
        yd_lut_entry_regs_t entrys[YD_LUT_ENTRY_CNT];   /*0x10c*/
    };
}group3_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t DIR_UTD_base;
        uint32_t DIR_UTD_base_up;
    };
}yd_dir_utd_base_regs_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t DIR_UTD_limit;
        uint32_t DIR_UTD_limit_up;
    };
}yd_dir_utd_limit_regs_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t DIR_TD_base_L;
        uint32_t DIR_TD_base_H;
    };
}yd_dir_td_base_t;

typedef union {
    struct {
        yd_dir_utd_base_regs_t dir_utd_base[YD_DIR_STATION_CNT];
        //uint32_t resv0[12];
        yd_dir_utd_limit_regs_t dir_utd_limit[YD_DIR_STATION_CNT];
        //uint32_t resv1[12];
        yd_dir_td_base_t dir_td_base[YD_DIR_STATION_CNT];
    };

}group4_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t obmsg;
    };
}yd_obmsg_field_t;

typedef union {
    uint32_t value;
    struct {
        yd_obmsg_field_t obmsg_field[YD_MAX_ORG_CNT][YD_MAX_PIPE_CNT];
        
    };
}group5_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t ibmsg;
    };
}yd_ibmsg_field_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t    ibmsg0_valid    : 1;
        uint32_t                    : 7;
        uint32_t    ibmsg1_valid    : 1;
        uint32_t                    : 7; 
        uint32_t    ibmsg2_valid    : 1;
        uint32_t                    : 7;
        uint32_t    ibmsg3_valid    : 1;
        uint32_t                    : 7;
    };
}yd_ibmsg_valid_field_t;

#define YD_NTB_IBMSG_GROUP_NUM  8
/*group 6*/
#define YD_NTB_ALL_STATION_CNT  16
typedef union {
    uint32_t value;

    struct {
        yd_ibmsg_field_t ibmsg_field[YD_NTB_ALL_STATION_CNT][YD_MAX_PIPE_CNT];
        uint32_t resv0[256];
        yd_ibmsg_valid_field_t ibmsg_valid_field[YD_NTB_ALL_STATION_CNT][YD_NTB_IBMSG_GROUP_NUM];
    };
    
}group6_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t            : 8;
        uint32_t odb1       : 1;
        uint32_t            : 7;
        uint32_t odb2       : 1;
        uint32_t            : 7;
        uint32_t odb3       : 1;
        uint32_t            : 7;
    };
}yd_odb_regs_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t idb0       : 1;
        uint32_t            : 7;
        uint32_t idb1       : 1;
        uint32_t            : 7;
        uint32_t idb2       : 1;
        uint32_t            : 7;
        uint32_t idb3       : 1;
        uint32_t            : 7;
    };
}yd_idb_regs_t;

typedef union {
    uint32_t value;
    struct {
        yd_odb_regs_t odb_regs[YD_MAX_ORG_CNT];
        uint32_t resv0[48];
        yd_idb_regs_t idb_regs[YD_MAX_ORG_CNT];
    };

}group7_t;

typedef union {
    uint32_t value;
    struct {
	    uint32_t GID_BN                  : 8;
	    uint32_t GID_DF_base             : 8;
	    uint32_t GID_DF_limit            : 8;
	    uint32_t GID_dsp_bus_master_en   : 1;
	    uint32_t GID_ep_bus_master_en    : 1;
	    uint32_t                         : 6;
    };
}yd_station_cfg_t;
#define YD_NTB_GROUP8_MAX_CFG   16
typedef union {
    uint32_t value;
    struct {
        yd_station_cfg_t station_cfg[YD_NTB_GROUP8_MAX_CFG];
    };
}group8_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t NT_RSV_RW_B0       : 8;
        uint32_t NT_RSV_RW_B1       : 8;
        uint32_t NT_RSV_RW_B2       : 8;
        uint32_t NT_RSV_RW_B3       : 8;
        uint32_t resv0[5];
        uint32_t dw0_b0_hw_wr_en    : 1;
        uint32_t dw0_b1_hw_wr_en    : 1;
        uint32_t dw0_b2_hw_wr_en    : 1;
        uint32_t dw0_b3_hw_wr_en    : 1;
        uint32_t dw1_b0_hw_wr_en    : 1;
        uint32_t dw1_b1_hw_wr_en    : 1;
        uint32_t dw1_b2_hw_wr_en    : 1;
        uint32_t dw1_b3_hw_wr_en    : 1;
        uint32_t                    : 24;

    };
}group9_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t NT_RSV_RO;
    };
}group10_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t nt_rcv_io_cnt      : 8;
        uint32_t nt_rcv_at_miss_cnt : 8;
        uint32_t nt_cfg1_miss_cnt    : 8;
        uint32_t nt_ur_hit_cnt      : 8;
    };
}group11_sts0_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t NT_req_reqID_miss_cnt  : 8;
        uint32_t NT_cpl_reqID_miss_cnt  : 8;
        uint32_t NT_NTMSG_inv_cnt       : 8;
        uint32_t NT_TXCPL_invdid_cnt    : 8;
    };
}group11_sts1_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t NT_Rcv_io_msk                      : 1;    //0
        uint32_t NT_Rcv_AT_miss_msk                 : 1;    //1
        uint32_t NT_CFG1_miss_msk                   : 1;    //2
        uint32_t NT_UR_hit_msk                      : 1;    //3
        uint32_t NT_req_reqID_miss_msk              : 1;    //4
        uint32_t NT_cpl_reqID_miss_msk              : 1;    //5
        uint32_t NT_NTMSG_inv_msk                   : 1;    //6
        uint32_t NT_TXCPL_invdid_msk                : 1;    //7
        uint32_t NT_DSP_UDT_msk                     : 1;    //8
        uint32_t NT_TXECRC_int_msk                  : 1;    //9
        uint32_t NT_RXECRC_int_msk                  : 1;    //10
        uint32_t NTBINT_err_int_msk                 : 1;    //11
        uint32_t NT_tx_redsop_msk                   : 1;    //12
        uint32_t NT_tx_redeop_msk                   : 1;    //13
        uint32_t NT_tx_invphase_msk                 : 1;    //14
        uint32_t NT_rx_redsop_msk                   : 1;    //15
        uint32_t NT_rx_redeop_msk                   : 1;    //16
        uint32_t NT_rx_invphase_msk                 : 1;    //17
        uint32_t NT_rx_invid_msk                    : 1;    //18
        uint32_t NT_rx_eop_miss_msk                 : 1;    //19
        uint32_t NT_rx_eop_fail_msk                 : 1;    //20
        uint32_t                                    : 3;
        uint32_t ntmsg_rxram_ecc_corr_int_msk       : 1;    //24
        uint32_t ntmsg_rxram_ecc_ucorr_int_msk      : 1;    //25
        uint32_t ntcpl_rxram_ecc_corr_int_msk       : 1;    //26
        uint32_t ntcpl_rxram_ecc_ucorr_int_msk      : 1;    //27
        uint32_t nt_dsp_bmen_udt_int_msk            : 1;    //28
        uint32_t nt_ep_bmen_udt_int_msk             : 1;    //29
        uint32_t NT_RXMSG_inv_msk                   : 1;    //30
        uint32_t nt_2nd_rst_udt_int_msk             : 1;    //31
    };
}group11_mask_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t NT_DSP_UDT_sts     : 1;
        uint32_t                    : 7;
        uint32_t nt_rxmsg_inv_cnt   : 8;
        uint32_t nt_2nd_rst_udt_sts : 1;
        uint32_t nt_cfg0_miss_cnt   : 8;
        uint32_t                    : 7;
    };
}group12_msgsts1_1_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t nt_tx_redsop_cnt   : 8;    /*0xc48*/
        uint32_t nt_tx_redeop_cnt   : 8;
        uint32_t nt_tx_invphase_cnt : 8;
        uint32_t nt_rx_redsop_cnt   : 8;
    };
}group12_tlpexp0_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t nt_rx_redeop_cnt   : 8;    /*0xc4c*/
        uint32_t nt_rx_invphase_cnt : 8;
        uint32_t nt_rx_eop_miss_cnt : 8;
        uint32_t                    : 8;
    };
}group12_tlpexp1_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t nt_dsp_bme_udt_sts : 1;    /*0xc50*/
        uint32_t                    : 7;
        uint32_t nt_ep_bme_udt_sts  : 1;
        uint32_t                    : 23;
    };
}group12_bmen_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_unlock                 : 1;
        uint32_t                            : 7;
        uint32_t MSG_INVREQ                 : 1;
        uint32_t                            : 7;
        uint32_t MSG_INVCPL                 : 1;
        uint32_t                            : 7;
        uint32_t MSG_PageREQ                : 1;
        uint32_t                            : 7;
    };
}group12_msgsts0_t;

#define YD_NTB_GROUP12_MSGSTS1  0xce4
typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_PRG_RSP                : 1;
        uint32_t                            : 7;
        uint32_t MSG_LTR                    : 1;
        uint32_t                            : 7;
        uint32_t MSG_OBFF                   : 1;
        uint32_t                            : 7;
        uint32_t MSG_PMNAK                  : 1;
        uint32_t                            : 7;
    };
}group12_msgsts1_t;

#define YD_NTB_GROUP12_MSGSTS2  0xce8
typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_PMPME                  : 1;
        uint32_t                            : 7;
        uint32_t MSG_PMTURNOFF              : 1;
        uint32_t                            : 7;
        uint32_t MSG_PMTOACK                : 1;
        uint32_t                            : 7;
        uint32_t MSG_assert_INTA            : 1;
        uint32_t                            : 7;
    };
}group12_msgsts2_t;

#define YD_NTB_GROUP12_MSGSTS3  0xcec
typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_assert_INTB            : 1;
        uint32_t                            : 7;
        uint32_t MSG_assert_INTC            : 1;
        uint32_t                            : 7;
        uint32_t MSG_assert_INTD            : 1;
        uint32_t                            : 7;
        uint32_t MSG_deassert_INTA          : 1;
        uint32_t                            : 7;
    };
}group12_msgsts3_t;

#define YD_NTB_GROUP12_MSGSTS4  0xcf0
typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_deassert_INTB          : 1;
        uint32_t                            : 7;
        uint32_t MSG_deassert_INTC          : 1;
        uint32_t                            : 7;
        uint32_t MSG_deassert_INTD          : 1;
        uint32_t                            : 7;
        uint32_t MSG_ERR_COR                : 1;
        uint32_t                            : 7;
    };
}group12_msgsts4_t;

#define YD_NTB_GROUP12_MSGSTS5  0xcf4
typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_ERR_NONFATAL           : 1;
        uint32_t                            : 7;
        uint32_t MSG_ERR_FATAL              : 1;
        uint32_t                            : 7;
        uint32_t MSG_IGNORE0                : 1;
        uint32_t                            : 7;
        uint32_t MSG_IGNORE1                : 1;
        uint32_t                            : 7;
    };
}group12_msgsts5_t;

#define YD_NTB_GROUP12_MSGSTS6  0xcf8
typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_IGNORE3                : 1;
        uint32_t                            : 7;
        uint32_t MSG_IGNORE4                : 1;
        uint32_t                            : 7;
        uint32_t MSG_IGNORE5                : 1;
        uint32_t                            : 7;
        uint32_t MSG_IGNORE7                : 1;
        uint32_t                            : 7;
    };
}group12_msgsts6_t;

#define YD_NTB_GROUP12_MSGSTS7  0xcfc
typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_IGNORE8                : 1;
        uint32_t                            : 7;
        uint32_t MSG_SS_POWLIMIT            : 1;
        uint32_t                            : 7;
        uint32_t MSG_PTMREQ                 : 1;
        uint32_t                            : 7;
        uint32_t MSG_PTMRSP                 : 1;
        uint32_t                            : 7;
    };
}group12_msgsts7_t;

#define YD_NTB_GROUP12_MSGSTS8  0xd00
typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_VDM_type0              : 1;
        uint32_t                            : 7;
        uint32_t MSG_VDM_type1              : 1;
        uint32_t                            : 23;  
    }; 
}group12_msgsts8_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_unlock_msk                     : 1; //0
        uint32_t MSG_INVREQ_msk                     : 1; //1
        uint32_t MSG_INVCPL_msk                     : 1; //2
        uint32_t MSG_PageREQ_msk                    : 1; //3
        uint32_t MSG_PRG_RSP_msk                    : 1; //4
        uint32_t MSG_LTR_msk                        : 1; //5
        uint32_t MSG_OBFF_msk                       : 1; //6
        uint32_t MSG_PMNAK_msk                      : 1; //7
        uint32_t MSG_PMPME_msk                      : 1; //8
        uint32_t MSG_PMTURNOFF_msk                  : 1; //9
        uint32_t MSG_PMTOACK_msk                    : 1; //10
        uint32_t MSG_assert_INTA_msk                : 1; //11
        uint32_t MSG_assert_INTB_msk                : 1; //12
        uint32_t MSG_assert_INTC_msk                : 1; //13
        uint32_t MSG_assert_INTD_msk                : 1; //14
        uint32_t MSG_deassert_INTA_msk              : 1; //15
        uint32_t MSG_deassert_INTB_msk              : 1; //16
        uint32_t MSG_deassert_INTC_msk              : 1; //17
        uint32_t MSG_deassert_INTD_msk              : 1; //18
        uint32_t MSG_ERR_COR_msk                    : 1; //19
        uint32_t MSG_ERR_NONFATAL_msk               : 1; //20
        uint32_t MSG_ERR_FATAL_msk                  : 1; //21
        uint32_t MSG_IGNORE0_msk                    : 1; //22
        uint32_t MSG_IGNORE1_msk                    : 1; //23
        uint32_t MSG_IGNORE3_msk                    : 1; //24
        uint32_t MSG_IGNORE4_msk                    : 1; //25
        uint32_t MSG_IGNORE5_msk                    : 1; //26
        uint32_t MSG_IGNORE7_msk                    : 1; //27
        uint32_t MSG_IGNORE8_msk                    : 1; //28
        uint32_t                                    : 3; 
    };
}group12_msgmask0_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_SS_POWLIMIT_msk                : 1; //0
        uint32_t MSG_PTMREQ_msk                     : 1; //1
        uint32_t MSG_PTMRSP_msk                     : 1; //2
        uint32_t MSG_VDM_type0_msk                  : 1; //3
        uint32_t MSG_VDM_type1_msk                  : 1; //4
        uint32_t NTBINT_sii_int_msk                 : 1; //5
        uint32_t ntb_illegal_tlptype_msk            : 1; //6
        uint32_t ntb_illegal_msg_msk                : 1; //7
        uint32_t ntb_crsbdry_msk                    : 1; //8
        uint32_t ntb_dsp_txovsize_msk               : 1; //9
        uint32_t ntb_dsp_rxovsize_msk               : 1; //10
        uint32_t ntb_ep_txovsize_msk                : 1; //11
        uint32_t ntb_ep_rxovsize_msk                : 1; //12
        uint32_t ntb_dsp_msen_wr_msk                : 1; //13
        uint32_t ntb_dsp_msen_rd_msk                : 1; //14
        uint32_t ntb_ep_msen_wr_msk                 : 1; //15
        uint32_t ntb_ep_msen_rd_msk                 : 1; //16
        uint32_t ntb_dsp_win_miss_wr_msk            : 1; //17
        uint32_t ntb_dsp_win_miss_rd_msk            : 1; //18
        uint32_t ntb_ep_bar_miss_wr_msk             : 1; //19
        uint32_t ntb_ep_bar_miss_rd_msk             : 1; //20
        uint32_t                                    : 11;
    };
}group12_msgmask1_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t iep_sts_b8_mst_data_perr               : 1; //0
        uint32_t iep_sts_b11_signaled_tgt_abort         : 1; //1
        uint32_t iep_sts_b12_rcv_tgt_abort              : 1; //2
        uint32_t iep_sts_b13_rcv_mst_abort              : 1; //3
        uint32_t iep_sts_b14_signaled_serr              : 1; //4
        uint32_t iep_sts_b15_det_perr                   : 1; //5
        uint32_t iep_dsr_b0_corr_err_det                : 1; //6
        uint32_t iep_dsr_b1_nf_err_det                  : 1; //7
        uint32_t iep_dsr_b2_f_err_det                   : 1; //8
        uint32_t iep_dsr_b3_unsupt_req_det              : 1; //9
        uint32_t iep_aer_ce_status                      : 1; //10
        uint32_t iep_aer_uce_status                     : 1; //11
        uint32_t idsp_sts_b8_mst_data_perr              : 1; //12
        uint32_t idsp_sts_b11_signaled_tgt_abort        : 1; //13
        uint32_t idsp_sts_b12_rcv_tgt_abort             : 1; //14
        uint32_t idsp_sts_b13_rcv_mst_abort             : 1; //15
        uint32_t idsp_sts_b14_signaled_serr             : 1; //16
        uint32_t idsp_sts_b15_det_perr                  : 1; //17
        uint32_t idsp_dsr_b0_corr_err_det               : 1; //18
        uint32_t idsp_dsr_b1_nf_err_det                 : 1; //19
        uint32_t idsp_dsr_b2_f_err_det                  : 1; //20
        uint32_t idsp_dsr_b3_unsupt_req_det             : 1; //21
        uint32_t idsp_secsts_b8_mst_data_perr           : 1; //22
        uint32_t idsp_secsts_b11_signaled_tgt_abort     : 1; //23
        uint32_t idsp_secsts_b12_rcv_tgt_abort          : 1; //24
        uint32_t idsp_secsts_b13_rcv_mst_abort          : 1; //25
        uint32_t idsp_secsts_b14_signaled_serr          : 1; //26
        uint32_t idsp_secsts_b15_det_perr               : 1; //27
        uint32_t                                        : 4;

    };
}hostclrsts_int_msk_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_ERR_CNT            : 8;
        uint32_t                        : 24;
    };
}group12_cnt1_t; /*0xd10*/


typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_ERR_1STHEAD_DW0_B0         : 8;
        uint32_t MSG_ERR_1STHEAD_DW0_B1         : 8;
        uint32_t MSG_ERR_1STHEAD_DW0_B2         : 8;
        uint32_t MSG_ERR_1STHEAD_DW0_B3         : 8;
    };
}group12_head4_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_ERR_1STHEAD_DW1_B0         : 8;
        uint32_t MSG_ERR_1STHEAD_DW1_B1         : 8;
        uint32_t MSG_ERR_1STHEAD_DW1_B2         : 8;
        uint32_t MSG_ERR_1STHEAD_DW1_B3         : 8;
    };
}group12_head5_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_ERR_1STHEAD_DW2_B0         : 8;
        uint32_t MSG_ERR_1STHEAD_DW2_B1         : 8;
        uint32_t MSG_ERR_1STHEAD_DW2_B2         : 8;
        uint32_t MSG_ERR_1STHEAD_DW2_B3         : 8;
    };
}group12_head6_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t MSG_ERR_1STHEAD_DW3_B0         : 8;
        uint32_t MSG_ERR_1STHEAD_DW3_B1         : 8;
        uint32_t MSG_ERR_1STHEAD_DW3_B2         : 8;
        uint32_t MSG_ERR_1STHEAD_DW3_B3         : 8;
    };
}group12_head7_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t TX_ECRC_MNGERR_CNT             : 8;
        uint32_t RX_ECRC_MNGERR_CNT             : 8;
        uint32_t TX_ECRC_MNGERRMISS_CNT         : 8;
        uint32_t RX_ECRC_MNGERRMISS_CNT         : 8;
    };
}group12_cnt2_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW0_B0      :8;
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW0_B1      :8;
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW0_B2      :8;
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW0_B3      :8;
    };
}group12_head8_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW1_B0      :8;
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW1_B1      :8;
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW1_B2      :8;
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW1_B3      :8;
    };
}group12_head9_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW2_B0      :8;
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW2_B1      :8;
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW2_B2      :8;
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW2_B3      :8;
    };
}group12_head10_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW3_B0      :8;
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW3_B1      :8;
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW3_B2      :8;
        uint32_t TX_ECRC_MNGERR_1STHEAD_DW3_B3      :8;
    };
}group12_head11_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW0_B0      :8;
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW0_B1      :8;
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW0_B2      :8;
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW0_B3      :8;
    };
}group12_head12_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW1_B0      :8;
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW1_B1      :8;
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW1_B2      :8;
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW1_B3      :8;
    };
}group12_head13_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW2_B0      :8;
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW2_B1      :8;
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW2_B2      :8;
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW2_B3      :8;
    };
}group12_head14_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW3_B0      :8;
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW3_B1      :8;
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW3_B2      :8;
        uint32_t TX_ECRC_MNGERRMISS_1STHEAD_DW3_B3      :8;
    };
}group12_head15_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t NT_RX_INVID_cnt        : 8;
        uint32_t                        : 24;
    };
}group12_cnt3_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t NT_RX_INVID_INFO_B0    : 8;
        uint32_t NT_RX_INVID_INFO_B1    : 8;
        uint32_t NT_RX_INVID_INFO_B2    : 8;
        uint32_t NT_RX_INVID_INFO_B3    : 8;
    };
}group12_info3_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t NT_RX_INVID_1STHEAD_DW0_B0 : 8;
        uint32_t NT_RX_INVID_1STHEAD_DW0_B1 : 8;
        uint32_t NT_RX_INVID_1STHEAD_DW0_B2 : 8;
        uint32_t NT_RX_INVID_1STHEAD_DW0_B3 : 8;
    };
}group12_head16_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t NT_RX_INVID_1STHEAD_DW1_B0 : 8;
        uint32_t NT_RX_INVID_1STHEAD_DW1_B1 : 8;
        uint32_t NT_RX_INVID_1STHEAD_DW1_B2 : 8;
        uint32_t NT_RX_INVID_1STHEAD_DW1_B3 : 8;
    };
}group12_head17_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t NT_RX_INVID_1STHEAD_DW2_B0 : 8;
        uint32_t NT_RX_INVID_1STHEAD_DW2_B1 : 8;
        uint32_t NT_RX_INVID_1STHEAD_DW2_B2 : 8;
        uint32_t NT_RX_INVID_1STHEAD_DW2_B3 : 8;
    };
}group12_head18_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t NT_RX_INVID_1STHEAD_DW3_B0 : 8;
        uint32_t NT_RX_INVID_1STHEAD_DW3_B1 : 8;
        uint32_t NT_RX_INVID_1STHEAD_DW3_B2 : 8;
        uint32_t NT_RX_INVID_1STHEAD_DW3_B3 : 8;
    };
}group12_head19_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb2cb_txram_ecc_corr_cnt_B0   : 8;
        uint32_t ntb2cb_txram_ecc_corr_cnt_B1   : 8;
        uint32_t ntb2cb_txram_ecc_corr_cnt_B2   : 8;
        uint32_t                                : 8;
        
    };
}group12_ecc0_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb2cb_txram_ecc_ucorr_cnt   : 8;
        uint32_t                              : 24;
    };
}group12_ecc1_t;



typedef union {
    uint32_t value;
    struct {
        uint32_t cb2ntb_rxram_ecc_corr_cnt_B0   : 8;
        uint32_t cb2ntb_rxram_ecc_corr_cnt_B1   : 8;
        uint32_t cb2ntb_rxram_ecc_corr_cnt_B2   : 8;
        uint32_t                                : 8;
    };
}group12_ecc2_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t cb2ntb_rxram_ecc_ucorr_cnt   : 8;
        uint32_t                              : 24;
    };
}group12_ecc3_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntmsg_rxram_ecc_corr_cnt_B0    : 8;
        uint32_t ntmsg_rxram_ecc_corr_cnt_B1    : 8;
        uint32_t ntmsg_rxram_ecc_corr_cnt_B2    : 8;
        uint32_t                                : 8;
    };
}group12_ecc4_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntmsg_rxram_ecc_ucorr_cnt      : 8;
        uint32_t                                : 24;
    };
}group12_ecc5_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntcpl_rxram_ecc_corr_cnt_B0    : 8;
        uint32_t ntcpl_rxram_ecc_corr_cnt_B1    : 8;
        uint32_t ntcpl_rxram_ecc_corr_cnt_B2    : 8;
        uint32_t                                : 8;
    };
}group12_ecc6_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntcpl_rxram_ecc_ucorr_cnt   : 8;
        uint32_t                             : 24;
        
    };
}group12_ecc7_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t NT_rx_eop_fail_cnt     : 8;
        uint32_t                        : 24;
    };
}group12_cnt4_t;


typedef union {
    uint32_t value;
    struct{
        uint32_t NT_RX_eopfail_1STHEAD_DW0_B0       : 8;
        uint32_t NT_RX_eopfail_1STHEAD_DW0_B1       : 8;
        uint32_t NT_RX_eopfail_1STHEAD_DW0_B2       : 8;
        uint32_t NT_RX_eopfail_1STHEAD_DW0_B3       : 8;
    };
}group12_head20_t;

typedef union {
    uint32_t value;
    struct{
        uint32_t NT_RX_eopfail_1STHEAD_DW1_B0       : 8;
        uint32_t NT_RX_eopfail_1STHEAD_DW1_B1       : 8;
        uint32_t NT_RX_eopfail_1STHEAD_DW1_B2       : 8;
        uint32_t NT_RX_eopfail_1STHEAD_DW1_B3       : 8;
    };
}group12_head21_t;

typedef union {
    uint32_t value;
    struct{
        uint32_t NT_RX_eopfail_1STHEAD_DW2_B0       : 8;
        uint32_t NT_RX_eopfail_1STHEAD_DW2_B1       : 8;
        uint32_t NT_RX_eopfail_1STHEAD_DW2_B2       : 8;
        uint32_t NT_RX_eopfail_1STHEAD_DW2_B3       : 8;
    };
}group12_head22_t;

typedef union {
    uint32_t value;
    struct{
        uint32_t NT_RX_eopfail_1STHEAD_DW3_B0       : 8;
        uint32_t NT_RX_eopfail_1STHEAD_DW3_B1       : 8;
        uint32_t NT_RX_eopfail_1STHEAD_DW3_B2       : 8;
        uint32_t NT_RX_eopfail_1STHEAD_DW3_B3       : 8;
    };
}group12_head23_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t nt_txib_hit_cnt            : 8;
        uint32_t nt_txbar0_outof_range_cnt  : 8;
        uint32_t nt_txbar0_plinv_cnt        : 8;
        uint32_t nt_txlut_inv_cnt           : 8;
    };
}group11_sts2_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t nt_txdir_inv_cnt           : 8;
        uint32_t                            : 24;
    };
}group11_sts3_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t nt_txib_hit_msk                    : 1; //0
        uint32_t nt_txbar0_outof_range_msk          : 1; //1
        uint32_t nt_txbar0_plinv_msk                : 1; //2
        uint32_t nt_txlut_inv_msk                   : 1; //3
        uint32_t nt_txdir_inv_msk                   : 1; //4
        uint32_t nt_tx_poisonwr_hit_msk             : 1; //5
        uint32_t nt_rx_poisonwr_hit_msk             : 1; //6
        uint32_t nt_tx_cplabort_hit_msk             : 1; //7
        uint32_t nt_tx_poisoncpl_hit_msk            : 1; //8
        uint32_t nt_rx_poisoncpl_hit_msk            : 1; //9
        uint32_t nt_rx_cplabort_hit_msk             : 1; //10
        uint32_t nt_tx_bme_miss_msk                 : 1; //11
        uint32_t ntb_dsptxcfg_fmtfail_msk           : 1; //12
        uint32_t ntb_eptxcfg_fmtfail_msk            : 1; //13
        uint32_t ntb_txbar0_fmtfail_msk             : 1; //14
        uint32_t NT_CFG0_miss_msk                   : 1; //15
        uint32_t nt_tx_poisoncfgw0_hit_msk          : 1; //16
        uint32_t nt_tx_poisoncfgr0_hit_msk          : 1; //17
        uint32_t nt_tx_poisoncfgw1_hit_msk          : 1; //18
        uint32_t nt_tx_poisoncfgr1_hit_msk          : 1; //19
        uint32_t nt_tx_poisonwr0_hit_msk            : 1; //20
        uint32_t nt_tx_poisonrd0_hit_msk            : 1; //21
        uint32_t nt_tx_poisonwr2_hit_msk            : 1; //22
        uint32_t nt_tx_poisonrd2_hit_msk            : 1; //23
        uint32_t nt_tx_poisonmsg_hit_msk            : 1; //24
        uint32_t nt_tx_poisonplgl_hit_msk           : 1; //25
        uint32_t                                    : 6;
    };
}group11_mask_new_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t NT_ERR_1STHEAD_DW0_B0              : 8;
        uint32_t NT_ERR_1STHEAD_DW0_B1              : 8;
        uint32_t NT_ERR_1STHEAD_DW0_B2              : 8;
        uint32_t NT_ERR_1STHEAD_DW0_B3              : 8;
    };
}group11_head0_t; /*db0*/

typedef union {
    uint32_t value;
    struct {
        uint32_t NT_ERR_1STHEAD_DW1_B0              : 8;
        uint32_t NT_ERR_1STHEAD_DW1_B1              : 8;
        uint32_t NT_ERR_1STHEAD_DW1_B2              : 8;
        uint32_t NT_ERR_1STHEAD_DW1_B3              : 8;
    };
}group11_head1_t; /*e04*/

typedef union {
    uint32_t value;
    struct {
        uint32_t NT_ERR_1STHEAD_DW0_B0              : 8;
        uint32_t NT_ERR_1STHEAD_DW0_B1              : 8;
        uint32_t NT_ERR_1STHEAD_DW0_B2              : 8;
        uint32_t NT_ERR_1STHEAD_DW0_B3              : 8;
    };
}group11_head2_t; /*e58*/

typedef union {
    uint32_t value;
    struct {
        uint32_t NT_ERR_1STHEAD_DW3_B0              : 8;
        uint32_t NT_ERR_1STHEAD_DW3_B1              : 8;
        uint32_t NT_ERR_1STHEAD_DW3_B2              : 8;
        uint32_t NT_ERR_1STHEAD_DW3_B3              : 8;
    };
}group11_head3_t; /*eac*/


typedef union {
    uint32_t value;
    struct {
        uint32_t TXARB_GNT_B0       : 8;
        uint32_t TXARB_GNT_B1       : 8;
        uint32_t TXARB_GNT_B2       : 8;
        uint32_t TXARB_GNT_B3       : 8;

    };
}group13_f0_t; /*0x1000*/

typedef union {
    uint32_t value;
    struct {
        uint32_t RXARB_GNT_L_B0       : 8;
        uint32_t RXARB_GNT_L_B1       : 8;
        uint32_t RXARB_GNT_L_B2       : 8;
        uint32_t RXARB_GNT_L_B03       : 8;

    };
}group13_f1_t;  /*0x1004*/

typedef union {
    uint32_t value;
    struct {
        uint32_t RXARB_GNT_H_B0       : 8;
        uint32_t RXARB_GNT_H_B1       : 8;
        uint32_t RXARB_GNT_H_B2       : 8;
        uint32_t RXARB_GNT_H_B3       : 8;

    };
}group13_f2_t; /*0x1008*/

typedef union {
    uint32_t value;
    struct {
        uint32_t DBGSEL0;
    
    };
}group13_f3_t; /*0x100c*/

typedef union {
    uint32_t value;
    struct {
        uint32_t DBGSEL1;
       
    };
}group13_f4_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t MEMCFGARB_GNT;
       
    };
}group13_f5_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t                                : 16;
        uint32_t ntmsg_rxram_ras_correct        : 1;
        uint32_t                                : 7;
        uint32_t ntcpl_rxram_ras_correct        : 1;
        uint32_t                                : 7;

    };
}group13_f6_t;



typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_CNT        : 8;
        uint32_t ECRC_EPERR_CNT         : 8;
        uint32_t                        : 16;
    };
}group12_cnt5_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_illegal_tlptype_cnt    : 8;
        uint32_t ntb_illegal_ecrc_cnt       : 8;
        uint32_t ntb_illegal_length_cnt     : 8;
        uint32_t ntb_illegal_msg_cnt        : 8;
    };
}group12_mlf0_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_crsbdry_cnt            : 8;
        uint32_t                            : 24;
    };
}group12_mlf1_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_dsp_tx_ovsize_cnt      : 2;
        uint32_t                            : 6;
        uint32_t ntb_dsp_rx_ovsize_cnt      : 2;
        uint32_t                            : 6;
        uint32_t ntb_ep_tx_ovsize_cnt       : 2;
        uint32_t                            : 6;
        uint32_t ntb_ep_rx_ovsize_cnt       : 2;
        uint32_t                            : 6;
    };
}group12_mlf2_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_dsp_msen_wr_cnt        : 2;
        uint32_t                            : 6;
        uint32_t ntb_dsp_msen_rd_cnt        : 2;
        uint32_t                            : 6;
        uint32_t ntb_ep_msen_wr_cnt         : 2;
        uint32_t                            : 6;
        uint32_t ntb_ep_msen_rd_cnt         : 2;
        uint32_t                            : 6;
    };
}group12_sts0_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_dsp_win_miss_wr_cnt    : 2;
        uint32_t                            : 6;
        uint32_t ntb_dsp_win_miss_rd_cnt    : 2;
        uint32_t                            : 6;
        uint32_t ntb_ep_bar_miss_wr_cnt     : 2;
        uint32_t                            : 6;
        uint32_t ntb_ep_bar_miss_rd_cnt     : 2;
        uint32_t                            : 6;
    };
}group12_sts1_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_eptxcfg_fmtfail_sts            : 1;    /*0*/
        uint32_t ntb_txbar0_fmtfail_sts             : 1;    /*1*/
        uint32_t nt_cfg1_miss_sts                   : 1;    /*2*/
        uint32_t ntb_illegal_tlptype_sts            : 1;    /*3*/
        //uint32_t ntb_illegal_ecrc_sts               : 1;    /*4*/             DE 20240717版本删除了这些寄存器
        //uint32_t ntb_illegal_length_sts             : 1;    /*5*/
        uint32_t ntb_illegal_msg_sts                : 1;    /*4*/
        uint32_t ntb_crsbdry_sts                    : 1;    /*5*/
        //uint32_t ntb_dsp_txovsize_sts               : 1;    /*8*/
        //uint32_t ntb_dsp_rxovsize_sts               : 1;    /*9*/
        uint32_t ntb_ep_txovsize_sts                : 1;    /*6*/
        uint32_t ntb_ep_rxovsize_sts                : 1;    /*7*/
        uint32_t                                    : 24;
    };
}group12_ntbmlf_substs_t;



typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_rcv_io_sts                     : 1;    /*0*/
        uint32_t ntb_rcv_at_miss_sts                : 1;    /*1*/
        uint32_t ntb_ur_hit_sts                     : 1;    /*2*/
        uint32_t ntb_txib_hit_sts                   : 1;    /*3*/
        uint32_t ntb_txbar0_outof_range_sts         : 1;    /*4*/
        uint32_t ntb_txbar0_plinv_sts               : 1;    /*5*/
        uint32_t ntb_txlut_inv_sts                  : 1;    /*6*/
        uint32_t ntb_txdir_inv_sts                  : 1;    /*7*/
        uint32_t ntb_tgt_bus_master_en_miss_sts     : 1;    /*8*/
        uint32_t ntb_tx_legal_msg_sts               : 1;    /*9*/
        //uint32_t ntb_dsp_msen_wr_sts                : 1;    /*10*/        DE 20240717版本删除了这些寄存器
        //uint32_t ntb_dsp_msen_rd_sts                : 1;    /*11*/
        uint32_t ntb_ep_msen_wr_sts                 : 1;    /*10*/
        uint32_t ntb_ep_msen_rd_sts                 : 1;    /*11*/
        //uint32_t ntb_dsp_win_miss_wr_sts            : 1;    /*14*/
        //uint32_t ntb_dsp_win_miss_rd_sts            : 1;    /*15*/
        uint32_t ntb_ep_bar_miss_wr_sts             : 1;    /*12*/
        uint32_t ntb_ep_bar_miss_rd_sts             : 1;    /*13*/
        uint32_t                                    : 18;
    };
}group12_ntbur_substs_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_req_reqid_miss_sts             : 1;    /*0*/
        uint32_t ntb_cpl_reqid_miss_sts             : 1;    /*1*/
        uint32_t ntb_ntmsg_inv_sts                  : 1;    /*2*/
        uint32_t ntb_txcpl_invdid_sts               : 1;    /*3*/
        uint32_t ntb_rxmsg_inv_sts                  : 1;    /*4*/
        uint32_t ntb_tx_redsop_sts                  : 1;    /*5*/
        uint32_t ntb_tx_redeop_sts                  : 1;    /*6*/
        uint32_t ntb_tx_invphase_sts                : 1;    /*7*/
        uint32_t ntb_rx_redsop_sts                  : 1;    /*8*/
        uint32_t ntb_rx_redeop_sts                  : 1;    /*9*/
        uint32_t ntb_rx_invphase_sts                : 1;    /*10*/
        uint32_t ntb_rx_eop_miss_sts                : 1;    /*11*/
        uint32_t ntb_rx_eop_fail_sts                : 1;    /*12*/
        uint32_t ntb_rx_invid_sts                   : 1;    /*13*/
        uint32_t ntb_ntmsg_ecc_uncorr_sts           : 1;    /*14*/
        uint32_t ntb_ntcpl_ecc_uncorr_sts           : 1;    /*15*/
        uint32_t                                    : 16;
    };
}group12_ntbuce_internal_substs_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_req_reqid_miss_sts             : 1;    /*0*/
        uint32_t ntb_cpl_reqid_miss_sts             : 1;    /*1*/
        uint32_t ntb_ntmsg_inv_sts                  : 1;    /*2*/
        uint32_t ntb_txcpl_invdid_sts               : 1;    /*3*/
        uint32_t ntb_rxmsg_inv_sts                  : 1;    /*4*/
        uint32_t ntb_tx_redsop_sts                  : 1;    /*5*/
        uint32_t ntb_tx_redeop_sts                  : 1;    /*6*/
        uint32_t ntb_tx_invphase_sts                : 1;    /*7*/
        uint32_t ntb_rx_redsop_sts                  : 1;    /*8*/
        uint32_t ntb_rx_redeop_sts                  : 1;    /*9*/
        uint32_t ntb_rx_invphase_sts                : 1;    /*10*/
        uint32_t ntb_rx_eop_miss_sts                : 1;    /*11*/
        uint32_t ntb_rx_eop_fail_sts                : 1;    /*12*/
        uint32_t ntb_rx_invid_sts                   : 1;    /*13*/
        uint32_t ntb_ntmsg_ecc_corr_sts             : 1;    /*14*/
        uint32_t ntb_ntcpl_ecc_corr_sts             : 1;    /*15*/
        uint32_t                                    : 16;
    };
}group12_ntbce_internal_substs_t;

typedef union {
    uint32_t value;
    struct {
        //uint32_t nt_tx_poisoncfgw0_sts              : 1;    /*0*/     DE 20240717版本删除了这些寄存器
        //uint32_t nt_tx_poisoncfgr0_sts              : 1;    /*1*/
        uint32_t nt_tx_poisoncfgw1_sts              : 1;    /*0*/
        uint32_t nt_tx_poisoncfgr1_sts              : 1;    /*1*/
        uint32_t nt_tx_poisonwr0_sts                : 1;    /*2*/
        uint32_t nt_tx_poisonrd0_sts                : 1;    /*3*/
        uint32_t nt_tx_poisonwr2_sts                : 1;    /*4*/
        uint32_t nt_tx_poisonrd2_sts                : 1;    /*5*/
        uint32_t nt_tx_poisonmsg_sts                : 1;    /*6*/
        uint32_t nt_tx_poisonplgl_sts               : 1;    /*7*/
        uint32_t                                    : 24;
    };
}group12_ntbep_substs_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t nt_rx_ecrc_sts             : 1;
        uint32_t nt_rx_poisonwr_sts         : 1;
        uint32_t nt_rx_poisoncpl_sts        : 1;
        uint32_t nt_rx_cplabort_sts         : 1;
        uint32_t                            : 28;
    };
}group12_ntbunused_substs_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_dsp_txovsize_sts       : 1;    /*0*/
        uint32_t ntb_dsp_rxovsize_sts       : 1;    /*1*/
        uint32_t ntb_dsp_msen_wr_sts        : 1;    /*2*/
        uint32_t ntb_dsp_msen_rd_sts        : 1;    /*3*/
        uint32_t ntb_dsp_win_miss_wr_sts    : 1;    /*4*/
        uint32_t ntb_dsp_win_miss_rd_sts    : 1;    /*5*/
        uint32_t nt_tx_poisoncfgw0_sts      : 1;    /*6*/
        uint32_t nt_tx_poisoncfgr0_sts      : 1;    /*7*/
        uint32_t nt_tx_cfg0_miss_sts        : 1;    /*8*/
        uint32_t nt_dsptxcfg_fmtfail_sts    : 1;    /*9*/
        uint32_t                            : 22;
    };
}group12_ntbdsp_substs_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_func_dsp_udt                   : 1;    /*0*/
        uint32_t ntb_func_dsp_bme_udt               : 1;    /*1*/
        uint32_t ntb_func_ep_bme_udt                : 1;    /*2*/
        uint32_t ntb_func_2nd_rst_udt               : 1;    /*3*/
        uint32_t ntb_func_flushend                  : 1;    /*4*/                                
        uint32_t ntb_err_ecrc_eperr_sts             : 1;    /*5*/
        uint32_t ntb_err_ecrc_mngerr_sts            : 1;    /*6*/
        uint32_t ntb_err_tx_poisontlp_group         : 1;    /*7*/
        uint32_t ntb_err_malform_group              : 1;    /*8*/
        uint32_t ntb_err_ur_group                   : 1;    /*9*/
        uint32_t ntb_err_internal_uce_group         : 1;    /*10*/
        uint32_t ntb_err_internal_ce_group          : 1;    /*11*/
        uint32_t ntb_err_unused_sts                 : 1;    /*12*/
        uint32_t ntb_err_dsp_sts                    : 1;    /*13*/
        uint32_t ntb_hostclr_sts                    : 1;    /*14*/
        uint32_t ntb_dsp_pfxblk_sts                 : 1;    /*15*/
        uint32_t ntb_ep_pfxerr_group                : 1;    /*16*/
        uint32_t ntb_rsvnt                          : 1;    /*17*/
        uint32_t                                    : 14;
    };
}group12_ntbintsts_t;




typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head24_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head25_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head26_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head27_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head28_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head29_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head30_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head31_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head32_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head33_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head34_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head35_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head36_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head37_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head38_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B0 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B1 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B2 : 8;
        uint32_t ECRC_DSPERR_1STHEAD_DW0_B3 : 8;

    };
}group12_head39_t;

typedef union {
    uint32_t value;
    struct 
    {
        uint32_t nt_tx_poisonwr_hit_cnt     : 8;
        uint32_t nt_rx_poisonwr_hit_cnt     : 8;
        uint32_t nt_tx_poisoncpl_hit_cnt    : 8;
        uint32_t nt_rx_poisoncpl_hit_cnt    : 8;
    };
}group11_sts4_t;

/*cpl abort*/
#define YD_NTB_GROUP11_STS5_OFFSET  0x1144

typedef union {
    uint32_t value;
    struct {
        uint32_t nt_tx_cplabort_hit_cnt     : 8;
        uint32_t nt_rx_cplabort_hit_cnt     : 8;
        uint32_t nt_tx_bme_miss_cnt         : 8;
        uint32_t                            : 8;
    };

}group11_sts5_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_dsptxcfg_fmtfail_cnt       : 8;
        uint32_t ntb_eptxcfg_fmtfail_cnt        : 8;
        uint32_t ntb_txbar0_fmtfail_cnt         : 8;
        uint32_t                                : 8;
    };
}group11_sts6_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t nt_tx_poisoncfgw0_hit_cnt      : 2;
        uint32_t                                : 6;
        uint32_t nt_tx_poisoncfgr0_hit_cnt      : 2;
        uint32_t                                : 6;
        uint32_t nt_tx_poisoncfgw1_hit_cnt      : 2;
        uint32_t                                : 6;
        uint32_t nt_tx_poisoncfgr1_hit_cnt      : 2;
        uint32_t                                : 6;
    };
}group11_sts7_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t nt_tx_poisonwr0_hit_cnt        : 2;
        uint32_t                                : 6;
        uint32_t nt_tx_poisonrd0_hit_cnt        : 2;
        uint32_t                                : 6;
        uint32_t nt_tx_poisonwr2_hit_cnt        : 2;
        uint32_t                                : 6;
        uint32_t nt_tx_poisonrd2_hit_cnt        : 2;
        uint32_t                                : 6;
    };
}group11_sts8_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t nt_tx_poisonmsg_hit_cnt        : 2;
        uint32_t                                : 6;
        uint32_t nt_tx_poisonplgl_hit_cnt       : 2;
        uint32_t                                : 22;
    };
}group11_sts9_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t tx_bme_miss_tgtid              : 8;
        uint32_t tx_bme_miss_tgt_dsp_bmen       : 1;
        uint32_t tx_bme_miss_tgt_ep_bmen        : 1;
    };
}group11_info0_t;


typedef union {
    uint32_t value;
    struct {
        
        uint32_t nt_tx_bme_miss_1sthead_B0      : 8;
        uint32_t nt_tx_bme_miss_1sthead_B1      : 8;
        uint32_t nt_tx_bme_miss_1sthead_B2      : 8;
        uint32_t nt_tx_bme_miss_1sthead_B3      : 8;
    };
}group12_bme_err_dw_t;  /*0x1180*/

typedef union {
    uint32_t value;
    struct {
        uint32_t fail_1sthead_B0        : 8;
        uint32_t fail_1sthead_B1        : 8;
        uint32_t fail_1sthead_B2        : 8;
        uint32_t fail_1sthead_B3        : 8;

    };
}group12_dsptxcfg_fmt_dw_t; /*0x1190*/

typedef union {
    uint32_t value;
    struct {
        uint32_t fail_1sthead_B0        : 8;
        uint32_t fail_1sthead_B1        : 8;
        uint32_t fail_1sthead_B2        : 8;
        uint32_t fail_1sthead_B3        : 8;
    };
}group12_eptxcfg_fmt_dw_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t fail_1sthead_B0        : 8;
        uint32_t fail_1sthead_B1        : 8;
        uint32_t fail_1sthead_B2        : 8;
        uint32_t fail_1sthead_B3        : 8;
    };
}group12_txbar0_fmt_dw_t; /*0x11b0*/
typedef union {
    uint32_t value;
    struct {
        uint32_t NT_req_reqID_miss_uc_severity      : 1;    /*0*/
        uint32_t NT_cpl_reqID_miss_uc_severity      : 1;    /*1*/
        uint32_t NT_NTMSG_inv_uc_severity           : 1;    /*2*/
        uint32_t NT_TXCPL_invdid_uc_severity        : 1;    /*3*/
        uint32_t NT_RXMSG_inv_uc_severity           : 1;    /*4*/
        uint32_t NT_tx_redsop_uc_severity           : 1;    /*5*/
        uint32_t NT_tx_redeop_uc_severity           : 1;    /*6*/
        uint32_t NT_tx_invphase_uc_severity         : 1;    /*7*/
        uint32_t NT_rx_redsop_uc_severity           : 1;    /*8*/
        uint32_t NT_rx_redeop_uc_severity           : 1;    /*9*/
        uint32_t NT_rx_invphase_uc_severity         : 1;    /*10*/
        uint32_t NT_rx_eop_miss_uc_severity         : 1;    /*11*/
        uint32_t NT_rx_eop_fail_uc_severity         : 1;    /*12*/
        uint32_t NT_rx_invid_uc_severity            : 1;    /*13*/
        uint32_t                                    : 18;
    };
}group11_aer_svt_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t t1sthead_B0             : 8;
        uint32_t t1sthead_B1             : 8;
        uint32_t t1sthead_B2             : 8;
        uint32_t t1sthead_B3             : 8;
    };
}group12_cfg0_miss_dw0_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t t1sthead_B0             : 8;
        uint32_t t1sthead_B1             : 8;
        uint32_t t1sthead_B2             : 8;
        uint32_t t1sthead_B3             : 8;
    };
}group12_cfg0_miss_dw1_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t t1sthead_B0             : 8;
        uint32_t t1sthead_B1             : 8;
        uint32_t t1sthead_B2             : 8;
        uint32_t t1sthead_B3             : 8;
    };
}group12_cfg0_miss_dw2_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t t1sthead_B0             : 8;
        uint32_t t1sthead_B1             : 8;
        uint32_t t1sthead_B2             : 8;
        uint32_t t1sthead_B3             : 8;
    };
}group12_cfg0_miss_dw3_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t B0                     : 8;
        uint32_t B1                     : 8;
        uint32_t B2                     : 8;
        uint32_t B3                     : 8;
    };
}group12_illegaltype_1sthead_dw_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t B0                     : 8;
        uint32_t B1                     : 8;
        uint32_t B2                     : 8;
        uint32_t B3                     : 8;
    };
}group12_illegalecrc_1sthead_dw_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t B0                     : 8;
        uint32_t B1                     : 8;
        uint32_t B2                     : 8;
        uint32_t B3                     : 8;
    };
}group12_illegallength_1sthead_dw_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t B0                     : 8;
        uint32_t B1                     : 8;
        uint32_t B2                     : 8;
        uint32_t B3                     : 8;
    };
}group12_illegalmsg_1sthead_dw_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t B0                     : 8;
        uint32_t B1                     : 8;
        uint32_t B2                     : 8;
        uint32_t B3                     : 8;
    };
}group12_crsbdry_1sthead_dw_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t B0                     : 8;
        uint32_t B1                     : 8;
        uint32_t B2                     : 8;
        uint32_t B3                     : 8;
    };
}group12_ep_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t dsp_cfg_wr_en          : 1;     /*0x8000*/
        uint32_t iep_cfg_wr_en          : 1;
        uint32_t idsp_non_sticky_rst_n  : 1;
        uint32_t iep_non_sticky_rst_n   : 1;
        uint32_t idsp_sticky_rst_n      : 1;
        uint32_t iep_sticky_rst_n       : 1;
        uint32_t idsp_bar_mask_wr_en    : 1;
        uint32_t iep_bar_mask_wr_en     : 1;
        uint32_t RECRC_EN               : 1;
        uint32_t RECRC_CHK              : 1;
        uint32_t                        : 22;
    };
}cfg_space_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t rdlh_link_up           : 1;
        uint32_t rdlh_dlcntrl_state     : 2;
        uint32_t                        : 29;
    };
}cfg_in0_add_t; /*0x8004*/


typedef union {
    uint32_t value;
    struct {
        uint32_t smlh_link_up                       : 1;
        uint32_t smlh_autoneg_link_width            : 6;
        uint32_t smlh_autoneg_link_sp               : 4;
        uint32_t smlh_bw_mgt_status                 : 1;
        uint32_t smlh_link_auto_bw_status           : 1;
        uint32_t smlh_link_training_in_prog         : 1;
        uint32_t smlh_clr_enter_compliance          : 1;
        uint32_t smlh_tx_margin_rst                 : 1;
        uint32_t mac_phy_txdeemph                   : 1;
        uint32_t smlh_ls2_eq_req                    : 1;
        uint32_t smlh_ls2_eq_success                : 3;
        uint32_t smlh_ls2_eq_cmpl                   : 1;
        uint32_t smlh_ls2_eq_enter                  : 1;
        uint32_t smlh_ltssm_in_detectquiet          : 1;
        uint32_t smlh_two_retimers_pre_detected     : 1;
        uint32_t smlh_crosslink_resolution          : 2;
        uint32_t smlh_retimer_pre_detected          : 1;
        uint32_t aux_pwr_det                        : 1;
        uint32_t radm_cpl_pending                   : 1;
        uint32_t                                    : 1;
    };
}cfg_in1_add_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t cfg_cor_err_det        : 1;
        uint32_t cfg_nf_err_det         : 1;
        uint32_t cfg_f_err_det          : 1;
        uint32_t cfg_unsupt_req_det     : 1;
        uint32_t                        : 28;
    };
}cfg_in2_add_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t master_data_perr_det       : 1;
        uint32_t signaled_target_abort_det  : 1;
        uint32_t rcvd_target_abort_det      : 1;
        uint32_t rcvd_master_abort_det      : 1;
        uint32_t signaled_sys_err_det       : 1;
        uint32_t perr_det                   : 1;
        uint32_t                            : 26;
    };
}cfg_in3_add_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t master_data_perr_det2      : 1;
        uint32_t signaled_target_abort_det2 : 1;
        uint32_t rcvd_target_abort_det2     : 1;
        uint32_t rcvd_master_abort_det2     : 1;
        uint32_t signaled_sys_err_det2      : 1;
        uint32_t perr_det2                  : 1;
        uint32_t                            : 26;
    };
}cfg_in4_add_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t radm_snoop_upd         : 1;
        uint32_t radm_snoop_bus_num     : 1;
        uint32_t                        : 7;
        uint32_t radm_snoop_dev_num     : 1;
        uint32_t                        : 22;
    };
}cfg_in5_add_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t pm_status          : 1;
        uint32_t pm_pme_en          : 1;
        uint32_t aux_pm_en          : 1;
        uint32_t app_clk_pm_en      : 1;
        uint32_t                    : 28;
    };
}cfg_in6_add_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t exp_rom_validation_status_strobe   : 1;
        uint32_t exp_rom_validation_status          : 1;
        uint32_t exp_rom_validation_details_strobe  : 1;
        uint32_t exp_rom_validation_details         : 1;
        uint32_t                                    : 28;
    };
}cfg_in7_add_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t header;
    };
}iep_dbi_error_log_add_t;   /*0x8044*/

typedef union {
    uint32_t value;
    struct {
        uint32_t header;
    };
}iep_mem_wr_error_log_add_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t header;
    };
}dsp_dbi_error_log_add_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t header;
    };
}dsp_mem_wr_error_log_add_t;   /*0x8074*/


typedef union {
    uint32_t value;
    struct {
        uint32_t xdlh_replay_num_rlover_err     : 1;
        uint32_t xdlh_replay_timeout_err        : 1;
        uint32_t rdlh_prot_err                  : 1;
        uint32_t rdlh_bad_dllp_err              : 1;
        uint32_t rdlh_bad_tlp_err               : 1;
        uint32_t rmlh_rcvd_err                  : 1;
        uint32_t                                : 26;
    };
}aer_error0_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t corr_internal_err                  : 1;
        uint32_t internal_err                       : 1;
        uint32_t rtlh_overfl_err                    : 1;
        uint32_t rtlh_fc_prot_err                   : 1;
        uint32_t radm_mlf_tlp_err                   : 1;
        uint32_t radm_ecrc_err                      : 1;
        uint32_t radm_unexp_cpl_err                 : 1;
        uint32_t radm_cpl_timeout_err               : 1;
        uint32_t radm_rcvd_req_ca                   : 1;
        uint32_t radm_rcvd_req_ur                   : 1;
        uint32_t radm_rcvd_cpl_poisoned             : 1;
        uint32_t radm_rcvd_wreq_poisoned            : 1;
    };
}aer_error1_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t xtlh_xmt_cpl_ur                        : 1;
        uint32_t xtlh_xmt_cpl_ca                        : 1;
        uint32_t xtlh_xmt_cpl_poisoned                  : 1;
        uint32_t xtlh_xmt_wreq_poisoned                 : 1;
        uint32_t radm_rcvd_cpl_ca                       : 1;
        uint32_t radm_rcvd_cpl_ur                       : 1;
        uint32_t xal_pci_addr_perr                      : 1;
        uint32_t xal_set_mstr_abort_primary             : 1;
        uint32_t xal_set_trgt_abort_primary             : 1;
        uint32_t xal_serr                               : 1;
        uint32_t xal_perr                               : 1;
        uint32_t xal_rcvd_cpl_ur                        : 1;
        uint32_t xal_rcvd_cpl_ca                        : 1;
        uint32_t xal_xmt_cpl_ca                         : 1;
        uint32_t lbc_xmt_cpl_ca                         : 1;
    };
}aer_error2_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t radm_hdr_log_valid         : 1;
        uint32_t                            : 15;
        uint32_t radm_msg_req_id            : 16;
    };
}aer_error3_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t radm_hdr_log;
    };
}aer_hdrlog0_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t radm_hdr_log;
    };
}aer_hdrlog1_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t radm_hdr_log;
    };
}aer_hdrlog2_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t radm_hdr_log;
    };
}aer_hdrlog3_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t radm_correctable_err           : 1;
        uint32_t                                : 7;
        uint32_t radm_nonfatal_err              : 1;
        uint32_t                                : 7;
        uint32_t radm_fatal_err                 : 1;
        uint32_t                                : 15;
    };
}aer_error4_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t uce_dl_prot_err_func_en_n          : 1;    /*0*/
        uint32_t uce_rx_tlp_poisoned_func_en_n      : 1;    /*1*/
        uint32_t uce_rx_fc_prot_err_func_en_n       : 1;    /*2*/
        uint32_t uce_cpl_timeout_func_en_n          : 1;    /*3*/
        uint32_t uce_cpl_tx_abort_func_en_n         : 1;    /*4*/
        uint32_t uce_unexp_tx_cpl_func_en_n         : 1;    /*5*/
        uint32_t uce_rx_overfl_func_en_n            : 1;    /*6*/
        uint32_t uce_rx_mlf_tlp_func_en_n           : 1;    /*7*/
        uint32_t uce_rx_ecrc_err_func_en_n          : 1;    /*8*/
        uint32_t uce_tx_unsupt_req_err_func_en_n    : 1;    /*9*/
        uint32_t uce_internal_err_func_en_n         : 1;    /*10*/
        uint32_t ce_rx_err_func_en_n                : 1;    /*11*/
        uint32_t ce_bad_tlp_func_en_n               : 1;    /*12*/
        uint32_t ce_bad_dllp_func_en_n              : 1;    /*13*/
        uint32_t ce_replay_num_rlover_func_en_n     : 1;    /*14*/
        uint32_t ce_replay_timeout_func_en_n        : 1;    /*15*/
        uint32_t ce_corr_internal_err_func_en_n     : 1;    /*16*/
        uint32_t                                    : 15;
    };
}ntb_mangaer_autoclr_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t dl_prot_err_sts                    : 1;    /*0*/
        uint32_t rx_tlp_wreq_poisoned_sts           : 1;    /*1*/
        uint32_t rx_tlp_cpl_poisoned_sts            : 1;    /*2*/
        uint32_t rx_fc_prot_err_sts                 : 1;    /*3*/
        uint32_t cpl_timeout_sts                    : 1;    /*4*/
        uint32_t cpl_tx_abort_sts                   : 1;    /*5*/
        uint32_t unexp_tx_cpl_sts                   : 1;    /*6*/
        uint32_t rx_overfl_sts                      : 1;    /*7*/
        uint32_t rx_mlf_tlp_sts                     : 1;    /*8*/
        uint32_t rx_ecrc_err_sts                    : 1;    /*9*/
        uint32_t tx_unsupt_req_err_sts              : 1;    /*10*/
        uint32_t internal_err_sts                   : 1;    /*11*/
        uint32_t                                    : 20;
    };
}ntb_mngaer_ucests_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t rx_err_sts                         : 1;    /*0*/
        uint32_t bad_tlp_sts                        : 1;    /*1*/
        uint32_t bad_dllp_sts                       : 1;    /*2*/
        uint32_t replay_num_rlover_sts              : 1;    /*3*/
        uint32_t replay_timeout_sts                 : 1;    /*4*/
        uint32_t corr_internal_err_sts              : 1;    /*5*/
        uint32_t                                    : 26;
    };
}ntb_mngaer_cests_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t radm_hdr_log;
    };
}ntb_mngaer_hdr_log_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t radm_hdr_log_valid;
    };
}ntb_mngaer_hdr_log_valid_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_0                 : 8;  
        uint32_t ntb_msi_ctrl_1                 : 8;  
        uint32_t ntb_msi_ctrl_2                 : 8;  
        uint32_t ntb_msi_ctrl_3                 : 8;  
    };
}group13_msi_g0_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_4                 : 8;  
        uint32_t ntb_msi_ctrl_5                 : 8;  
        uint32_t ntb_msi_ctrl_6                 : 8;  
        uint32_t ntb_msi_ctrl_7                 : 8;  
    };
}group13_msi_g1_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_8                 : 8;  
        uint32_t ntb_msi_ctrl_9                 : 8;  
        uint32_t ntb_msi_ctrl_10                : 8;  
        uint32_t ntb_msi_ctrl_11                : 8;  
    };
}group13_msi_g2_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_12                : 8;  
        uint32_t ntb_msi_ctrl_13                : 8;  
        uint32_t ntb_msi_ctrl_14                : 8;  
        uint32_t ntb_msi_ctrl_15                : 8;  
    };
}group13_msi_g3_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_16                : 8;  
        uint32_t ntb_msi_ctrl_17                : 8;  
        uint32_t ntb_msi_ctrl_18                : 8;  
        uint32_t ntb_msi_ctrl_19                : 8;  
    };
}group13_msi_g4_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_20                : 8;  
        uint32_t ntb_msi_ctrl_21                : 8;  
        uint32_t ntb_msi_ctrl_22                : 8;  
        uint32_t ntb_msi_ctrl_23                : 8;  
    };
}group13_msi_g5_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_24                : 8;  
        uint32_t ntb_msi_ctrl_25                : 8;  
        uint32_t ntb_msi_ctrl_26                : 8;  
        uint32_t ntb_msi_ctrl_27                : 8;  
    };
}group13_msi_g6_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_28                : 8;  
        uint32_t ntb_msi_ctrl_29                : 8;  
        uint32_t ntb_msi_ctrl_30                : 8;  
        uint32_t ntb_msi_ctrl_31                : 8;  
    };
}group13_msi_g7_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_32                : 8;  
        uint32_t ntb_msi_ctrl_33                : 8;  
        uint32_t ntb_msi_ctrl_34                : 8;  
        uint32_t ntb_msi_ctrl_35                : 8;  
    };
}group13_msi_g8_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_36                : 8;  
        uint32_t ntb_msi_ctrl_37                : 8;  
        uint32_t ntb_msi_ctrl_38                : 8;  
        uint32_t ntb_msi_ctrl_39                : 8;  
    };
}group13_msi_g9_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_40                : 8;  
        uint32_t ntb_msi_ctrl_41                : 8;  
        uint32_t ntb_msi_ctrl_42                : 8;  
        uint32_t ntb_msi_ctrl_43                : 8;  
    };
}group13_msi_g10_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_44                : 8;  
        uint32_t ntb_msi_ctrl_45                : 8;  
        uint32_t ntb_msi_ctrl_46                : 8;  
        uint32_t ntb_msi_ctrl_47                : 8;  
    };
}group13_msi_g11_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_48                : 8;  
        uint32_t ntb_msi_ctrl_49                : 8;  
        uint32_t ntb_msi_ctrl_50                : 8;  
        uint32_t ntb_msi_ctrl_51                : 8;  
    };
}group13_msi_g12_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_52                : 8;  
        uint32_t ntb_msi_ctrl_53                : 8;  
        uint32_t ntb_msi_ctrl_54                : 8;  
        uint32_t ntb_msi_ctrl_55                : 8;  
    };
}group13_msi_g13_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_56                : 8;  
        uint32_t ntb_msi_ctrl_57                : 8;  
        uint32_t ntb_msi_ctrl_58                : 8;  
        uint32_t ntb_msi_ctrl_59                : 8;  
    };
}group13_msi_g14_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_msi_ctrl_60                : 8;  
        uint32_t ntb_msi_ctrl_61                : 8;  
        uint32_t ntb_msi_ctrl_62                : 8;  
        uint32_t ntb_msi_ctrl_63                : 8;  
    };
}group13_msi_g15_t;



typedef union {
    uint32_t value;
    struct {
        uint32_t smlh_link_up                   : 1;
        uint32_t                                : 31;
    };
}group13_cfgin1_1_0_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t smlh_link_up                   : 1;
        uint32_t                                : 31;
    };
}group13_cfgin1_1_1_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_flushend_msk               : 1;
        uint32_t                                : 7;
        uint32_t ntb_hotrst                     : 1;
        uint32_t                                : 23;
    };
}group13_hotrst_ctrl_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_flushend                   : 1;
        uint32_t                                : 31;
    };
}group13_hotrst_sts_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_tx_regin_full_vector                   : 1;        /*0x0*/
        uint32_t ntb_tx_txbuf_full_vector                   : 1;        /*0x1*/
        uint32_t ntb_tx_ntmsg_full_vector                   : 1;        /*0x2*/
        uint32_t ntb_tx_mdtx_full_vector                    : 1;        /*0x3*/ 
        uint32_t ntb_tx_mdtxreg_full_vector                 : 1;        /*0x4*/
        uint32_t                                            : 2;        
        uint32_t ntb_tx_n2c_p0_full_vector                  : 1;        /*0x7*/
        uint32_t ntb_tx_n2c_p1_full_vector                  : 1;        /*0x8*/
        uint32_t                                            : 2; 
        uint32_t ntb_rx_cb2ntb_full_vector                  : 1;        /*11*/
        uint32_t ntb_rx_inbuf_full_vector                   : 1;        /*12*/
        uint32_t ntb_rx_md_full_vector                      : 1;        /*13*/
        uint32_t ntb_rx_n2s_full_vector                     : 1;        /*14*/
        uint32_t                                            : 1; 
        uint32_t ntb_rx_ntmsg_full_vector                   : 1;        /*16*/
        uint32_t ntb_rx_ntcpl_full_vector                   : 1;        /*17*/
        uint32_t ntb_rx_ntmsi_full_vector                   : 1;        /*18*/
        uint32_t ntb_ecc_rxecc_full_vector                  : 1;        /*19*/
        uint32_t ntb_cfg_bar0_full_vector                   : 1;        /*20*/
        uint32_t ntb_cfg_ibmag_full_vector                  : 1;        /*21*/
        uint32_t ntb_cfg_bar0_dbi_in_fifo_full_vector       : 1;        /*22*/ 
        uint32_t ntb_cfg_bar0_dbi_out_fifo_full_vector      : 1;        /*23*/ 
        uint32_t ntb_cfg_dsp_dbi_in_fifo_full_vector        : 1;        /*24*/ 
        uint32_t ntb_cfg_dsp_dbi_out_fifo_full_vector       : 1;        /*25*/
        uint32_t ntb_cfg_ep_dbi_in_fifo_full_vector         : 1;        /*26*/ 
        uint32_t ntb_cfg_ep_dbi_out_fifo_full_vector        : 1;        /*27*/ 
        uint32_t                                            : 4;
    };
}group13_pfmon_sts_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_tx_regin_full_enable                   : 1;        /*0x0*/
        uint32_t ntb_tx_txbuf_full_enable                   : 1;        /*0x1*/
        uint32_t ntb_tx_ntmsg_full_enable                   : 1;        /*0x2*/
        uint32_t ntb_tx_mdtx_full_enable                    : 1;        /*0x3*/ 
        uint32_t ntb_tx_mdtxreg_full_enable                 : 1;        /*0x4*/
        uint32_t                                            : 2;        
        uint32_t ntb_tx_n2c_p0_full_enable                 : 1;        /*0x7*/
        uint32_t ntb_tx_n2c_p1_full_enable                  : 1;        /*0x8*/
        uint32_t                                            : 2; 
        uint32_t ntb_rx_cb2ntb_full_enable                  : 1;        /*11*/
        uint32_t ntb_rx_inbuf_full_enable                   : 1;        /*12*/
        uint32_t ntb_rx_md_full_enable                      : 1;        /*13*/
        uint32_t ntb_rx_n2s_full_enable                     : 1;        /*14*/
        uint32_t                                            : 1; 
        uint32_t ntb_rx_ntmsg_full_enable                   : 1;        /*16*/
        uint32_t ntb_rx_ntcpl_full_enable                   : 1;        /*17*/
        uint32_t ntb_rx_ntmsi_full_enable                   : 1;        /*18*/
        uint32_t ntb_ecc_rxecc_full_enable                  : 1;        /*19*/
        uint32_t ntb_cfg_bar0_full_enable                   : 1;        /*20*/
        uint32_t ntb_cfg_ibmag_full_enable                  : 1;        /*21*/
        uint32_t ntb_cfg_bar0_dbi_in_fifo_full_enable       : 1;        /*22*/ 
        uint32_t ntb_cfg_bar0_dbi_out_fifo_full_enable      : 1;        /*23*/ 
        uint32_t ntb_cfg_dsp_dbi_in_fifo_full_enable        : 1;        /*24*/ 
        uint32_t ntb_cfg_dsp_dbi_out_fifo_full_enable       : 1;        /*25*/
        uint32_t ntb_cfg_ep_dbi_in_fifo_full_enable         : 1;        /*26*/ 
        uint32_t ntb_cfg_ep_dbi_out_fifo_full_enable        : 1;        /*27*/ 
        uint32_t                                            : 4;
    };
}group13_pfmon_en_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t TXP1ARB_GNT_B0     : 8;            
        uint32_t TXP1ARB_GNT_B1     : 8;      
        uint32_t TXP1ARB_GNT_B2     : 8;       
        uint32_t TXP1ARB_GNT_B3     : 8;          
    };
}group13_f7_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t s0_pasid_en        : 1;
        uint32_t s1_pasid_en        : 1; 
        uint32_t s2_pasid_en        : 1; 
        uint32_t s3_pasid_en        : 1; 
        uint32_t s4_pasid_en        : 1; 
        uint32_t s5_pasid_en        : 1; 
        uint32_t s6_pasid_en        : 1; 
        uint32_t s7_pasid_en        : 1; 
        uint32_t s8_pasid_en        : 1; 
        uint32_t s9_pasid_en        : 1; 
        uint32_t s10_pasid_en       : 1; 
        uint32_t s11_pasid_en       : 1; 
        uint32_t s12_pasid_en       : 1; 
        uint32_t s13_pasid_en       : 1; 
        uint32_t s14_pasid_en       : 1; 
        uint32_t s15_pasid_en       : 1;             
        uint32_t                    : 16;             
    };
}group13_f8_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t s0_tph_en          : 1;
        uint32_t                    : 1;  
        uint32_t s1_tph_en          : 1;
        uint32_t                    : 1;  
        uint32_t s2_tph_en          : 1;
        uint32_t                    : 1;  
        uint32_t s3_tph_en          : 1;
        uint32_t                    : 1;  
        uint32_t s4_tph_en          : 1;
        uint32_t                    : 1;  
        uint32_t s5_tph_en          : 1;
        uint32_t                    : 1;  
        uint32_t s6_tph_en          : 1;
        uint32_t                    : 1;  
        uint32_t s7_tph_en          : 1;
        uint32_t                    : 1;  
        uint32_t s8_tph_en          : 1; 
        uint32_t                    : 15;             
    };
}group13_f9_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_intx_doorbell_ring         : 1;
        uint32_t                                : 31;
    };
}group13_intx_logic_sts_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_intx_reg_mode_inta                 : 1;
        uint32_t ntb_intx_reg_mode_intb                 : 1;
        uint32_t ntb_intx_reg_mode_intc                 : 1;
        uint32_t ntb_intx_reg_mode_intd                 : 1;
        uint32_t ntb_intx_doorbell_ring_timer_limit     : 16;
        uint32_t ntb_intx_doorbell_ring_intx_mask       : 1;
        uint32_t                                        : 11;
    };
}group13_intx_ctrl_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t ntb_intx_inta                  : 1;
        uint32_t ntb_intx_intb                  : 1;
        uint32_t ntb_intx_intc                  : 1;
        uint32_t ntb_intx_intd                  : 1;
        uint32_t                                : 28;
    };
}group13_intx_regset_t;





typedef union {
    uint32_t value;
    struct {
        uint32_t s0_trigger                     : 1;
        uint32_t                                : 7;
        uint32_t s1_trigger                     : 1;
        uint32_t                                : 7;
        uint32_t s2_trigger                     : 1;
        uint32_t                                : 7;
        uint32_t s3_trigger                     : 1;
        uint32_t                                : 7;
    };
}group13_rsvint_trgr_ntb_rsvint0_t;





typedef union {
    uint32_t value;
    struct {
        uint32_t s4_trigger                     : 1;
        uint32_t                                : 7;
        uint32_t s5_trigger                     : 1;
        uint32_t                                : 7;
        uint32_t s6_trigger                     : 1;
        uint32_t                                : 7;
        uint32_t s7_trigger                     : 1;
        uint32_t                                : 7;
    };
}group13_rsvint_trgr_ntb_rsvint1_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t s8_trigger                     : 1;
        uint32_t                                : 31;
    };
}group13_rsvint_trgr_ntb_rsvint2_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t s0_cnt                     : 1;
        uint32_t s1_cnt                     : 1;
        uint32_t s2_cnt                     : 1;
        uint32_t s3_cnt                     : 1;
    };
}group13_rsvint_cnt_ntb_rsvint0_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t s4_cnt                     : 1;
        uint32_t s5_cnt                     : 1;
        uint32_t s6_cnt                     : 1;
        uint32_t s7_cnt                     : 1;
    };
}group13_rsvint_cnt_ntb_rsvint1_t;

typedef union {
    uint32_t value;
    struct {
        uint32_t s8_cnt                     : 1;
        uint32_t                            : 31;
    };
}group13_rsvint_cnt_ntb_rsvint2_t;


typedef union {
    uint32_t value;
    struct {
        uint32_t s0_int_mask                        : 1;
        uint32_t s1_int_mask                        : 1;
        uint32_t s2_int_mask                        : 1;
        uint32_t s3_int_mask                        : 1;
        uint32_t s4_int_mask                        : 1;
        uint32_t s5_int_mask                        : 1;
        uint32_t s6_int_mask                        : 1;
        uint32_t s7_int_mask                        : 1;
        uint32_t s8_int_mask                        : 1;
        uint32_t                                    : 23;
    };
}group13_rsvint_ctrl_t;



struct yd_ntb_reg{
    group0_t                                            group0;                         /*0x0*/
    group1_t                                            group1;                         /*0x4    size=32*4*/
    group0_roext_t                                      group0_roext;                   /*0x404*/
    group0_fabric_t                                     group0_fabric;                  /*0x408*/
    uint32_t                                            resv0[61];
    group3_t                                            group3;                         /*0x500      size=32*4*/
    uint32_t                                            resv1[61];
    group4_t                                            group4;                         /*0x700*/
    uint32_t                                            resv2[480];
    group5_t                                            group5;                         /*0x1000*/
    uint32_t                                            resv3[512];
    group6_t                                            group6;                         /*0x2000*/
    uint32_t                                            resv4[128];
    group7_t                                            group7;                         /*0xb00*/
    uint32_t                                            resv5[944];
    group8_t                                            group8;                         /*0xc04     size = 7*4*/
    uint32_t                                            resv6[48];
    group9_t                                            group9;                         /*0xc20*/
    uint32_t                                            resv7[1];
    group10_t                                           group10[56];                        /*0xc24*/
    group11_sts0_t                                      group11_sts0;                   /*0xc28*/
    group11_sts1_t                                      group11_sts1;                   /*0xc2c*/
    group11_sts2_t                                      group11_sts2;                   /*0xda4*/
    group11_sts3_t                                      group11_sts3;                   /*0xda8*/
    group11_sts4_t                                      group11_sts4;                   /*0x1140*/
    group11_sts5_t                                      group11_sts5;                   /*0x1144*/
    group11_sts6_t                                      group11_sts6;                   /*0x1148*/
    group11_sts7_t                                      group11_sts7;
    group11_sts8_t                                      group11_sts8;
    group11_sts9_t                                      group11_sts9;
    uint32_t                                            resv9[22];
    group11_info0_t                                     group11_info0;
    uint32_t                                            resv10[31];
    group11_mask_t                                      group11_mask;                   /*0xc40*/
    group11_mask_new_t                                  group11_mask_new;               /*0xdac*/
    group11_aer_svt_t                                   group11_aer_svt;                /*0x1200*/
    uint32_t                                            resv11[61];
    group11_head0_t                                     group11_head0;              /*0xdb0*/
    uint32_t                                            resv12[20];
    group11_head1_t                                     group11_head1;              /*0xe04*/
    uint32_t                                            resv13[20];
    group11_head2_t                                     group11_head2;              /*0xe58*/
    uint32_t                                            resv14[20];
    group11_head3_t                                     group11_head3;              /*0xeac*/
    uint32_t                                            resv15[192];
    group12_msgsts1_1_t                                 group12_msgsts1_1;             /*0xc44*/
    group12_tlpexp0_t                                   group12_tlpexp0;                /*0xc48*/
    group12_tlpexp1_t                                   group12_tlpexp1;                 /*0xc4c*/
    group12_bmen_t                                      group12_bmen;                   /*0xc50*/
  
    group12_msgsts0_t                                   group12_msgsts0;                /*0xce0*/
    group12_msgsts1_t                                   group12_msgsts1;                /*0xce4*/
    group12_msgsts2_t                                   group12_msgsts2;                /*0xce8*/
    group12_msgsts3_t                                   group12_msgsts3;                /*0xcec*/
    group12_msgsts4_t                                   group12_msgsts4;                /*0xcf0*/
    group12_msgsts5_t                                   group12_msgsts5;                /*0xcf4*/
    group12_msgsts6_t                                   group12_msgsts6;                /*0xcf8*/
    group12_msgsts7_t                                   group12_msgsts7;                /*0xcfc*/
    group12_msgsts8_t                                   group12_msgsts8;                /*0xd00*/

    group12_cnt1_t                                      group12_cnt1;                   /*0xd10*/
    group12_cnt2_t                                      group12_cnt2;                   /*0xd34*/
    group12_cnt3_t                                      group12_cnt3;                   /*0xd58*/
    group12_info3_t                                     group12_info3;                  /*0xd5c*/
    uint32_t                                            resv16[4];
    group12_ecc4_t                                      group12_ecc4;                   /*0xd80*/
    group12_ecc5_t                                      group12_ecc5;                   /*0xd84*/
    group12_ecc6_t                                      group12_ecc6;                   /*0xd88*/
    group12_ecc7_t                                      group12_ecc7;                   /*0xd8c*/
    group12_cnt4_t                                      group12_cnt4;                   /*0xd90*/
    group12_cnt5_t                                      group12_cnt5;                   /*0x10fc*/

    group12_mlf0_t                                      group12_mlf0;

    group12_mlf1_t                                      group12_mlf1;

    group12_mlf2_t                                      group12_mlf2;

    group12_sts0_t                                      group12_sts0;
    group12_sts1_t                                      group12_sts1;

    uint32_t                                            resv17[32];
    group12_ntbmlf_substs_t                             group12_ntbmlf_substs;

    group12_ntbur_substs_t                              group12_ntbur_substs;

    group12_ntbuce_internal_substs_t                    group12_ntbuce_internal_substs;

    group12_ntbce_internal_substs_t                     group12_ntbce_internal_substs;

    group12_ntbep_substs_t                              group12_ntbep_substs;
    group12_ntbunused_substs_t                          group12_ntbunused_substs;
    group12_ntbdsp_substs_t                             group12_ntbdsp_substs;
    uint32_t                                            resv18[9];
    group12_ntbintsts_t                                 group12_ntbintsts;
    uint32_t                                            resv19[47];
    group12_msgmask0_t                                  group12_msgmask0;               /*0xd04*/
    group12_msgmask1_t                                  group12_msgmask1;               /*0xd08*/
    hostclrsts_int_msk_t                                hostclrsts_int_msk;
    uint32_t                                            resv20[61];

    group12_head4_t                                     group12_head4;                  /*0xd24*/
    group12_head5_t                                     group12_head5;                  /*0xd28*/
    group12_head6_t                                     group12_head6;                  /*0xd2c*/
    group12_head7_t                                     group12_head7;                  /*0xd30*/
   
    group12_head8_t                                     group12_head8;                  /*9xd38*/
    group12_head9_t                                     group12_head9;                  /*0xd3c*/
    group12_head10_t                                    group12_head10;                 /*0xd40*/
    group12_head11_t                                    group12_head11;                 /*0xd44*/
    group12_head12_t                                    group12_head12;                 /*0xd48*/
    group12_head13_t                                    group12_head13;                 /*0xd4c*/
    group12_head14_t                                    group12_head14;                 /*0xd50*/
    group12_head15_t                                    group12_head15;                 /*0xd54*/
 
    group12_head16_t                                    group12_head16;                 /*0xd60*/
    group12_head17_t                                    group12_head17;                 /*0xd64*/
    group12_head18_t                                    group12_head18;                 /*0xd68*/
    group12_head19_t                                    group12_head19;                 /*0xd6c*/
    group12_head20_t                                    group12_head20;                 /*0xd94*/
    group12_head21_t                                    group12_head21;                 /*0xd98*/
    group12_head22_t                                    group12_head22;                 /*0xd9c*/
    group12_head23_t                                    group12_head23;                 /*0xda0*/

    group12_head24_t                                    group12_head24;                 /*0x1100*/
    group12_head25_t                                    group12_head25;                 /*0x1104*/
    group12_head26_t                                    group12_head26;                 /*0x1108*/
    group12_head27_t                                    group12_head27;                 /*0x110c*/
    group12_head28_t                                    group12_head28;                 /*0x1110*/
    group12_head29_t                                    group12_head29;                 /*0x1114*/
    group12_head30_t                                    group12_head30;                 /*0x1118*/
    group12_head31_t                                    group12_head31;                 /*0x111c*/
    group12_head32_t                                    group12_head32;                 /*0x1120*/
    group12_head33_t                                    group12_head33;                 /*0x1124*/
    group12_head34_t                                    group12_head34;                 /*0x1128*/
    group12_head35_t                                    group12_head35;                 /*0x112c*/
    group12_head36_t                                    group12_head36;                 /*0x1130*/
    group12_head37_t                                    group12_head37;                 /*0x1134*/
    group12_head38_t                                    group12_head38;                 /*0x1138*/
    group12_head39_t                                    group12_head39;                 /*0x113c*/


    group12_bme_err_dw_t                                group12_bme_err_dw;             /*0x1180*/
    uint32_t                                            resv21[3];

    group12_dsptxcfg_fmt_dw_t                           group12_dsptxcfg_fmt_dw;        /*0x1190*/
    uint32_t                                            resv22[3];
    group12_eptxcfg_fmt_dw_t                            group12_eptxcfg_fmt_dw;         /*0x11a0*/
    uint32_t                                            resv23[3];
    group12_txbar0_fmt_dw_t                             group12_txbar0_fmt_dw;          /*0x11b0*/
    uint32_t                                            resv24[3];
    group12_cfg0_miss_dw0_t                             group12_cfg0_miss_dw0;          /*0x1210*/
       
    group12_cfg0_miss_dw1_t                             group12_cfg0_miss_dw1;          /*0x1214*/
    group12_cfg0_miss_dw2_t                             group12_cfg0_miss_dw2;          /*0x1218*/
    group12_cfg0_miss_dw3_t                             group12_cfg0_miss_dw3;          /*0x121c*/


    group12_illegaltype_1sthead_dw_t                    group12_illegaltype_1sthead_dw;
    uint32_t                                            resv25[3];
    group12_illegalecrc_1sthead_dw_t                    group12_illegalecrc_1sthead_dw;
    uint32_t                                            resv26[3];
    group12_illegallength_1sthead_dw_t                  group12_illegallength_1sthead_dw;
    uint32_t                                            resv27[3];
    group12_illegalmsg_1sthead_dw_t                     group12_illegalmsg_1sthead_dw;
    uint32_t                                            resv28[3];
    group12_crsbdry_1sthead_dw_t                        group12_crsbdry_1sthead_dw;
    uint32_t                                            resv29[7];
    group12_ep_t                                        group12_ep;

    uint32_t                                            resv30[239];

    group13_f0_t                                        group13_f0;                     /*0x1000*/
    group13_f1_t                                        group13_f1;                     /*0x1004*/
    group13_f2_t                                        group13_f2;                     /*0x1008*/
    group13_f3_t                                        group13_f3;                     /*0x100c*/
    group13_f4_t                                        group13_f4;                     /*0x1010*/
    group13_f5_t                                        group13_f5;                     /*0x1014*/
    group13_f6_t                                        group13_f6;                     /*0x1018*/

    uint32_t                                            resv31;

    group13_msi_g0_t                                    group13_msi_g0;                 /*0x1300*/   
    group13_msi_g1_t                                    group13_msi_g1;                 /*0x1304*/
    group13_msi_g2_t                                    group13_msi_g2;                 /*0x1308*/
    group13_msi_g3_t                                    group13_msi_g3;                 /*0x130c*/
    group13_msi_g4_t                                    group13_msi_g4;                 /*0x1310*/
    group13_msi_g5_t                                    group13_msi_g5;                 /*0x1314*/
    group13_msi_g6_t                                    group13_msi_g6;                 /*0x1318*/
    group13_msi_g7_t                                    group13_msi_g7;
    group13_msi_g8_t                                    group13_msi_g8;
    group13_msi_g9_t                                    group13_msi_g9;
    group13_msi_g10_t                                   group13_msi_g10;
    group13_msi_g11_t                                   group13_msi_g11;
    group13_msi_g12_t                                   group13_msi_g12;
    group13_msi_g13_t                                   group13_msi_g13;
    group13_msi_g14_t                                   group13_msi_g14;
    group13_msi_g15_t                                   group13_msi_g15;
    uint32_t                                            resv32[40];

    group13_hotrst_ctrl_t                               group13_hotrst_ctrl;            /*0x5100*/
    uint32_t                                            resv33[3];
    group13_hotrst_sts_t                                group13_hotrst_sts;             /*5110*/
    uint32_t                                            resv34[3];
    group13_cfgin1_1_0_t                                group13_cfgin1_1_0;             /*5120*/
    group13_cfgin1_1_1_t                                group13_cfgin1_1_1;             /*5124*/
    uint32_t                                            resv35[2];
    group13_pfmon_sts_t                                 group13_pfmon_sts;              /*0x5130*/
    group13_pfmon_en_t                                  group13_pfmon_en;               /*0x5134*/
    uint32_t                                            resv36[50];
    group13_f7_t                                        group13_f7;
    group13_f8_t                                        group13_f8;
    group13_f9_t                                        group13_f9;
    uint32_t                                            resv100[1];
    group13_intx_logic_sts_t                            group13_intx_logic_sts;
    group13_intx_ctrl_t                                 group13_intx_ctrl;
    group13_intx_regset_t                               group13_intx_regset;
    uint32_t                                            resv101[1];
    group13_rsvint_trgr_ntb_rsvint0_t                   group13_rsvint_trgr_ntb_rsvint0;
    group13_rsvint_trgr_ntb_rsvint1_t                   group13_rsvint_trgr_ntb_rsvint1;
    group13_rsvint_trgr_ntb_rsvint2_t                   group13_rsvint_trgr_ntb_rsvint2;
    uint32_t                                            resv102[1];
    group13_rsvint_cnt_ntb_rsvint0_t                    group13_rsvint_cnt_ntb_rsvint0;
    group13_rsvint_cnt_ntb_rsvint1_t                    group13_rsvint_cnt_ntb_rsvint1;
    group13_rsvint_cnt_ntb_rsvint2_t                    group13_rsvint_cnt_ntb_rsvint2;
    uint32_t                                            resv103[1];
    group13_rsvint_ctrl_t                               group13_rsvint_ctrl;
   
   
};



typedef void (*yd_cb_func_t)(uint8_t cb_result, uint32_t dst_partition, uint8_t *data, size_t size, void *cb_arg);
typedef void (*yd_db_func_t)(uint8_t cb_result, uint32_t dst_partition, uint8_t db_num, void *cb_arg);
typedef void (*yd_ntf_func_t)(uint8_t cb_result, uint8_t *data, size_t size, void *cb_arg);
struct yd_callback_info{
    struct list_head list;
    uint8_t pipe_id;
    void *cb_arg;
    yd_cb_func_t cb_func;
};

struct yd_db_callback_info{
    struct list_head list;
    uint8_t db_num;
    void *cb_arg;
    yd_db_func_t cb_func;
};

struct yd_ntf_callback_info{
    void *cb_arg;
    yd_ntf_func_t cb_func;
    uint8_t flag;
};

/*put in yd_ntb_dev*/
struct yd_msg_callack{
    struct yd_callback_info callback_info[YD_MAX_STATION_ID];
};

struct yd_db_callack{
    struct yd_db_callback_info callback_info[YD_MAX_STATION_ID];
};

struct yd_ntf_callback{
    struct yd_ntf_callback_info callback_info;
};

struct yd_ntb_dev{
    struct pci_dev *pdev;
	enum yd_mem_type mem_type;
    uint8_t station_id;
    dma_addr_t bar2;
    dma_addr_t bar3;
    dma_addr_t lut_base;
    size_t bar2_total_size;
    size_t bar3_total_size;
    size_t bar2_residue_size;
    size_t bar3_residue_size;
	struct yd_ntb_reg *cfg;
   
    int idb_irq[3];
    int ibmsg_irq;
    int pcie_cap_irq;
    struct yd_msg_callack msg_callback;
    struct yd_db_callack db_callback;
    struct yd_ntf_callback ntf_callback;
    struct work_struct doorbell_work;
    struct work_struct message_work;
    struct mutex db_msg_lock;
    struct mutex lut_lock;
    struct mutex dir_lock;
    struct mutex req_id_lock;

    size_t dir_max_size;
    size_t lut_max_size;

    uint8_t station_topo[YD_MAX_STATION_ID];
    uint8_t ntb_cnt;
};

int yd_common_set_global_ndev(struct yd_ntb_dev *yd_ndev);
struct yd_ntb_dev *yd_common_get_global_ndev(void);
int yd_topo_init_live_station(void);
int yd_topo_get_live_station(uint32_t *station_array, uint32_t *station_cnt);
int yd_common_get_local_station_id(void);
int yd_common_init_local_station_id(void);
bool yd_common_station_id_valid(uint8_t station_id);
#endif
