#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/slab.h>
#include <linux/io.h>
#include <linux/crc32.h>

#include "../yd_ntb_common.h"

#include <linux/dmaengine.h>
#include <linux/pci.h>
struct completion g_comp;

#define TEST_DMA0_REQID 0x12
#define TEST_DMA1_REQID 0x34


#define CRC_VAL 10
uint32_t test_case;
uint32_t ntb_client;
uint32_t win_lut;
uint32_t lut_cnt;
uint32_t dir_cnt;
uint32_t addr_type;
uint32_t request_bdf;
module_param(test_case, int, 0);
module_param(ntb_client, int, 0);
module_param(win_lut, int, 0);
module_param(lut_cnt, int, 0);
module_param(dir_cnt, int, 0);
module_param(addr_type, int, 0);
module_param(request_bdf, int, 0);

#define PRJ_YUNDU_H
typedef void (*yd_cb_func_t)(uint8_t cb_result, uint32_t dst_partition, uint8_t *data, size_t size, void *cb_arg);
extern int sudo_alloc_lut_map_win(uint32_t station_id, phys_addr_t dst_addr, size_t size, phys_addr_t *src_addr, size_t *result_size);
extern int sudo_free_lut_map_win(uint32_t station_id, phys_addr_t dst_addr);
extern int sudo_alloc_dir_map_win(uint32_t station_id, phys_addr_t dst_addr, size_t size, phys_addr_t *src_addr, size_t *result_size);
extern int sudo_free_dir_map_win(uint32_t station_id, uint64_t addr);

extern int sudo_ntb_register_msg_cb(uint32_t station_id, uint32_t pipe_id, yd_cb_func_t func, void *arg);
extern int sudo_ntb_unregister_msg_cb(uint32_t station_id, uint32_t pipe_id);

extern int sudo_ntb_register_db_cb(uint32_t station_id, uint8_t db_num, yd_db_func_t func, void *arg);
extern int sudo_ntb_unregister_db_cb(uint32_t station_id, uint8_t db_num);

extern int sudo_ntb_knock_doorbell(uint32_t station_id, uint8_t db_num);
extern int sudo_ntb_send_msg(uint8_t station_id, uint8_t pipe_id, uint8_t *val, size_t size);
extern int sudo_ntb_get_max_pipe(void);

extern int sudo_ntb_get_topo(uint32_t *station_array, uint32_t *station_cnt);
extern int sudo_ntb_get_local_station_id(void);

extern int sudo_ntb_set_req_id(uint16_t req_id);
extern int sudo_ntb_clear_req_id(uint16_t req_id);
extern int sudo_ntb_free_req_id_cnt(void);

extern int sudo_ntb_get_lut_size(void);
extern int sudo_ntb_get_dir_size(void);

extern void sudo_ntf_cs_station_set(uint8_t cs_station, uint8_t as_usp);
extern void sudo_ntf_build_cs_path(uint8_t cs_station);
extern void sudo_ntf_p2p_port_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t addr32_align, uint32_t addr64_align, uint8_t cs_station, uint32_t dev_bdf);
extern void sudo_ntf_dst_nt_bus_set(uint8_t cs_station, uint32_t dst_fabric_nt_bus);
extern void sudo_ntf_internal_sw_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t addr32_align, uint32_t addr64_align);
extern void sudo_ntf_internal_nt_bus_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t dev_bdf);
extern void sudo_ntf_detect_other_sw_ntb(uint8_t cs_station);
extern int sudo_ntf_send_msg(uint8_t cs_station, uint8_t ntf_id, uint8_t *data, uint8_t len);
extern int sudo_ntf_msg_cb_register(yd_ntf_func_t func, void *arg);

#define TEST_PIPE_ID    0

#define TEST_ALLOC_CMD    0xff00

#define TEST_FREE_CMD   0xff

#define TEST_WRITE_OK_CMD   0xf0f0

#define TEST_READ_OK_CMD    0xf000

#define TEST_ALL_END        0xf00f

#define TEST_RESP_MSG_CMD   0xffff

#define TEST_REQ_ID 0x0




static unsigned long long g_client_recv_addr;


struct completion comp;
static int g_deal_ret;
static uint32_t g_crc_val;
#define TEST_SEND_TIMEOUT   3000


#define CLIENT_REQ_WIN_PHYS_ADDR        0x1
#define SERVER_RESP_WIN_PHYS_ADDR       0x2
#define CLIENT_WRITE_OK                 0x3
#define CLIENT_READ_OK                  0x4
#define SERVER_RESP_READ_OK_CRC         0x5
#define REQ_WIN_ADDR_MSG                0x6
#define SERVER_RESP_WIN_ADDR_CRC        0x7
#define SERVER_RESP_READ_OK_RET         0x8
#define REQ_FREE_WIN_ADDR               0x8
#define CLIENT_ALL_END                  0x9
#define CLIENT_RUN_SERVER_PRO           0xa
#define NTF_SERVER_RECV_REQ_NT_BUS      0xb
#define NTF_CLIENT_RECV_RESP_NT_BUS     0xc


#define CV_NTB_CASE_01  0x1
#define CV_NTB_CASE_02  0x2
#define CV_NTB_CASE_03  0x3
#define CV_NTB_CASE_04  0x4
#define CV_NTB_CASE_05  0x5
#define CV_NTB_CASE_06  0x6
#define CV_NTB_CASE_07  0x7
#define CV_NTB_CASE_08  0x8
#define CV_NTB_CASE_09  0x9
#define CV_NTB_CASE_10  0xa
#define CV_NTB_CASE_11  0xb
#define CV_NTB_CASE_12  0xc
#define CV_NTB_CASE_13  0xd
#define CV_NTB_CASE_14  0xe
#define CV_NTB_CASE_15  0xf
#define CV_NTB_CASE_16  0x10
#define CV_NTB_CASE_17  0x11
#define CV_NTB_CASE_18  0x12
#define CV_NTB_CASE_19  0x13
#define CV_NTB_CASE_20  0x14
#define CV_NTB_CASE_21  0x15
#define CV_NTB_CASE_22  0x16
#define CV_NTB_CASE_23  0x17
#define CV_NTB_CASE_24  0x18
#define CV_NTB_CASE_25  0x19
#define CV_NTB_CASE_26  0x1a
#define CV_NTB_CASE_27  0x1b
#define CV_NTB_CASE_28  0x1c
#define CV_NTB_CASE_29  0x1d
#define CV_NTB_CASE_30  0x1e
#define CV_NTB_CASE_31  0x1f

#define CV_NTB_CASE_35  0x23
#define CV_NTB_CASE_36  0x24
#define CV_NTB_CASE_37  0x25
#define CV_NTB_CASE_38  0x26
#define CV_NTB_CASE_40  0x28
#define CV_NTB_CASE_41  0x29
#define CV_NTB_CASE_42  0x2a
#define CV_NTB_CASE_43  0x2b
#define CV_NTB_CASE_51  0x33
#define CV_NTB_CASE_52  0x34
#define CV_NTB_CASE_58  0x3a



struct test_packet{
    uint32_t command;
    uint32_t case_num;
    uint64_t p_addr; 
    uint32_t crc_val;
    uint16_t ret;
    uint16_t dma_32;
};



static char g_case03_msg[] = "case3 msg";
static char g_case04_msg[] = "case4 msg";
//static char g_case06_msg[] = "case6 msg";
static char g_case07_msg[] = "case7 msg";
static char g_case08_msg[] = "case8 msg";
static char g_case09_msg[] = "case9 msg";
static char g_case10_msg[] = "case10 msg";
//static char g_case11_msg[] = "case11 msg";
static char g_case12_msg[] = "case12 msg";
static char g_case13_msg[] = "case13 msg";
//static char g_case14_msg[] = "case14 msg";
static char g_case17_msg[] = "case17 msg";
static char g_case18_msg[] = "case18 msg";
static char g_case20_msg[] = "case20 msg";


static int ntb_cv_get_remote_paddr(uint32_t target_station, unsigned long long *remote_addr, uint32_t case_num);
static int ntb_cv_rc_reqid_set(void);

#define DMA_DEV_VENDOR_ID   0x9011
#define DMA0_DEV_DEVICE_ID   0x1234
#define DMA1_DEV_DEVICE_ID   0x5678
#define NTB_DEV_VENDOR_ID   0x9011
#define NTB_DEV_DEVICE_ID   0x1359
#define NTB_DSP_DEV_DEVICE_ID   0x1358

#define MEP_DEV_VENDOR_ID   0x0c51
#define MEP_DEV_DEVICE_ID   0x0101



uint32_t src_fabric_station;
uint32_t cs_station;
uint32_t as_usp;
uint32_t dst_fabric_station;
uint32_t dst_fabric_nt_bus;
uint32_t addr32_align;
uint32_t addr64_align;
uint32_t ntf_id;
uint32_t ntf_client;
module_param(src_fabric_station, int, 0);
module_param(cs_station, int, 0);
module_param(as_usp, int, 0);
module_param(dst_fabric_station, int, 0);
module_param(dst_fabric_nt_bus, int, 0);
module_param(addr32_align, int, 0);
module_param(addr64_align, int, 0);
module_param(ntf_id, int, 0);
module_param(ntf_client, int, 0);

uint32_t test_type;
module_param(test_type, int, 0);
/*ntf case start*/
enum ntf_to_host_cmd {
    NTF_MULITE_FABRIC_INFO = 1,
    NTF_INTERNAL_FABRIC_INFO,
    NTF_DETECT_RESP,
    NTF_LOCAL_MSG,
};
uint32_t g_data[4*8];
uint32_t g_ntf_cmd = 0;



static struct pci_dev *ntb_cv_get_mep_dev(void)
{
    struct pci_dev *dev = NULL;
    dev = pci_get_device(MEP_DEV_VENDOR_ID, MEP_DEV_DEVICE_ID, dev);
    return dev;
    
}

static struct pci_dev *ntb_cv_get_ntb_dev(void)
{
    struct pci_dev *dev = NULL;
    dev = pci_get_device(NTB_DEV_VENDOR_ID, NTB_DEV_DEVICE_ID, dev);
    return dev;
   
}

static struct pci_dev *ntb_cv_get_ntb_dsp_dev(void)
{
    struct pci_dev *dev = NULL;
    dev = pci_get_device(NTB_DEV_VENDOR_ID, NTB_DSP_DEV_DEVICE_ID, dev);
    return dev;
    
}

static struct pci_dev *ntb_cv_get_dma0_dev(void)
{
    struct pci_dev *dev = NULL;
    dev = pci_get_device(DMA_DEV_VENDOR_ID, DMA0_DEV_DEVICE_ID, dev);
    return dev;
}

static struct pci_dev *ntb_cv_get_dma1_dev(void)
{
    struct pci_dev *dev = NULL;
    dev = pci_get_device(DMA_DEV_VENDOR_ID, DMA1_DEV_DEVICE_ID, dev);
	return dev;
   
   
}


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


static void dma_complete_callback(void *data)
{
   
    complete(&g_comp);
}

static int yd_dma_cv_common(struct device *dev, char *name, dma_addr_t src, dma_addr_t dst, size_t len, int max_burst, int wait)
{
    struct dma_slave_config config;
    struct dma_async_tx_descriptor *tx = NULL;
    dma_cookie_t cookie;
    long timeout = 5000;
    struct dma_chan *dchan = NULL;
    int ret = 0;
    struct dma_tx_state state;
    enum dma_status dstatus;
    int flag = 0;
    dchan = dma_request_chan(dev, name);
    if(!dchan || IS_ERR(dchan))
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
wait_comp:
    if(!wait_for_completion_timeout(&g_comp, msecs_to_jiffies(timeout))) {
        printk("[%s]: wait_for_completion_timeout timeout\n", __func__);
        ret = -1;
    }
    dstatus = dmaengine_tx_status(dchan, cookie, &state);
    printk("[%s]: %d: the residue = %d\n", __func__, __LINE__, state.residue);
    if(state.residue && flag < 5)
    {
        flag++;
        goto wait_comp;
    }
chan_err:
    dma_release_channel(dchan);
    return ret;
}

#define PAKCET_DMA_32_FLAG  0xffff0000

static int build_packet(struct test_packet **packet, uint32_t command, uint32_t case_num, uint32_t crc_val, uint32_t ret, uint64_t p_addr)
{
    struct test_packet *tmp = (struct test_packet *)vmalloc(sizeof(struct test_packet));
    if(!tmp)
    {
        return -1;
    }
    memset(tmp, 0, sizeof(struct test_packet));
    tmp->command = command;
    tmp->case_num = case_num;
    tmp->p_addr = p_addr;
    
    tmp->crc_val = crc_val;
    tmp->ret = (uint16_t)(ret & 0xffff);
    tmp->dma_32 = (uint16_t)((ret & 0xffff0000) >> 16);
    *packet = tmp;
 
    return 0;
    
}

static void free_packet(struct test_packet *packet)
{
    vfree(packet);
}

static int send_pipe_msg(uint8_t target_station, uint8_t pipe_id, uint8_t *val, size_t size)
{
    int ret;

    printk("[%s]: %d: enter target station = %d, size = %ld\n", __func__, __LINE__, target_station, size);
    ret = sudo_ntb_send_msg(target_station, TEST_PIPE_ID, val, size);
    if(ret)
    {
        printk("[%s]: %d: sudo_ntb_send_msg failed\n\n", __func__, __LINE__);
        return -1;
    }

    ret = sudo_ntb_knock_doorbell(target_station, 0);
    if(ret)
    {
        return ret;
    }
    return 0;
}


static unsigned long long get_local_dma_phys(uint32_t target_station)
{
    struct pci_dev *pdev = NULL;
	unsigned long long phys = 0;
    printk("[%s]: %d: enter, target station = %d\n", __func__, __LINE__, target_station);
    if(target_station == 0)
    {
        printk("[%s]: %d: get dma1 pdev\n", __func__, __LINE__);
        pdev = ntb_cv_get_dma1_dev();
    }
    else if(target_station == 1)
    {
        printk("[%s]: %d: get dma0 pdev\n", __func__, __LINE__);
        pdev = ntb_cv_get_dma0_dev();
    }
    else{
        printk("[%s]: %d: get dma else\n", __func__, __LINE__);
        return 0;
    }
    if(!pdev)
    {
        printk("[%s]: %d: get dma failed\n", __func__, __LINE__);
        return 0;
    }
    printk("[%s]: %d: get dma successful\n", __func__, __LINE__);


    phys = pci_resource_start(pdev, 0);
	return phys;
}

/*server???client?????????*/
static void server_client_req_win_phys_addr(uint32_t target_station, struct test_packet *rev_packet)
{
    unsigned long long phys_addr;
    int ret;
    struct test_packet *packet = NULL;
    uint32_t order = 0;
    void *p = NULL;
    gfp_t flags = GFP_KERNEL;
    
    printk("[%s]: %d: enter\n", __func__, __LINE__);
    switch (rev_packet->case_num)
    {
    
    case CV_NTB_CASE_07:
        
        order = 0;
        break;
    case CV_NTB_CASE_08:  /*max size dir win*/
        
        order = 0;
        break;
    case CV_NTB_CASE_09:  /*max size dir win*/
        
        order = 0;
        break;
    case CV_NTB_CASE_10:  /*max size dir win*/
        
        order = 0;
        break;
    case CV_NTB_CASE_11:  /*32 lut*/
        order = 0;
        break;
    case CV_NTB_CASE_12:  /*dir 1m*/
        order = 10;
        break;
    case CV_NTB_CASE_13:  /*dir 1m后边界*/
        order = 10;
        break;
    case CV_NTB_CASE_15:
    case CV_NTB_CASE_16:
        phys_addr = get_local_dma_phys(target_station);
        printk("[%s]: %d: phys addr = %llx\n", __func__, __LINE__, phys_addr);
        goto resp_phys;
    case CV_NTB_CASE_17:
        order = 10;
        break;
    case CV_NTB_CASE_18:
        order = 10;
        break;
    case CV_NTB_CASE_20:
        order = 10;
        break;


    default:
        break;
    }
    if(rev_packet->dma_32)
    {
        flags |= GFP_DMA32;
    }
    p = (void *)__get_free_pages(flags, order);
    if(!p)
    {
        return;
    }
    phys_addr = virt_to_phys(p);
    
resp_phys:
   
    switch (rev_packet->case_num)
    {
 
    case CV_NTB_CASE_08:
        memcpy(p, g_case08_msg, sizeof(g_case08_msg)); 
        break;
    case CV_NTB_CASE_10:
        memcpy(p, g_case10_msg, sizeof(g_case10_msg));
        break;
    case CV_NTB_CASE_20:
        memcpy(p, g_case20_msg, sizeof(g_case20_msg));
        break;

    default:
        break;
    }


    printk("[%s]: %d: enter, p = %p, phys_addr = %llx\n", __func__, __LINE__, p, phys_addr);
    ret = build_packet(&packet, SERVER_RESP_WIN_PHYS_ADDR, rev_packet->case_num, 0, 0, phys_addr);
    if(ret)
    {
        printk("[%s]: build packet failed\n", __func__);
        return;
    }

    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: send_pipe_msg failed\n", __func__);
        return;
    }
    
    printk("[%s]: send_pipe_msg successful\n", __func__);
    free_packet(packet);
}

/*server???client???????server???????case???????crc???????deal ret=0*/
static void server_client_write_ok_deal(uint32_t target_station, struct test_packet *recv_packet)
{
    struct test_packet *packet = NULL;
    int ret;
    void *p = NULL, *tmp_p = NULL;
    size_t size = 0;
    uint32_t crc_val;
    switch (recv_packet->case_num)
    {
  

    case CV_NTB_CASE_07:
        size = sizeof(g_case07_msg);
        break;
    case CV_NTB_CASE_09:
        size = sizeof(g_case09_msg);
        break;
    case CV_NTB_CASE_12:
        size = sizeof(g_case12_msg);
        break;
    case CV_NTB_CASE_13:
        size = 1024*1024;
        break;
    case CV_NTB_CASE_17:
        size = sizeof(g_case17_msg);
        break;
    default:
	return;

    }
    
   
    p = phys_to_virt(recv_packet->p_addr);
    printk("[%s]: %d: p = %lx, size = %ld", __func__, __LINE__, (unsigned long)p, size);
    if(recv_packet->case_num == CV_NTB_CASE_13)
    {
        tmp_p = (uint8_t *)p + size - sizeof(g_case13_msg);
        size = sizeof(g_case13_msg);
    }
    else{
        tmp_p = p;
    }
    printk("[%s]: %d: tmp_p = %lx, size = %ld", __func__, __LINE__, (unsigned long)tmp_p, size);
    crc_val = crc32_be(CRC_VAL, (uint8_t *)tmp_p, size);
    printk("[%s]: %d recv client send paddr= %llx, ioremap buf = %s, crc val = %d, tmp p = %s\n", __func__, __LINE__, recv_packet->p_addr, (char *)p, crc_val, (char *)tmp_p);
   
    ret = build_packet(&packet, SERVER_RESP_WIN_ADDR_CRC, recv_packet->case_num, crc_val, 0, 0);
    if(ret)
    {
        printk("[%s]: build packet failed\n", __func__);
        return;
    }
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: send_pipe_msg failed\n", __func__);
       
    }

    
    free_packet(packet);
}

static void client_server_resp_win_phys_addr(uint32_t target_station, unsigned long long phys_addr)
{  
    g_client_recv_addr = phys_addr;
    complete(&comp);
}

/*client??server???crc,comp??????client???????crc?packet crc*/
static void client_server_resv_win_addr_crc(uint32_t target_station, struct test_packet *recv_packet)
{
    g_crc_val = recv_packet->crc_val;
    complete(&comp);
     
}

static void client_server_resp_read_ok_ret(uint32_t target_station, struct test_packet *recv_packet)
{
    printk("[%s]: %d: del ret = %d\n", __func__, __LINE__, recv_packet->ret);
    g_deal_ret = recv_packet->ret;
    complete(&comp);
     
}

static int server_get_dma_buf_crc(uint32_t target_station)
{
    struct pci_dev *pdev = NULL;
    void __iomem *bar = 0;
    unsigned long res_start, res_len;
    uint32_t crc_val;
	printk("[%s]: %d: target_station is %dn", __func__, __LINE__, target_station);
    if(target_station == 0)
    {
        pdev = ntb_cv_get_dma1_dev();
    }
    else if(target_station == 1)
    {
        pdev = ntb_cv_get_dma0_dev();
    }
    else{
        return -1;
    }
    
    if(!pdev)
    {
        return -1;
    }


    res_start = pci_resource_start(pdev, 0);
    res_len = pci_resource_len(pdev, 0);
    
    bar = (void *)ioremap(res_start, res_len);
    if(!bar)
    {
	    return -1;
    }


    printk("[%s]: %d: bar + 0x124 = %d\n", __func__, __LINE__, *(uint32_t *)(bar + 0x124));
    crc_val =  crc32_be(CRC_VAL, (uint8_t *)(bar + 0x124), sizeof("chen"));

    *(uint32_t *)(bar + 0x124) = 0;
    iounmap(bar);

    return crc_val;

}

static void server_client_read_ok_deal(uint32_t target_station, struct test_packet *recv_packet)
{
    uint32_t crc_val;
    int deal_ret = 0, ret;
    struct test_packet *packet = NULL;
    switch (recv_packet->case_num)
    {
    case CV_NTB_CASE_01:
        break;
    case CV_NTB_CASE_02:
        break;


    case CV_NTB_CASE_08:
        crc_val = crc32_be(CRC_VAL, g_case08_msg, sizeof(g_case08_msg));
        break;
    case CV_NTB_CASE_10:
        crc_val = crc32_be(CRC_VAL, g_case10_msg, sizeof(g_case10_msg));
        break;
    case CV_NTB_CASE_15:
    case CV_NTB_CASE_16:
		printk("will get dma buf crc-----------\n");
        crc_val = server_get_dma_buf_crc(target_station);
		printk("get dma buf crc end-----------\n");
        break;
   
    default:
        break;
    }
    printk("[%s]: %d: recv crc= %d, local crc = %d\n", __func__, __LINE__, recv_packet->crc_val, crc_val);
    if(recv_packet->crc_val != crc_val)
    {
        deal_ret = -1;
    }
    build_packet(&packet, SERVER_RESP_READ_OK_RET, recv_packet->case_num, 0, deal_ret, 0);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: send_pipe_msg failed\n", __func__);
        
    }
    free_packet(packet);
}

static void server_client_all_end(uint32_t target_station, struct test_packet *recv_packet)
{
    uint32_t order = 0;
    switch (recv_packet->case_num)
    {
   
    case CV_NTB_CASE_07:
        order = 0;
        break;
    case CV_NTB_CASE_08:
        order = 0;
        break;
    case CV_NTB_CASE_09:
        order = 0;
        break;
    case CV_NTB_CASE_10:
        order = 0;
        break;
    case CV_NTB_CASE_11:
        order = 0;
        break;
    case CV_NTB_CASE_12:
        order = 10;
        break;
    case CV_NTB_CASE_13:
        order = 10;
        break;
    case CV_NTB_CASE_15:
        printk("[%s]: %d: case 15 end\n", __func__, __LINE__);
		return;
    case CV_NTB_CASE_16:
        printk("[%s]: %d: case 16 end\n", __func__, __LINE__);
		return;
    case CV_NTB_CASE_17:
        order = 10;
        break;
    case CV_NTB_CASE_18:
        order = 10;
        break;




    default:
		return;
    }
    ssleep(1);
    printk("[%s]: %d: end\n", __func__, __LINE__);
    if(recv_packet->p_addr)
        free_pages((unsigned long)phys_to_virt((phys_addr_t )recv_packet->p_addr), order);
}

static int server_ntb_case_29(uint8_t target_station)
{
    
    int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
    
    
    struct test_packet *packet = NULL;
    struct pci_dev *dma_pdev = NULL, *ntb_pdev = NULL;
    int i =0;
    void *p = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_29);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }

  

    ret = sudo_alloc_dir_map_win(target_station, remote_addr, 0xffff, &local_addr, &size);
    if(ret)
    {
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }

    if(target_station == 0)
    {
        dma_pdev = ntb_cv_get_dma1_dev();
    }
    else{
        dma_pdev = ntb_cv_get_dma0_dev();
    }
   

    ntb_pdev = ntb_cv_get_ntb_dev();
    if(!ntb_pdev || !dma_pdev)
    {
        printk("[%s]: %d: get failed, ntb dev = %p, dma0 pdev = %p\n", __func__, __LINE__, ntb_pdev, dma_pdev);
        goto final;
    }

    printk("[%s]: %d: get dma ok\n", __func__, __LINE__);
    
    sudo_ntb_set_req_id(0x0);
    sudo_ntb_set_req_id(0x800);  /*dma id*/
    ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }

   

    p = (void *)__get_free_pages(GFP_KERNEL, 10);
    if(!p)
    {
        printk("[%s]: %d: __get_free_pages fialed\n", __func__, __LINE__);
        return -1;
    }
    
    for(i = 0; i< 1000; i++)
    {
 
        yd_dma_cv_common(&ntb_pdev->dev, "tx", local_addr, virt_to_phys(p), 4096, 0, 0);
    }
  

final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_29, 0, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);

    sudo_free_dir_map_win(target_station, local_addr);
    sudo_ntb_clear_req_id(0x00);
    sudo_ntb_clear_req_id(0x800);
   
    kfree(p);
    return ret;

}

static void server_ntb_case_30(void)
{

}

static void server_client_run_server_pro(uint32_t target_station, struct test_packet *recv_packet)
{
   
    switch (recv_packet->case_num)
    {
    case CV_NTB_CASE_29:
        server_ntb_case_29(target_station);
        break;
    case CV_NTB_CASE_30:
        server_ntb_case_30();
        break;
    default:
        break;
    }
   

}

static uint32_t g_server_nt_bus = 0;

static void ntf_internal_server_recv_nt_bus(uint32_t target_station, uint32_t dsp_nt_bus)
{
    struct test_packet *packet = NULL;
    int ret;
    sudo_ntf_internal_nt_bus_set(src_fabric_station, dst_fabric_station, 0);
    build_packet(&packet, NTF_CLIENT_RECV_RESP_NT_BUS, 1, 0, 0, g_server_nt_bus);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg NTF_CLIENT_RECV_RESP_NT_BUS failed\n", __func__, __LINE__);
    
    }
    free_packet(packet);
}


static void ntf_internal_client_recv_nt_bus(uint32_t target_station, uint32_t dsp_nt_bus)
{
    sudo_ntf_internal_nt_bus_set(src_fabric_station, dst_fabric_station, 0);
    complete(&comp);
}

static void db_callback(uint8_t cb_result, uint32_t target_station, uint8_t db_num, void *cb_arg)
{
    printk("[%s]: recv target id = %d, db num = %d\n", __func__, target_station, db_num);
}
static void msg_callback(uint8_t cb_result, uint32_t target_station, uint8_t *data, size_t size, void *cb_arg)
{

    struct test_packet *packet = (struct test_packet *)data;
    printk("[%s]: %d: enter\n", __func__, __LINE__);
    if(size != sizeof(struct test_packet))
    {
        printk("[%s]: packet check failed, size = %ld, packet size is %ld\n", __func__, size, sizeof(struct test_packet));
        return;
    }
    printk("[%s]: %d: case num = %d, packet size = %ld\n", __func__, __LINE__, packet->case_num, size);
    switch (packet->command)
    {
    case CLIENT_REQ_WIN_PHYS_ADDR:
        printk("[%s]: CLIENT_REQ_WIN_PHYS_ADDR\n", __func__);
        server_client_req_win_phys_addr(target_station, packet);
        /* code */
        break;
    case SERVER_RESP_WIN_PHYS_ADDR:
        printk("[%s]: SERVER_RESP_WIN_PHYS_ADDR\n", __func__);
        client_server_resp_win_phys_addr(target_station, packet->p_addr);
        break;
    case CLIENT_WRITE_OK:
        printk("[%s]: CLIENT_WRITE_OK\n", __func__);
        
        server_client_write_ok_deal(target_station, packet);
        break;
    case SERVER_RESP_WIN_ADDR_CRC:
        printk("[%s]: SERVER_RESP_WIN_ADDR_CRC\n", __func__);
        client_server_resv_win_addr_crc(target_station, packet);
        break;
    case CLIENT_READ_OK:
        printk("[%s]: CLIENT_READ_OK\n", __func__);
        server_client_read_ok_deal(target_station, packet);
        break;
    case SERVER_RESP_READ_OK_RET:
        printk("[%s]: SERVER_RESP_READ_OK_RET\n", __func__);
        client_server_resp_read_ok_ret(target_station, packet);
        break;
    case CLIENT_ALL_END:
        printk("[%s]: CLIENT_ALL_END\n", __func__);
        server_client_all_end(target_station, packet);
       
        break;
    case CLIENT_RUN_SERVER_PRO:
        
        printk("[%s]: CLIENT_RUN_SERVER_PRO\n", __func__);
        server_client_run_server_pro(target_station, packet);

        break;
    case NTF_SERVER_RECV_REQ_NT_BUS:
        printk("[%s]: NTF_SERVER_RECV_NT_BUS", __func__);
        ntf_internal_server_recv_nt_bus(target_station, (uint32_t)(packet->p_addr)); /*p_addr 复用nt bus*/
        break;
    case NTF_CLIENT_RECV_RESP_NT_BUS:
        printk("[%s]: NTF_CLIENT_RESP_NT_BUS", __func__);
        ntf_internal_client_recv_nt_bus(target_station, (uint32_t)(packet->p_addr));
        break;
    default:
        printk("[%s]: invalid command", __func__);
        return;
        break;
    }
    
    return;
}

enum ntb_win_type{
    NTB_WIN_LUT,
    NTB_WIN_DIR,
};


static void get_win_info(void)
{
    size_t lut_size, dir_size;
    uint8_t req_id_cnt;
    lut_size = sudo_ntb_get_lut_size();
    dir_size = sudo_ntb_get_dir_size();
    req_id_cnt = sudo_ntb_free_req_id_cnt();
    printk("[%s]: the lut size = %ld, dir size = %ld, req id cnt = %d\n", __func__, lut_size, dir_size, req_id_cnt);
}

static int ntb_cv_get_remote_paddr(uint32_t target_station, unsigned long long *remote_addr, uint32_t case_num)
{
    struct test_packet *packet = NULL;
    int ret;
    if(test_case == CV_NTB_CASE_14)
    {
        ret = build_packet(&packet, CLIENT_REQ_WIN_PHYS_ADDR, case_num, 0, PAKCET_DMA_32_FLAG, 0);
    }
    else{
        ret = build_packet(&packet, CLIENT_REQ_WIN_PHYS_ADDR, case_num, 0, 0, 0);
    }
    if(ret)
    {
        return -1;
    }
    printk("[%s]: %d: enter\n", __func__, __LINE__);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg CLIENT_REQ_WIN_PHYS_ADDR failed\n", __func__, __LINE__);
        return -1;
    }
    free_packet(packet);
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server p addr time out\n", __func__, __LINE__);
        return -1;
    }
    printk("[%s]: %d: after wait_for_completion_timeout,  g_client_recv_addr = %llx\n", __func__, __LINE__, g_client_recv_addr);
    *remote_addr = g_client_recv_addr;
    return 0;
}


static int ntb_cv_04(uint32_t target_station)       
{
    int ret = -1;
    char tmp_buf[] = "hello";
    ret = sudo_ntb_send_msg(target_station, TEST_PIPE_ID, tmp_buf, sizeof(tmp_buf));
    if(ret)
    {
        printk("[%s]: %d: sudo_ntb_send_msg failed\n\n", __func__, __LINE__);
        return -1;
    }

    return 0;
}

static int ntb_cv_05(uint32_t target_station)     
{
    int ret = -1;
    // ret = sudo_ntb_knock_doorbell(target_station, 0);
    // if(ret)
    // {
    //     printk("[%s]: %d: sudo_ntb_knock_doorbell station %d failed\n", __func__, __LINE__, target_station);
    // }
    // ssleep(2);
    // ret = sudo_ntb_knock_doorbell(target_station, 2);
    // if(ret)
    // {
    //     printk("[%s]: %d: sudo_ntb_knock_doorbell station %d failed\n", __func__, __LINE__, target_station);
    // }
    ret = sudo_ntb_knock_doorbell(target_station, 1);
    if(ret)
    {
        printk("[%s]: %d: sudo_ntb_knock_doorbell station %d failed\n", __func__, __LINE__, target_station);
    }
    return 0;
}

static int ntb_cv_rc_reqid_set(void)
{
    int ret;
    ret = sudo_ntb_set_req_id(TEST_REQ_ID);
    if(ret < 0) 
    {
        printk("[%s]: %d: sudo_ntb_set_req_id rc failed\n", __func__, __LINE__);
        return ret;
    }

    ret = sudo_ntb_set_req_id(0x1700);
    if(ret < 0)
    {
        printk("[%s]: %d: sudo_ntb_set_req_id rp failed\n", __func__, __LINE__);
        return ret;
    }
    return 0;
}



static int ntb_cv_07(uint32_t local_station, uint32_t target_station)
{
    int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
    void *map_addr = NULL;
    
    uint32_t crc_val;
    struct test_packet *packet = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_07);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }

    ret = sudo_alloc_lut_map_win(target_station, remote_addr, sizeof(g_case07_msg), &local_addr, &size);
    if(ret)
    {
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }
    ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }

    map_addr = (void *)ioremap(local_addr, size);

    memcpy(map_addr, g_case07_msg, sizeof(g_case07_msg));
    
    crc_val = crc32_be(CRC_VAL, (uint8_t *)g_case07_msg, sizeof(g_case07_msg));
   
    build_packet(&packet, CLIENT_WRITE_OK, CV_NTB_CASE_07, crc_val, 0, remote_addr);
    
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    /*??server???crc*/
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        goto final;
    }
    
    if(g_crc_val == crc_val)
    {
        ret = 0;
        printk("[%s]: %d: g_crc_val ==  crc_val\n", __func__, __LINE__);
    }
    else{
        ret = -1;
        printk("[%s]: %d: crc_val = %d, g_crc_val = %d\n", __func__, __LINE__, crc_val, g_crc_val);
    
    }
final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_05, 0, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    sudo_free_lut_map_win(target_station, local_addr);
    sudo_ntb_clear_req_id(0x0);
    sudo_ntb_clear_req_id(0x1700);
    return ret;
}

static int ntb_cv_08(uint32_t local_station, uint32_t target_station)
{
    int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
    void *map_addr = NULL;
    char tmp_buf[32] = {0};
    uint32_t crc_val;
    struct test_packet *packet = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_08);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }

    ret = sudo_alloc_lut_map_win(target_station, remote_addr, sizeof(g_case08_msg), &local_addr, &size);
    if(ret)
    {
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }
    ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }

    map_addr = (void *)ioremap(local_addr, size);
    memcpy(tmp_buf, map_addr, sizeof(g_case08_msg));
    
    crc_val = crc32_be(CRC_VAL, (uint8_t *)map_addr, sizeof(g_case08_msg));
    printk("[%s]: %d: will build_packet , command = %d, case num = %d\n", __func__, __LINE__, CLIENT_READ_OK, CV_NTB_CASE_08);
    
    build_packet(&packet, CLIENT_READ_OK, CV_NTB_CASE_08, crc_val, 0, remote_addr);
    
  
    printk("[%s]: %d:  build_packet end , command = %d, case num = %d\n", __func__, __LINE__, packet->command, packet->case_num);
    printk("[%s]: %d: in for, val = %x\n", __func__, __LINE__, *(uint32_t *)(&packet));
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    
    /*??server???ret ok*/
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        goto final;
    }
    free_packet(packet);
    if(g_deal_ret == 0)
    {
        ret = 0;
        printk("[%s]: %d: g_deal_ret = 0\n", __func__, __LINE__);
    }
    else{
        ret = -1;
        printk("[%s]: %d: g_deal_ret = %d\n", __func__, __LINE__, g_deal_ret);
    
    }
final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_08, 0, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    sudo_free_lut_map_win(target_station, local_addr);
    sudo_ntb_clear_req_id(0x0);
    sudo_ntb_clear_req_id(0x1700);
    return ret;
}


static int ntb_cv_09(uint32_t local_station, uint32_t target_station)        
{
        int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
    void *map_addr = NULL;
    
    uint32_t crc_val;
    struct test_packet *packet = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_09);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }

    ret = sudo_alloc_dir_map_win(target_station, remote_addr, 0xffff, &local_addr, &size);
    if(ret)
    {
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }
    ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }

    map_addr = (void *)ioremap(local_addr, size);

    memcpy(map_addr, g_case09_msg, sizeof(g_case09_msg));
    
    crc_val = crc32_be(CRC_VAL, (uint8_t *)g_case09_msg, sizeof(g_case09_msg));

    build_packet(&packet, CLIENT_WRITE_OK, CV_NTB_CASE_09, crc_val, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        goto final;
    }
    
    if(g_crc_val == crc_val)
    {
        ret = 0;
        printk("[%s]: %d: g_crc_val ==  crc_val\n", __func__, __LINE__);
    }
    else{
        ret = -1;
        printk("[%s]: %d: crc_val = %d, g_crc_val = %d\n", __func__, __LINE__, crc_val, g_crc_val);
    
    }
final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_06, 0, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    sudo_free_dir_map_win(target_station, local_addr);
    sudo_ntb_clear_req_id(0x0);
    sudo_ntb_clear_req_id(0x1700);
    return ret;
}

static int ntb_cv_10(uint32_t local_station, uint32_t target_station) 
{
    int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
    void *map_addr = NULL;
    char tmp_buf[32] = {0};
    uint32_t crc_val;
    struct test_packet *packet = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_10);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }
   
    ret = sudo_alloc_dir_map_win(target_station, remote_addr, 0xffff, &local_addr, &size);
    if(ret)
    {   
        goto final;
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }
   
    ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }
   
    map_addr = (void *)ioremap(local_addr, size);
  
    memcpy(tmp_buf, map_addr, sizeof(g_case10_msg));
   
    crc_val = crc32_be(CRC_VAL, (uint8_t *)map_addr, sizeof(g_case10_msg));
   
    build_packet(&packet, CLIENT_READ_OK, CV_NTB_CASE_10, crc_val, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        goto final;
    }
    if(g_deal_ret == 0)
    {
        ret = 0;
        printk("[%s]: %d: g_deal_ret = 0\n", __func__, __LINE__);
    }
    else{
        ret = -1;
        printk("[%s]: %d: g_deal_ret = %d\n", __func__, __LINE__, g_deal_ret);
    
    }
final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_10, 0, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    sudo_free_dir_map_win(target_station, local_addr);
    sudo_ntb_clear_req_id(0x0);
    sudo_ntb_clear_req_id(0x1700);
    return ret;
}





static int ntb_cv_11(uint32_t local_station, uint32_t target_station)  
{
    
    int ret, i;
    unsigned long long remote_addr[32];
    unsigned long long local_addr[32];
    void *map_addr[32];
    size_t size = 0;
    char write_buf[64] = {0};
    char read_buf[64] = {0};
    struct test_packet *packet = NULL;
    ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }
    for(i = 0; i < 32; i++)
    {
        ret = ntb_cv_get_remote_paddr(target_station, &remote_addr[i], CV_NTB_CASE_11);
        if(ret)
        {
            printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
            return ret;
        }
        ret = sudo_alloc_lut_map_win(target_station, remote_addr[i], sizeof(write_buf), &local_addr[i], &size);
        if(ret)
        {
            printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
            return ret;
        }
        map_addr[i] = ioremap(local_addr[i], size);

    }
    for(i = 0; i < 32; i++)
    {
        memset(write_buf, 0, 64);
        sprintf(write_buf, "case07:%d", i);
        memcpy(map_addr[i], write_buf, strlen(write_buf));
        memcpy(read_buf, map_addr[i], strlen(write_buf));
        printk("[%s]: %d: map addr = %s\n", __func__, __LINE__, (char *)map_addr[i]);
        if(strncmp(write_buf, read_buf, strlen(write_buf)) !=0)
        {
            printk("[%s]: %d: i = %d, write buf = %s, strncmp failed\n", __func__, __LINE__, i, write_buf);
        }
    }

    for(i = 0; i < 32; i++)
    {
        build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_11, 0, 0, remote_addr[i]);
        ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
        if(ret)
        {
            printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
        }
        free_packet(packet);
        sudo_free_lut_map_win(target_station, local_addr[i]);
        
    }
    sudo_ntb_clear_req_id(0x0);
    sudo_ntb_clear_req_id(0x1700);
   return 0;

}

static int ntb_cv_12_bak(uint32_t local_station, uint32_t target_station)  /*边界测试ide*/
{
    int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
    void *map_addr = NULL;
    
    uint32_t crc_val;
    struct test_packet *packet = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_06);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }

    ret = sudo_alloc_dir_map_win(target_station, remote_addr, 1024*1024, &local_addr, &size);
    if(ret)
    {
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }
    ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }

    map_addr = (void *)ioremap(local_addr, size);

    memcpy(map_addr, g_case12_msg, sizeof(g_case12_msg));
    memcpy(map_addr + 1024, g_case12_msg, sizeof(g_case12_msg));
    printk("[%s]: %d: map base = %s, map + 1024 = %s\n", __func__, __LINE__, (char *)map_addr, (char *)(map_addr + 1024));
    crc_val = crc32_be(CRC_VAL, (uint8_t *)map_addr, 1024 + sizeof(g_case08_msg));

    build_packet(&packet, CLIENT_WRITE_OK, CV_NTB_CASE_08, crc_val, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    /*??server???crc*/
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        goto final;
    }
    
    if(g_crc_val == crc_val)
    {
        ret = 0;
        printk("[%s]: %d: g_crc_val ==  crc_val\n", __func__, __LINE__);
    }
    else{
        ret = -1;
        printk("[%s]: %d: crc_val = %d, g_crc_val = %d\n", __func__, __LINE__, crc_val, g_crc_val);
    
    }
final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_08, 0, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    sudo_free_dir_map_win(target_station, local_addr);
    sudo_ntb_clear_req_id(0x0);
    sudo_ntb_clear_req_id(0x1700);
    return ret;
}



static int ntb_cv_12(uint32_t local_station, uint32_t target_station)  /*h*/
{
    int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
    void *map_addr = NULL;
    
    uint32_t crc_val;
    struct test_packet *packet = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_12);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }

    ret = sudo_alloc_dir_map_win(target_station, remote_addr, 1024*1024, &local_addr, &size);
    if(ret)
    {
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }
    ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }

    map_addr = (void *)ioremap(local_addr, size);

    memcpy(map_addr, g_case12_msg, sizeof(g_case12_msg));

    crc_val = crc32_be(CRC_VAL, (uint8_t *)map_addr,  sizeof(g_case12_msg));

    build_packet(&packet, CLIENT_WRITE_OK, CV_NTB_CASE_12, crc_val, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    /*??server???crc*/
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        goto final;
    }
    
    if(g_crc_val == crc_val)
    {
        ret = 0;
        printk("[%s]: %d: g_crc_val ==  crc_val\n", __func__, __LINE__);
    }
    else{
        ret = -1;
        printk("[%s]: %d: crc_val = %d, g_crc_val = %d\n", __func__, __LINE__, crc_val, g_crc_val);
    
    }
final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_12, 0, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    sudo_free_dir_map_win(target_station, local_addr);
    sudo_ntb_clear_req_id(0x0);
    sudo_ntb_clear_req_id(0x1700);
    return ret;
}

static int ntb_cv_13(uint32_t local_station, uint32_t target_station) 
{
    int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
    void *map_addr = NULL;
    
    uint32_t crc_val;
    struct test_packet *packet = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_13);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
        return -1;
    }

    ret = sudo_alloc_dir_map_win(target_station, remote_addr, 1024*1024, &local_addr, &size);
    if(ret)
    {
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }
    printk("[%s]: %d: size = %ld\n", __func__, __LINE__, size);
    ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }

    map_addr = (void *)ioremap(local_addr, size);
    printk("[%s]: %d: map addr base = %llx, +after=%llx, size = %ld\n", __func__, __LINE__, (uint64_t)map_addr, (uint64_t)(map_addr+size-sizeof(g_case13_msg)), size);
    memcpy((uint8_t *)map_addr+size-sizeof(g_case13_msg), g_case13_msg, sizeof(g_case13_msg));
    
    crc_val = crc32_be(CRC_VAL, (uint8_t *)g_case13_msg, sizeof(g_case13_msg));

    build_packet(&packet, CLIENT_WRITE_OK, CV_NTB_CASE_13, crc_val, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    /*??server???crc*/
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        goto final;
    }
    
    if(g_crc_val == crc_val)
    {
        ret = 0;
        printk("[%s]: %d: g_crc_val ==  crc_val\n", __func__, __LINE__);
    }
    else{
        ret = -1;
        printk("[%s]: %d: crc_val = %d, g_crc_val = %d\n", __func__, __LINE__, crc_val, g_crc_val);
    
    }
final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_13, 0, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    sudo_free_dir_map_win(target_station, local_addr);
    sudo_ntb_clear_req_id(0x0);
    sudo_ntb_clear_req_id(0x1700);
    return ret;
}
static int ntb_cv_14(uint32_t local_station, uint32_t target_station) 
{
    int ret = -1;
    ret = ntb_cv_07(local_station, target_station);
    if(ret)
    {
        return ret;
    }
    ret = ntb_cv_08(local_station, target_station);
    if(ret)
    {
        return ret;
    }
    ret = ntb_cv_09(local_station, target_station);
    if(ret)
    {
        return ret;
    }
    ret = ntb_cv_10(local_station, target_station);
    if(ret)
    {
        return ret;
    }
    return 0;
}


/*
  对端将dma ep bar地址提供给本端，group分区时，将dma0分配到对端group。测试程序通过doorbell和msg机制向对端group
  申请对应dma0得总线地址，本端收到dma0总线地址后，配置到对应开窗中，并且将rc和usp得bdf设置到req id里，然后对开窗写入
  对应case指定字符串，并计算此字符串哈希值，将哈希值发送给对端，对端将dma0 bar0对应开窗地址得内容进行哈希值计算，与本端
  传入得哈希值进行比较，成功反给本端0，不成功反给本端非0值*/

static int ntb_cv_15(uint32_t local_station, uint32_t target_station)  /*Ch rc to ep*/
{

    int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
    void *map_addr = NULL;
   
    uint32_t crc_val;
    struct test_packet *packet = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_15);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }

    ret = sudo_alloc_lut_map_win(target_station, remote_addr, sizeof(g_case03_msg), &local_addr, &size);
    if(ret)
    {
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }

    sudo_ntb_set_req_id(0x0);

    map_addr = (void *)ioremap(local_addr, size);
    memcpy((map_addr+0x124), "chen", sizeof("chen"));
    printk("[%s]: %d map 0x124 buf is %x", __func__, __LINE__, *(uint32_t *)(map_addr+0x124));
    
    crc_val = crc32_be(CRC_VAL, (uint8_t *)(map_addr+0x124), sizeof("chen"));

    build_packet(&packet, CLIENT_READ_OK, CV_NTB_CASE_15, crc_val, 0, remote_addr);
    ssleep(1);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        goto final;
    }
    free_packet(packet);
    if(g_deal_ret == 0)
    {
        ret = 0;
        printk("[%s]: %d: g_deal_ret = 0\n", __func__, __LINE__);
    }
    else{
        ret = -1;
        printk("[%s]: %d: g_deal_ret = %d\n", __func__, __LINE__, g_deal_ret);
    
    }
final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_15, 0, 0, remote_addr);
    ssleep(1);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    sudo_free_lut_map_win(target_station, local_addr);
    sudo_ntb_clear_req_id(0x0);
    return ret;
}



/*group分区时，将dma0分配到本端groupdma1分配到对端group。测试程序通过doorbell和msg机制向对端group申请对应dma1得总线地址，
  本端收到dma1总线地址后，配置到对应开窗中，并且将本端dma0得bdf设置到req id里，host配置dma读写该开窗地址，并且将写入得指定字
  符串计算哈希值，将哈希值发送给对端，对端将dma1 bar0对应开窗地址得内容进行哈希值计算，与本端传入得哈希值进行比较，成功反给本端0，不成功反给本端非0值*/
static int ntb_cv_16(uint32_t local_station, uint32_t target_station)  /*ep to ep*/
{
    int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
    
    
    uint32_t crc_val;
    struct test_packet *packet = NULL;
    struct pci_dev *dma_pdev = NULL, *ntb_pdev = NULL;

    void *p = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_16);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
        return -1;
    }

    ret = sudo_alloc_lut_map_win(target_station, remote_addr, 0x10, &local_addr, &size);
    if(ret)
    {
        printk("[%s]: %d: sudo_alloc_dir_map_win failed\n", __func__, __LINE__);
         return -1;
    }

    if(local_station == 0)
    {
        printk("[%s]: %d get dma0 dev\n", __func__, __LINE__);
        dma_pdev = ntb_cv_get_dma0_dev();
    }
    else if(local_station == 1)
    {
        printk("[%s]: %d get dma1 dev\n", __func__, __LINE__);
        dma_pdev = ntb_cv_get_dma1_dev();
    }
    if(!dma_pdev)
    {
        goto final;
    }

    ntb_pdev = ntb_cv_get_ntb_dev();
    if(!ntb_pdev)
    {
        goto final;
    }

    printk("[%s]: %d: the dma devfn = %x\n", __func__, __LINE__, request_bdf);
    sudo_ntb_set_req_id(request_bdf);

    p = (void *)__get_free_pages(GFP_KERNEL | GFP_DMA32, 10);
    if(!p)
    {
        printk("[%s]: %d: __get_free_pages fialed\n", __func__, __LINE__);
        return -1;
    }

    memcpy(p, "chen", sizeof("chen"));
    printk("[%s]: %d: remote dma addr phys = %llx, p = %s\n", __func__, __LINE__, remote_addr, (char *)p);
    yd_dma_cv_common(&ntb_pdev->dev, "tx", virt_to_phys(p), local_addr + 0x124, 4, 0, 1);
    ssleep(1);
    crc_val = crc32_be(CRC_VAL, (uint8_t *)p, sizeof("chen"));

    build_packet(&packet, CLIENT_READ_OK, CV_NTB_CASE_16, crc_val, 0, remote_addr);

    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        goto final;
    }
    free_packet(packet);
    if(g_deal_ret == 0)
    {
        ret = 0;
        printk("[%s]: %d: g_deal_ret = 0\n", __func__, __LINE__);
    }
    else{
        ret = -1;
        printk("[%s]: %d: g_deal_ret = %d\n", __func__, __LINE__, g_deal_ret);
    
    }
final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_16, 0, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);

    sudo_free_lut_map_win(target_station, local_addr);
    sudo_ntb_clear_req_id(request_bdf);
    return ret;
}


static int ntb_cv_17(uint32_t local_station, uint32_t target_station)  /*h ep to rc*/
{
    int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
   
    uint32_t crc_val;
    struct test_packet *packet = NULL;
    struct pci_dev *dma_pdev = NULL, *ntb_pdev = NULL;

    void *p = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_17);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }

    ret = sudo_alloc_dir_map_win(target_station, remote_addr, 0xffff, &local_addr, &size);
    if(ret)
    {
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }

    if(local_station == 0)
    {
        dma_pdev = ntb_cv_get_dma0_dev();
    }
    else if(local_station == 1)
    {
        dma_pdev = ntb_cv_get_dma1_dev();
    }
   
    if(!dma_pdev)
    {
        goto final;
    }
    ntb_pdev = ntb_cv_get_ntb_dev();
    if(!ntb_pdev)
    {
        goto final;
    }

    sudo_ntb_set_req_id(request_bdf);
    //ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }

    p = (void *)__get_free_pages(GFP_KERNEL, 10);
    if(!p)
    {
        printk("[%s]: %d: __get_free_pages fialed\n", __func__, __LINE__);
        return -1;
    }

    memcpy(p, g_case17_msg, sizeof(g_case17_msg));
    yd_dma_cv_common(&ntb_pdev->dev, "tx", virt_to_phys(p), local_addr,  0xffff, 0, 1);
    
    crc_val = crc32_be(CRC_VAL, (uint8_t *)p, sizeof(g_case18_msg));

    build_packet(&packet, CLIENT_WRITE_OK, CV_NTB_CASE_17, crc_val, 0, remote_addr);

    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        goto final;
    }
    free_packet(packet);
    if(g_crc_val == crc_val)
    {
        ret = 0;
        printk("[%s]: %d: g_deal_ret = 0\n", __func__, __LINE__);
    }
    else{
        ret = -1;
        printk("[%s]: %d: g_deal_ret = %d\n", __func__, __LINE__, g_deal_ret);
    
    }
final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_17, 0, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    //sudo_free_lut_map_win(target_station, local_addr);
    sudo_free_dir_map_win(target_station, local_addr);
    sudo_ntb_clear_req_id(request_bdf);
    return ret;
}



//#define TEST_ONE_WIN 0
/*两个dma往一个开窗写，测压力*/
static int ntb_cv_18(uint32_t local_station, uint32_t target_station)   /*h 2 dma to same win   h cv 18 19*/
{
    int ret;
    unsigned long long remote_addr1, remote_addr2;
    phys_addr_t local_addr1, local_addr2;
    size_t size;
   
   
    uint32_t crc_val1, crc_val2;
    struct test_packet *packet = NULL;
    struct pci_dev *dma0_pdev = NULL, *dma1_pdev = NULL, *ntb_pdev = NULL;

    void *p1 = NULL, *p2 = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr1, CV_NTB_CASE_20);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }

    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr2, CV_NTB_CASE_20);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }

    ret = sudo_alloc_lut_map_win(target_station, remote_addr1, sizeof(g_case20_msg), &local_addr1, &size);
    if(ret)
    {
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }

    ret = sudo_alloc_lut_map_win(target_station, remote_addr2, sizeof(g_case20_msg), &local_addr2, &size);
    if(ret)
    {
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }

   
    dma0_pdev = ntb_cv_get_dma0_dev();
   
    dma1_pdev = ntb_cv_get_dma1_dev();
   

    ntb_pdev = ntb_cv_get_ntb_dev();
    if(!ntb_pdev || !dma0_pdev || !dma1_pdev)
    {
    printk("[%s]: %d: get failed, ntb dev = %p, dma0 pdev = %p, dma1p dev= %p\n", __func__, __LINE__, ntb_pdev, dma0_pdev, dma1_pdev);
        goto final;
    }

    printk("[%s]: %d: get dma ok\n", __func__, __LINE__);
    sudo_ntb_set_req_id(0x700);
    sudo_ntb_set_req_id(0x800);
    ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {   
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }

    p1 = (void *)__get_free_pages(GFP_KERNEL, 10);
    if(!p1)
    {
        printk("[%s]: %d: __get_free_pages fialed\n", __func__, __LINE__);
        return -1;
    }

    p2 = (void *)__get_free_pages(GFP_KERNEL, 10);
    if(!p2)
    {
        printk("[%s]: %d: __get_free_pages fialed\n", __func__, __LINE__);
        return -1;
    }
    if(test_case == CV_NTB_CASE_18)
    {
        
    
        int i =0;
        for(i = 0; i< 100; i++)
        {
            printk("[%s]: %d: dma1 start t\n", __func__, __LINE__);
            dma0_pdev->dev.init_name = "SudoNtbEP";
            yd_dma_cv_common(&dma0_pdev->dev, "tx", local_addr1, virt_to_phys(p1), 4096, 0, 0);
    
            printk("[%s]: %d: dma2 start t\n", __func__, __LINE__);

            yd_dma_cv_common(&ntb_pdev->dev, "tx", local_addr1, virt_to_phys(p2), 4096, 0, 0);
        }
    }
    else{
       
        dma0_pdev->dev.init_name = "SudoNtbEP";
        printk("[%s]: %d: dma1 start t\n", __func__, __LINE__);
        yd_dma_cv_common(&dma0_pdev->dev, "tx", local_addr1, virt_to_phys(p1), sizeof(g_case20_msg), 0, 0);
    
        printk("[%s]: %d: dma2 start t\n", __func__, __LINE__);

        yd_dma_cv_common(&ntb_pdev->dev, "tx", local_addr2, virt_to_phys(p2), sizeof(g_case20_msg), 0, 0);

       
        crc_val1 = crc32_be(CRC_VAL, (uint8_t *)p1, sizeof(g_case20_msg));


        crc_val2 = crc32_be(CRC_VAL, (uint8_t *)p2, sizeof(g_case20_msg));

        printk("[%s]: %d: p1 = %s, p2 = %s\n", __func__, __LINE__, (char *)p1, (char *)p2);

        if(crc_val1 == crc_val2)
        {
            printk("[%s]: %d: win ok\n", __func__, __LINE__);
        }
        else{
            printk("[%s]: %d: win failed\n", __func__, __LINE__);
        }
    }
    //build_packet(&packet, CLIENT_READ_OK, CV_NTB_CASE_20, crc_val, 0, remote_addr);
/*
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        goto final;
    }
    free_packet(packet);
    if(g_deal_ret == 0)
    {
        ret = 0;
        printk("[%s]: %d: g_deal_ret = 0\n", __func__, __LINE__);
    }
    else{
        ret = -1;
        printk("[%s]: %d: g_deal_ret = %d\n", __func__, __LINE__, g_deal_ret);
    
    }
*/
final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_20, 0, 0, remote_addr1);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);

    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_20, 0, 0, remote_addr2);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);

    sudo_free_lut_map_win(target_station, local_addr1);
    sudo_free_lut_map_win(target_station, local_addr2);
    sudo_ntb_clear_req_id(0x700);
    sudo_ntb_clear_req_id(0x800);
    kfree(p1);
    kfree(p2);
    return ret;
    return 0;
}

static int ntb_cv_19(uint32_t local_station, uint32_t target_station) 
{
    return ntb_cv_18(local_station, target_station);
}

static int ntb_cv_58(uint32_t local_station, uint32_t target_station)  /*h 58*/
{
    int ret = 0;
    void __iomem *bar = 0;
    unsigned long res_start, res_len;
#ifdef PRJ_YUNDU_H
    struct yd_ntb_reg *cfg = NULL;
#else
    struct yd_ntb_cfg *cfg = NULL;
#endif
    struct pci_dev *pdev = ntb_cv_get_ntb_dev();
    if(!pdev)
    {
        return -1;
    }

    res_start = pci_resource_start(pdev, 0);
    res_len = pci_resource_len(pdev, 0);
    if(!devm_request_mem_region(&pdev->dev, res_start, res_len, KBUILD_MODNAME))
    {
        printk("[%s]: %d: devm_request_mem_region  failed\n", __func__, __LINE__);
        return -1;
    }
    bar = (void *)ioremap(res_start, res_len);
    if(!bar)
    {
	    return -1;
    }


    ntb_cv_rc_reqid_set();
#ifdef PRJ_YUNDU_H
    cfg = (struct yd_ntb_reg *)bar;
#else
    cfg = (struct yd_ntb_cfg *)bar;
#endif

#ifdef PRJ_YUNDU_H
    iowrite32(1, &cfg->group7.odb_regs[local_station]);
#else
    iowrite32(1, &cfg->db_cfg.odb_regs[local_station]);
#endif
    return ret;
}


static int enable_ecrc_checking(struct pci_dev *dev)
{
	int aer = dev->aer_cap;
	u32 reg32;

	if (!aer)
		return -ENODEV;

	pci_read_config_dword(dev, aer + PCI_ERR_CAP, &reg32);
	if (reg32 & PCI_ERR_CAP_ECRC_GENC)
		reg32 |= PCI_ERR_CAP_ECRC_GENE;
	if (reg32 & PCI_ERR_CAP_ECRC_CHKC)
		reg32 |= PCI_ERR_CAP_ECRC_CHKE;
	pci_write_config_dword(dev, aer + PCI_ERR_CAP, reg32);

	return 0;
}



static int ntb_cv_51(uint32_t local_station, uint32_t target_station)   /*h 51*/
{
    int ret = 0;
  
 

    struct pci_dev *pdev = ntb_cv_get_ntb_dev();
    if(!pdev)
    {
        return -1;
    }

    enable_ecrc_checking(pdev);

    ntb_cv_07(local_station, target_station);
    return ret;
}





static int ntb_cv_23_bak(uint32_t local_station, uint32_t target_station)   /*CV_NT_050*/
{
     int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
    void *map_addr = NULL;
    char tmp_buf[32] = {0};
  
  
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_03);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }

    ret = sudo_alloc_lut_map_win(target_station, remote_addr, sizeof(g_case03_msg), &local_addr, &size);
    if(ret)
    {
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }


    map_addr = (void *)ioremap(local_addr, size);
    memcpy(tmp_buf, map_addr, sizeof(g_case03_msg));

    sudo_free_lut_map_win(target_station, local_addr);
    
    return ret;
}



#define TEST_YD_ENTRY_ENABLE (UL(1) << 5)
#define TEST_YD_ENTRY_GET_ALIGN_ADDR(x)  ((((unsigned long long)(x) & GENMASK(63, 12)) >> 12) << 6)
#define TEST_YD_ENTRY_PARTITION_ID(x)    (((x) & GENMASK(4, 0)) << 58)

static int ntb_cv_36(uint32_t local_station, uint32_t target_station)   /*CV_NT_051*/
{
    int ret = 0;
    void __iomem *bar = 0;
    void __iomem *lut = 0;
    unsigned long res_start, res_len;
#ifdef PRJ_YUNDU_H
    struct yd_ntb_reg *cfg = NULL;
#else
    struct yd_ntb_cfg *cfg = NULL;
#endif
    struct pci_dev *pdev = ntb_cv_get_ntb_dev();
    uint64_t val;
    if(!pdev)
    {
        return -1;
    }

    res_start = pci_resource_start(pdev, 2);
    res_len = pci_resource_len(pdev, 2);
    printk("[%s]: %d: res start = %lx\n", __func__, __LINE__, res_start);
  
    bar = (void *)ioremap(res_start, res_len);
    if(!bar)
    {
	    return -1;
    }


    //ntb_cv_rc_reqid_set();

#ifdef PRJ_YUNDU_H
    cfg = (struct yd_ntb_reg *)bar;
#else
    cfg = (struct yd_ntb_cfg *)bar;
#endif
    val = TEST_YD_ENTRY_ENABLE | (TEST_YD_ENTRY_GET_ALIGN_ADDR(0x12345678)) | (TEST_YD_ENTRY_PARTITION_ID(local_station));

#ifdef PRJ_YUNDU_H
    printk("[%s]: %d lut cfg enytys = %x\n", __func__, __LINE__,  &cfg->group3.entrys[0]);
    iowrite64(val, &cfg->group3.entrys[0]);
#else
    printk("[%s]: %d lut cfg enytys = %llx\n", __func__, __LINE__,  (uint64_t)&cfg->lut_cfg.entrys[0]);
    iowrite64(val, &cfg->lut_cfg.entrys[0]);
#endif
    lut = ioremap(res_start, 8);
    ioread32(lut);
    memcpy(&val, lut, 4);

    iounmap(bar);
    iounmap(lut);
    return ret;
}


static int ntb_cv_37(void)   /*CV_NT_051*/
{
    int ret = 0;
    void __iomem *bar = 0;
    unsigned long res_start, res_len;
    struct pci_dev *pdev = ntb_cv_get_ntb_dev();
    uint64_t val;
    if(!pdev)
    {
        return -1;
    }

    res_start = pci_resource_start(pdev, 0);
    res_len = pci_resource_len(pdev, 0);
    printk("[%s]: %d: res start = %lx\n", __func__, __LINE__, res_start);
  
    bar = (void *)ioremap(res_start, res_len);
    if(!bar)
    {
	    return -1;
    }


    val = *(uint64_t *)bar;
    if(val != 0xffffffffffffffff)
    {
        ret = -1;
    }

    iounmap(bar);
    return ret;
}


static int ntb_cv_38(uint32_t local_station, uint32_t target_station)   /*CV_NT_051*/
{
    int ret = 0;
    void __iomem *bar = 0;
     
    unsigned long res_start, res_len;
#ifdef PRJ_YUNDU_H
    struct yd_ntb_reg *cfg = NULL;
#else
    struct yd_ntb_cfg *cfg = NULL;
#endif
    struct pci_dev *pdev = ntb_cv_get_ntb_dev();
    uint32_t val;
    if(!pdev)
    {
        return -1;
    }

    res_start = pci_resource_start(pdev, 2);
    res_len = pci_resource_len(pdev, 2);
    printk("[%s]: %d: res start = %lx\n", __func__, __LINE__, res_start);
  
    bar = (void *)ioremap(res_start, res_len);
    if(!bar)
    {
	    return -1;
    }

#ifdef PRJ_YUNDU_H
    cfg = (struct yd_ntb_reg *)bar;
#else
    cfg = (struct yd_ntb_cfg *)bar;
#endif
    

#ifdef PRJ_YUNDU_H
    val = ioread32(&cfg->group6.ibmsg_field[local_station][0].value);
#else
    val = ioread32(&cfg->ibmsg_cfg.ibmsg_field[local_station][0]);
#endif
    if(val != 0xffffffff)
    {
        ret = -1;
    }

    iounmap(bar);
    return ret;
}


static int ntb_cv_40(void)   /*40 42 混用*/
{
    int ret = 0;
    void __iomem *bar = 0;
    unsigned long res_start, res_len;
    struct pci_dev *pdev = ntb_cv_get_ntb_dev();
    uint32_t val;
    if(!pdev)
    {
        return -1;
    }

    res_start = pci_resource_start(pdev, 0);
    res_len = pci_resource_len(pdev, 0);
    printk("[%s]: %d: res start = %lx\n", __func__, __LINE__, res_start);
  
    bar = (void *)ioremap(res_start, res_len);
    if(!bar)
    {
	    return -1;
    }


    val = ioread32(bar);
    if(val != 0xffffffff)
    {
        ret = -1;
    }

    iounmap(bar);
    return ret;
}


static int ntb_cv_41(void)   /*41 43 混用*/
{
    int ret = 0;
    void __iomem *bar = 0;
    unsigned long res_start, res_len;
    struct pci_dev *pdev = ntb_cv_get_ntb_dev();
    if(!pdev)
    {
        return -1;
    }

    res_start = pci_resource_start(pdev, 0);
    res_len = pci_resource_len(pdev, 0);
    printk("[%s]: %d: res start = %lx\n", __func__, __LINE__, res_start);
  
    bar = (void *)ioremap(res_start, res_len);
    if(!bar)
    {
	    return -1;
    }


    iowrite32(0x1234, bar);
    iounmap(bar);
    return ret;
}

static int ntb_cv_52(void)   /*41 43 混用*/
{
    int ret = 0;
    void __iomem *bar = 0;
    unsigned long res_start, res_len;
    struct pci_dev *pdev = ntb_cv_get_ntb_dev();
    uint32_t val;
    if(!pdev)
    {
        return -1;
    }

    res_start = pci_resource_start(pdev, 0);
    res_len = pci_resource_len(pdev, 0);
    printk("[%s]: %d: res start = %lx\n", __func__, __LINE__, res_start);
  
    bar = (void *)ioremap(res_start, res_len);
    if(!bar)
    {
	    return -1;
    }

    val = ioread32(bar + 0x8000);
    if(val != 0xffffffff)
    {
        ret = -1;
    }
    iounmap(bar);
    return ret;
}



static int ntb_cv_25(uint32_t local_station, uint32_t target_station)   /*CV_NT_052*/
{
    int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
    void *map_addr = NULL;
    char tmp_buf[32] = {0};
    uint32_t crc_val;
    struct test_packet *packet = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_04);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }
    printk("[%s]: %d: ente\n", __func__, __LINE__);
    ssleep(1);
    ret = sudo_alloc_dir_map_win(target_station, remote_addr, 0xffff, &local_addr, &size);
    if(ret)
    {   
        goto final;
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }
    printk("[%s]: %d: ente\n", __func__, __LINE__);
    ssleep(1);
    ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }
    sudo_ntb_clear_req_id(0x1700);
    printk("[%s]: %d: ente\n", __func__, __LINE__);
    ssleep(1);
    map_addr = (void *)ioremap(local_addr, size);
    printk("[%s]: %d: ente, map  addr = %llx, local = %llx\n", __func__, __LINE__, (uint64_t)map_addr, local_addr);
    ssleep(1);
    memcpy(tmp_buf, map_addr, sizeof(g_case04_msg));
    printk("[%s]: %d: ente\n", __func__, __LINE__);
    ssleep(1);
    crc_val = crc32_be(CRC_VAL, (uint8_t *)map_addr, sizeof(g_case04_msg));
    printk("[%s]: %d: ente\n", __func__, __LINE__);
    ssleep(1);
    printk("[%s]: %d: crc_val = %d, map addr buf = %s\n", __func__, __LINE__, crc_val, (char *)map_addr);
    build_packet(&packet, CLIENT_READ_OK, CV_NTB_CASE_04, crc_val, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    /*??server???ret ok*/
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        goto final;
    }
    if(g_deal_ret == 0)
    {
        ret = 0;
        printk("[%s]: %d: g_deal_ret = 0\n", __func__, __LINE__);
    }
    else{
        ret = -1;
        printk("[%s]: %d: g_deal_ret = %d\n", __func__, __LINE__, g_deal_ret);
    
    }
final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_04, 0, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    sudo_free_dir_map_win(target_station, local_addr);
    sudo_ntb_clear_req_id(0x0);
    
    return ret;
}

static int ntb_cv_26(uint32_t local_station, uint32_t target_station)   /*CV_NT_053*/
{
    int ret;
    unsigned long long remote_addr;
    phys_addr_t local_addr;
    size_t size;
    void *map_addr = NULL;
    char tmp_buf[32] = {0};
    uint32_t crc_val;
    struct test_packet *packet = NULL;
    ret = ntb_cv_get_remote_paddr(target_station, &remote_addr, CV_NTB_CASE_04);
    if(ret)
    {
        printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
    }
    printk("[%s]: %d: ente\n", __func__, __LINE__);
    ssleep(1);
    ret = sudo_alloc_dir_map_win(target_station, remote_addr, 0xffff, &local_addr, &size);
    if(ret)
    {   
        goto final;
        printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
    }
    printk("[%s]: %d: ente\n", __func__, __LINE__);
    ssleep(1);
    /*
    ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }
    */
    printk("[%s]: %d: ente\n", __func__, __LINE__);
   
    map_addr = (void *)ioremap(local_addr, size);
    printk("[%s]: %d: ente, map  addr = %llx, local = %llx\n", __func__, __LINE__, (uint64_t)map_addr, local_addr);
  
    memcpy(tmp_buf, map_addr, sizeof(g_case04_msg));
    printk("[%s]: %d: ente\n", __func__, __LINE__);
   
    crc_val = crc32_be(CRC_VAL, (uint8_t *)map_addr, sizeof(g_case04_msg));
    printk("[%s]: %d: ente\n", __func__, __LINE__);
   
    printk("[%s]: %d: crc_val = %d, map addr buf = %s\n", __func__, __LINE__, crc_val, (char *)map_addr);
    build_packet(&packet, CLIENT_READ_OK, CV_NTB_CASE_04, crc_val, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    /*??server???ret ok*/
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        goto final;
    }
    if(g_deal_ret == 0)
    {
        ret = 0;
        printk("[%s]: %d: g_deal_ret = 0\n", __func__, __LINE__);
    }
    else{
        ret = -1;
        printk("[%s]: %d: g_deal_ret = %d\n", __func__, __LINE__, g_deal_ret);
    
    }
final:
    build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_04, 0, 0, remote_addr);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
    }
    free_packet(packet);
    sudo_free_dir_map_win(target_station, local_addr);
    //sudo_ntb_clear_req_id(0x0);
    //sudo_ntb_clear_req_id(0x1700);
    return ret;
}


static int ntb_cv_35(uint32_t local_station, uint32_t target_station)   /*h 35 CV_NT_054*/
{
    int ret = 0;
    void __iomem *bar = 0;
    void __iomem *dir = 0;
    unsigned long res_start, res_len;
#ifdef PRJ_YUNDU_H
    struct yd_ntb_reg *cfg = NULL;
#else
    struct yd_ntb_cfg *cfg = NULL;
#endif
    struct pci_dev *pdev = ntb_cv_get_ntb_dev();
    
    if(!pdev)
    {
        return -1;
    }

    res_start = pci_resource_start(pdev, 0);
    res_len = pci_resource_len(pdev, 0);

    printk("[%s]: res start is %ld, res len = %ld\n", __func__, res_start, res_len);
    bar = (void *)ioremap(res_start, res_len);
    if(!bar)
    {
	    return -1;
    }

    ntb_cv_rc_reqid_set();
#ifdef PRJ_YUNDU_H
    cfg = (struct yd_ntb_reg *)bar;
#else
    cfg = (struct yd_ntb_cfg *)bar;
#endif


#ifdef PRJ_YUNDU_H
    iowrite64(0x12345678, &cfg->group4.dir_td_base[local_station]);
    iowrite64(ioread64(&cfg->group4.dir_utd_base[local_station]) + 0xffff, &cfg->group4.dir_utd_limit[local_station]);

    printk("[%s]: %d: dir p = %llx\n", __func__, __LINE__, ioread64(&cfg->group4.dir_utd_base[local_station]));
    dir = ioremap(ioread64(&cfg->group4.dir_utd_base[local_station]), 8);
#else
    iowrite64(0x12345678, &cfg->dir_cfg.dir_td_base[local_station]);
    iowrite64(ioread64(&cfg->dir_cfg.dir_utd_base[local_station]) + 0xffff, &cfg->dir_cfg.dir_utd_limit[local_station]);

    printk("[%s]: %d: dir p = %x\n", __func__, __LINE__, ioread32(&cfg->dir_cfg.dir_utd_base[local_station]));
    dir = ioremap(ioread32(&cfg->dir_cfg.dir_utd_base[local_station]), 8);
#endif
    ioread32(dir);

    iounmap(bar);
    iounmap(dir);
    return ret;
}



/*两边host一起对32个开窗读写，1000次压力测试：客户端发起请求，获取对端地址等信息，进行开窗，然后告诉server要进行相同操作*/
static int ntb_cv_30_bak(uint32_t local_station, uint32_t target_station)   /*32  lut??. same station  CV_NT_018*/
{
    
    int ret, i, j;
    unsigned long long remote_addr[32];
    unsigned long long local_addr[32];
    void *map_addr[32];
    size_t size = 0;
    char write_buf[64] = {0};
    char read_buf[64] = {0};
    struct test_packet *packet = NULL;
    ret = ntb_cv_rc_reqid_set();
    if(ret < 0)
    {
        printk("[%s]: %d: ntb_cv_rc_reqid_set failed\n", __func__, __LINE__);
    }
    for(i = 0; i < 32; i++)
    {
        ret = ntb_cv_get_remote_paddr(target_station, &remote_addr[i], CV_NTB_CASE_30);
        if(ret)
        {
            printk("[%s]: %d: ntb_cv_get_remote_paddr failed\n", __func__, __LINE__);
            return ret;
        }
        ret = sudo_alloc_lut_map_win(target_station, remote_addr[i], sizeof(write_buf), &local_addr[i], &size);
        if(ret)
        {
            printk("[%s]: %d: sudo_alloc_lut_map_win failed\n", __func__, __LINE__);
            return ret;
        }
        map_addr[i] = ioremap(local_addr[i], size);

    }


    /*通知server进行相同操作*/
    for(j = 0; j < 1000; j++)
    {
        for(i = 0; i < 32; i++)
        {
            memset(write_buf, 0, 64);
            sprintf(write_buf, "case07:%d", i);
            memcpy(map_addr[i], write_buf, strlen(write_buf));
            memcpy(read_buf, map_addr[i], strlen(write_buf));
            printk("[%s]: %d: map addr = %s\n", __func__, __LINE__, (char *)map_addr[i]);
            if(strncmp(write_buf, read_buf, strlen(write_buf)) !=0)
            {
                printk("[%s]: %d: i = %d, write buf = %s, strncmp failed\n", __func__, __LINE__, i, write_buf);
            }
        }
    }
  

    for(i = 0; i < 32; i++)
    {
        build_packet(&packet, CLIENT_ALL_END, CV_NTB_CASE_30, 0, 0, remote_addr[i]);
        ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
        if(ret)
        {
            printk("[%s]: %d: send_pipe_msg failed\n", __func__, __LINE__);
        }
        free_packet(packet);
        sudo_free_lut_map_win(target_station, local_addr[i]);
        
    }
    ntb_cv_rc_reqid_set();
   return 0;

}

static int ntb_cv_20(void)
{
    struct pci_dev *pdev = ntb_cv_get_ntb_dsp_dev();
    if(!pdev)
    {
        return -1;
    }
    yd_pci_reset_secondary_bus(pdev);
    return 0;
}




/*NTF_MULITE_FABRIC_INFO and NTF_INTERNAL_FABRIC_INFO*/
struct ntf_fabric_info{
    uint32_t dsp_nt_bus;
    uint32_t utd_32_base;
    uint32_t utd_32_base_up;
    uint32_t utd_64_base;
    uint32_t utd_64_base_up;
};

static void ntf_mul_server_recv_nt_bus(uint32_t ntf_id, uint32_t dsp_nt_bus)
{
    struct test_packet *packet = NULL;
    int ret;
    sudo_ntf_dst_nt_bus_set(cs_station, dsp_nt_bus);
    build_packet(&packet, NTF_CLIENT_RECV_RESP_NT_BUS, 1, 0, 0, g_server_nt_bus);
    ret = sudo_ntf_send_msg(cs_station, ntf_id, (void *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg NTF_CLIENT_RECV_RESP_NT_BUS failed\n", __func__, __LINE__);
    
    }
    free_packet(packet);
}


static void ntf_mul_client_recv_nt_bus(uint32_t ntf_id, uint32_t dsp_nt_bus)
{
    sudo_ntf_internal_nt_bus_set(src_fabric_station, dst_fabric_station, 0);
    complete(&comp);
}


void ntf_msg_cb(uint8_t cb_result, uint8_t *data, size_t size, void *cb_arg)
{

    struct test_packet *packet = NULL;
    int ret;
    if(cb_result == 0)
    {
        printk("[%s]: err cb_result", __func__);
        return;
    }
    if(cb_result == NTF_LOCAL_MSG)
    {
        packet = (struct test_packet *)data;
        if(packet->command == NTF_SERVER_RECV_REQ_NT_BUS)
        {
            sudo_ntf_dst_nt_bus_set(cs_station, packet->p_addr);
            build_packet(&packet, NTF_CLIENT_RECV_RESP_NT_BUS, 1, 0, 0, g_server_nt_bus);
            ret = sudo_ntf_send_msg(cs_station, packet->crc_val, (void *)packet, sizeof(struct test_packet));
            if(ret)
            {
                printk("[%s]: %d: send_pipe_msg NTF_CLIENT_RECV_RESP_NT_BUS failed\n", __func__, __LINE__);
            
            }
            free_packet(packet);
            return;
        }
        else if(packet->command == NTF_CLIENT_RECV_RESP_NT_BUS)
        {
            sudo_ntf_dst_nt_bus_set(cs_station, packet->p_addr);
        }
    }
    memcpy(&g_data, data, size);
    g_ntf_cmd = cb_result;
    complete(&comp);
}

/*CV_NT_65*/
static int ntf_cv_01(uint32_t target_station)  
{
    int ret;
    struct ntf_fabric_info info;
    struct test_packet *packet = NULL;
    sudo_ntf_internal_sw_set(src_fabric_station, dst_fabric_station, addr32_align, addr64_align);
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        /*return or goto final*/
        
    }
    if(g_ntf_cmd != NTF_INTERNAL_FABRIC_INFO)
    {
        printk("[%s]: wait comp info error", __func__);
        return -1;
    }
    memset(&info, 0, sizeof(struct ntf_fabric_info));
    memcpy(&info, &g_data, sizeof(struct ntf_fabric_info));
    if(!ntf_client)
    {
        g_server_nt_bus = info.dsp_nt_bus;
        return 0;
    }

    build_packet(&packet, NTF_SERVER_RECV_REQ_NT_BUS, 1, 0, 0, info.dsp_nt_bus);
    ret = send_pipe_msg(target_station, TEST_PIPE_ID, (uint8_t *)packet, sizeof(struct test_packet));
    if(ret)
    {
        printk("[%s]: %d: send_pipe_msg NTF_CLIENT_RECV_RESP_NT_BUS failed\n", __func__, __LINE__);
    
    }
    free_packet(packet);
    /*wait server resp dsp nt bus and set*/
    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        /*return or goto final*/
        
    }


    /*start usp 32 and 64 local addr to fabric*/
    return ret;
}


static int ntf_cv_02(uint32_t local_station, uint32_t target_station) {
    int ret;
    uint32_t i;
    struct ntf_fabric_info info;
    struct test_packet *packet = NULL;
    sudo_ntf_cs_station_set(cs_station, as_usp);
    sudo_ntf_build_cs_path(cs_station);

    sudo_ntf_p2p_port_set(src_fabric_station, dst_fabric_station, addr32_align, addr64_align, cs_station, 0);



    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        /*return or goto final*/
        
    }
    if(g_ntf_cmd != NTF_MULITE_FABRIC_INFO)
    {
        printk("[%s]: wait comp info error", __func__);
        return -1;
    }



    memset(&info, 0, sizeof(struct ntf_fabric_info));
    memcpy(&info, &g_data, sizeof(struct ntf_fabric_info));

    if(!ntf_client)
    {
        g_server_nt_bus = info.dsp_nt_bus;
        return 0;
    }

    



    /*ntf client run*/
    sudo_ntf_detect_other_sw_ntb(cs_station);

    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        /*return or goto final*/
        
    }
    if(g_ntf_cmd != NTF_DETECT_RESP)
    {
        printk("[%s]: wait comp info error", __func__);
        return -1;
    }
    for(i = 1; i < 8 ; i++)
    {
        if(g_data[i] = i)
        {
            printk("cs station%d id%d online", cs_station, i);
            ntf_id = i;
        }
    }
    if(!ntf_id)
    {
        printk("this cs station%d has no usp nt", cs_station);
        return -1;
    }
    build_packet(&packet, NTF_SERVER_RECV_REQ_NT_BUS, 1, local_station, 0, info.dsp_nt_bus);
    sudo_ntf_send_msg(cs_station, ntf_id, (void *)packet, sizeof(struct test_packet));

    if(!wait_for_completion_timeout(&comp, msecs_to_jiffies(TEST_SEND_TIMEOUT)))
    {
        printk("[%s]: %d: wait get server resp deal ret\n", __func__, __LINE__);
        ret = -1;
        /*return or goto final*/
        
    }


    return ret;
}

/*ntf case start*/

static int ntb_test_start(void)
{
    uint32_t station_array[7];
    uint32_t station_cnt;
    int ret;
    uint8_t i, local_station_id, target_station_id;
    get_win_info();
    ret = sudo_ntb_get_topo(station_array, &station_cnt);
    if(ret)
    {
        printk("[%s]: sudo_ntb_get_topo failed\n", __func__);
        return ret;
    }
    for(i = 0; i < station_cnt; i++)
    {
        printk("[%s]: i = %d, station id = %d\n", __func__, i, station_array[i]);
    }
    if(station_cnt < 2)
    {
        printk("[%s]: has only one ntb\n", __func__);
       // return ret;
    }

    local_station_id = sudo_ntb_get_local_station_id();
    if(local_station_id == station_array[0])
    {
        target_station_id = station_array[1];
    }
    else{
        target_station_id = station_array[0];
    }
    
    printk("[%s]: local station id = %d, target station id = %d\n", __func__, local_station_id, target_station_id);
    
  
    sudo_ntb_register_msg_cb(target_station_id, TEST_PIPE_ID, msg_callback, NULL);
    sudo_ntb_register_db_cb(target_station_id, 0, db_callback, NULL);
    sudo_ntb_register_db_cb(target_station_id, 1, db_callback, NULL);
    sudo_ntb_register_db_cb(target_station_id, 2, db_callback, NULL);
    /*test type有值证明是为了测试ntf的，ntb的case不用跑*/

    if(test_type)
    {
        ret = sudo_ntf_msg_cb_register(ntf_msg_cb, NULL);
        if(ret)
        {
            printk("ntf msg cb register failed");
            return -1;
        }

        switch (test_case)
        {
        case CV_NTB_CASE_01:
            ntf_cv_01(target_station_id);
            break;
        case CV_NTB_CASE_02:
            ntf_cv_02(local_station_id, target_station_id);
            break;
        default:
            break;
        }
    }

    if(!ntb_client)
        return 0;

    
    
    switch (test_case)
    {

    case CV_NTB_CASE_04:
        ntb_cv_04(target_station_id);
        break;
    case CV_NTB_CASE_05:
        ntb_cv_05(target_station_id);
        break;
    case CV_NTB_CASE_07:
        ntb_cv_07(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_08:
        ntb_cv_08(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_09:
        ntb_cv_09(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_10:
        ntb_cv_10(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_11:
        ntb_cv_11(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_12:
        ntb_cv_12(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_13:
        ntb_cv_13(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_14:
        ntb_cv_14(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_15:
        ntb_cv_15(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_16:
        ntb_cv_16(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_17:
        ntb_cv_17(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_18:
        ntb_cv_18(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_19:
        ntb_cv_19(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_20:
        ntb_cv_20();
        break;

    case CV_NTB_CASE_35:
        ntb_cv_35(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_36:
        ntb_cv_36(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_37:
        ntb_cv_37();
        break;
    case CV_NTB_CASE_38:
        ntb_cv_38(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_40:
        ntb_cv_40();
        break;
    case CV_NTB_CASE_41:
        ntb_cv_41();
        break;
    case CV_NTB_CASE_42:
        ntb_cv_40();
        break;
    case CV_NTB_CASE_43:
        ntb_cv_41();
        break;
    case CV_NTB_CASE_51:
        ntb_cv_51(local_station_id, target_station_id);
        break;
    case CV_NTB_CASE_52:
        ntb_cv_52();
        break;

    case CV_NTB_CASE_58:
        ntb_cv_58(local_station_id, target_station_id);
        break;
    
    default:
        break;
    }
    return ret;
}


static void tmp_test(void)
{
	/*
#if 0
    sudo_ntf_cs_station_set(2, 0);
    ssleep(5);
    sudo_ntf_build_cs_path(2);
    ssleep(5);
    sudo_ntf_p2p_port_set(3, 5, 8, 8, 2, 0x300);
    ssleep(5);
    sudo_ntf_dst_nt_bus_set(2, 195);

#else
    sudo_ntf_cs_station_set(3, 0);
    ssleep(5);
    sudo_ntf_build_cs_path(3);
    ssleep(5);
    sudo_ntf_p2p_port_set(2, 5, 8, 8, 3, 0x300);
    ssleep(5);
    sudo_ntf_dst_nt_bus_set(3, 195);
#endif
*/
     sudo_ntf_internal_sw_set(3, 2, 8, 8);
    ssleep(5);
     sudo_ntf_internal_nt_bus_set(3, 2, 0x500);
    ssleep(5);
     sudo_ntf_internal_sw_set(2, 3, 8, 8);
    ssleep(5);
     sudo_ntf_internal_nt_bus_set(2, 3, 0x300);
}


static int __init test_init(void)
{

    tmp_test();
    return 0;

    init_completion(&comp);
    init_completion(&g_comp);
    printk("ntb cleint = %d, test_case = %d\n", ntb_client, test_case);
    
    ntb_test_start();

    return 0;
}

static void __exit test_exit(void)
{
    uint32_t station_array[7];
    uint32_t station_cnt;
    int ret;
    uint8_t i, local_station_id, target_station_id;

    return;
    ret = sudo_ntb_get_topo(station_array, &station_cnt);
    if(ret)
    {
        printk("[%s]: sudo_ntb_get_topo failed\n", __func__);
        return;
    }
    for(i = 0; i < station_cnt; i++)
    {
        printk("[%s]: i = %d, station id = %d\n", __func__, i, station_array[i]);
    }
    if(station_cnt < 2)
    {
        printk("[%s]: has only one ntb\n", __func__);
       // return ret;
    }
   

    local_station_id = sudo_ntb_get_local_station_id();
    if(local_station_id == station_array[0])
    {
        target_station_id = station_array[1];
    }
    else{
        target_station_id = station_array[0];
    }
    ret = sudo_ntb_unregister_msg_cb(target_station_id, TEST_PIPE_ID);
    sudo_ntb_unregister_db_cb(target_station_id, 0);
    sudo_ntb_unregister_db_cb(target_station_id, 1);
    sudo_ntb_unregister_db_cb(target_station_id, 2);
    return;
}

MODULE_LICENSE("GPL");
module_init(test_init);
module_exit(test_exit);
