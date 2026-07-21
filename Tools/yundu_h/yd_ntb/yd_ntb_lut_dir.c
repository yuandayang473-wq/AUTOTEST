#include "yd_ntb_lut_dir.h"
/*保证dir和lut的映射不能有重叠*/
#define YD_NTB_MAX_LUT_CNT  32

#define YD_ENTRY_ENABLE (UL(1) << 5)
#define YD_ENTRY_GET_ALIGN_ADDR(x)  ((((unsigned long long)(x) & GENMASK(63, 12)) >> 12) << 6)
#define YD_ENTRY_PARTITION_ID(x)    (((x) & GENMASK(4, 0)) << 58)

#define YD_LUT_BASE_ADDR    0x30800000
#define YD_LUT_WIN_OFFSET   13
#define YD_LUT_WIN_SIZE     BIT(YD_LUT_WIN_OFFSET)

#define YD_DIR_WIN_OFFSET   20

#define YD_NTB_ALIGN_SZIE   4096


/*设置或者初始化时候用*/
static int yd_ntb_set_lut(struct yd_ntb_dev *yd_ndev, yd_lut_entry_regs_t *reg, uint32_t station_id, dma_addr_t addr, bool enable)
{
    uint64_t val = 0, result;
    
    mutex_lock(&yd_ndev->lut_lock);
    if(enable)
    {
        val = YD_ENTRY_ENABLE | YD_ENTRY_GET_ALIGN_ADDR(addr) | YD_ENTRY_PARTITION_ID(station_id);
    }
    else{
        val = 0;
    }
    iowrite64(val, reg);
    /*add read*/
    result = ioread64(reg);
    if(val != result)
    {
        mutex_unlock(&yd_ndev->lut_lock);
	printk("[%s]: %d: val != result\n", __func__, __LINE__);
    	return -1;
    }
    mutex_unlock(&yd_ndev->lut_lock);
    
    return 0;
}

static int yd_ntb_set_dir(struct yd_ntb_dev *yd_ndev, group4_t *group4, uint32_t station_id, dma_addr_t addr, size_t size)
{

    uint64_t val = 0;
    mutex_lock(&yd_ndev->dir_lock);
   
    iowrite64(addr, &group4->dir_td_base[station_id]);
   
    iowrite64(ioread64(&group4->dir_utd_base[station_id]) + size, &group4->dir_utd_limit[station_id]);

    val = ioread64(&group4->dir_td_base[station_id]);
    if(val != addr)
    {
    	    mutex_unlock(&yd_ndev->dir_lock);
	    return -1;
    }

    val = ioread64(&group4->dir_utd_limit[station_id]);
    if(val != (ioread64(&group4->dir_utd_base[station_id]) + size))
    {
    	    mutex_unlock(&yd_ndev->dir_lock);
	    return -1;
	    
    }


    mutex_unlock(&yd_ndev->dir_lock);

    
    return 0;
    
}

#define YD_LUT_GET_EN_BIT(x) (x & BIT(5))
#define YD_LUT_GET_SID(x)   (x & GENMASK(61, 58))

static bool yd_check_dst_addr_valid(struct yd_ntb_dev *yd_ndev, uint32_t dst_station, dma_addr_t dst_addr)
{
    group3_t *group3          = &yd_ndev->cfg->group3;
    yd_lut_entry_regs_t *entry_reg = NULL;
    uint8_t i;
    uint64_t tmp_addr, val;
    if(dst_addr & GENMASK(11, 0))
    {
        pci_dbg(yd_ndev->pdev, "[%s]: dst addr is not align\n", __func__);
        return false;
    }
    mutex_lock(&yd_ndev->lut_lock);
    for(i = 0;i < YD_LUT_ENTRY_CNT; i++)
    {
        entry_reg = &group3->entrys[i];
        if(entry_reg->LUT_EN && entry_reg->LUT_D_SID == dst_station)
        {
            val = entry_reg->LUT_TD_base_H;
            tmp_addr = (entry_reg->LUT_TD_base_L << 12) + (val << 38); 
            if(dst_addr > tmp_addr && dst_addr < (tmp_addr + YD_LUT_WIN_SIZE))
            {
                mutex_unlock(&yd_ndev->lut_lock);
                pci_dbg(yd_ndev->pdev, "[%s]: dst addr is invalid\n", __func__);
                return false;
            }
            
        }
    }
    mutex_unlock(&yd_ndev->lut_lock);
    return true;
}

/*不能map自己station id的*/
static bool yd_check_station_id_valid(struct yd_ntb_dev *yd_ndev, uint32_t dst_station)
{
    return yd_ndev->station_id == dst_station;
}

static int yd_ld_get_free_lut_entry(struct yd_ntb_dev *yd_ndev)
{
    uint8_t i;
    group3_t *group3             = NULL;
    yd_lut_entry_regs_t *entry_regs    = NULL;
    uint32_t val;

    group3    = &yd_ndev->cfg->group3;
    entry_regs  = group3->entrys;
    
    mutex_lock(&yd_ndev->lut_lock);
    for(i = 0;i< YD_LUT_ENTRY_CNT;i++)
    {
        val = ioread32(&entry_regs[i]);
        if(!YD_LUT_GET_EN_BIT(val))
        {
            mutex_unlock(&yd_ndev->lut_lock);
            return i;
        }
    }
    mutex_unlock(&yd_ndev->lut_lock);
    pci_dbg(yd_ndev->pdev, "[%s]: get free lut entry failed\n", __func__);
    return -1;
}

/*没给valid寄存器，就只能根据是否配置了地址进行判断*/
static bool yd_ld_dir_is_free(group4_t *group4, uint32_t station_id)
{
    uint64_t val;
    val = ioread64(&group4->dir_td_base[station_id]);
    if(val)
    {
        return false;
    }
    return true;
}

#define YD_LUT_GET_TD_BASE_L(x) (x & GENMASK(31, 6))
#define YD_LUT_GET_TD_BASE_H(x) (x & GENMASK(58, 32))

/*找到起始地址和station id，对上了就是了*/
static yd_lut_entry_regs_t *yd_ld_get_entry_by_addr(group3_t *group3, uint32_t station_id, dma_addr_t local_addr)
{
    uint32_t entry_num;
    yd_lut_entry_regs_t *entry_regs    = group3->entrys;
    struct yd_ntb_dev *yd_ndev              = NULL;
    
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return NULL;
    }
   
    if(local_addr < yd_ndev->lut_base)
    {
        pci_dbg(yd_ndev->pdev, "[%s]: local addr is invalid!!!\n", __func__);
        return NULL;
    }
    entry_num = (local_addr - yd_ndev->lut_base) / YD_LUT_WIN_SIZE;
    if(entry_num > (YD_NTB_MAX_LUT_CNT - 1))
    {
        pci_dbg(yd_ndev->pdev, "[%s]: entry num is invalid!!!\n", __func__);
        return NULL;
    }

    return &entry_regs[entry_num];
}



/*map之后返回得物理地址是bar2得物理地址不*/
int yd_alloc_lut_map_win(uint32_t station_id, unsigned long long dst_addr, size_t size, dma_addr_t *src_addr, size_t *result_size)
{
    group3_t *group3          = NULL;
    yd_lut_entry_regs_t *entry_reg = NULL;
    int entry_num;
    uint64_t addr_base;
    struct yd_ntb_dev *yd_ndev          = NULL;
    uint32_t val;

    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }

    if(!yd_check_dst_addr_valid(yd_ndev, station_id, dst_addr))   
    {
        return -1;
    }

    group3 = &yd_ndev->cfg->group3;

    if(size > yd_ndev->lut_max_size)
    {
        return -1;
    }

    if(yd_check_station_id_valid(yd_ndev, station_id))
    {
        pci_err(yd_ndev->pdev, "[%s]: station_id is invalid!!!\n", __func__);
        return -1;
    }
    
    entry_num = yd_ld_get_free_lut_entry(yd_ndev);
    if(entry_num < 0)
    {
        pci_err(yd_ndev->pdev, "[%s]: entry num is invalid!!!\n", __func__);
        return -1;
    }
    
    entry_reg = &group3->entrys[entry_num];
    
    yd_ntb_set_lut(yd_ndev, entry_reg, station_id, dst_addr, true);

    addr_base = ALIGN(yd_ndev->bar2, YD_NTB_ALIGN_SZIE);
    val = ioread32(&group3->LUT_fix_offset);

    *src_addr = yd_ndev->lut_base + entry_num * BIT(val);
    *result_size = size;

    return 0;
}

int yd_free_lut_map_win(uint32_t station_id, dma_addr_t dst_addr)   //basic_free_lut_map_win
{
    group3_t *group3          = NULL;
    yd_lut_entry_regs_t *entry_reg = NULL;
    struct yd_ntb_dev *yd_ndev          = NULL;

    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    group3 = &yd_ndev->cfg->group3;
    entry_reg = yd_ld_get_entry_by_addr(group3, station_id, dst_addr);
    if(!entry_reg)
    {
        pci_err(yd_ndev->pdev, "[%s]: entry_reg is invalid!!!\n", __func__);
        return -1;
    }
   
    yd_ntb_set_lut(yd_ndev, entry_reg, station_id, dst_addr, false);
    return 0;
}

int yd_alloc_dir_map_win(uint32_t station_id, dma_addr_t dst_addr, size_t size, dma_addr_t *src_addr, size_t *result_size)  //basic_alloc_dir_map_win
{
    /*dir是每个station只能映射一个*/
    /*station id和物理地址对应关系*/
    struct yd_ntb_dev *yd_ndev = NULL; 
    group4_t *group4 = NULL;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    group4 = &yd_ndev->cfg->group4;
    /*加个字节对齐数判断*/
    /*add dst addr check*/
    if(size > yd_ndev->dir_max_size || size < 0xffff)
    {
        pci_err(yd_ndev->pdev, "[%s]: size is invalid!!!\n", __func__);
        return -1;
    }

    if(yd_check_station_id_valid(yd_ndev, station_id))
    {
        pci_err(yd_ndev->pdev, "[%s]: station_id is invalid!!!\n", __func__);
        return -1;
    }

    /*lock */
    if(!yd_ld_dir_is_free(group4, station_id))
    {
        pci_dbg(yd_ndev->pdev, "[%s]: the entry of station id %d is busy!!!\n", __func__, station_id);
        return -1;  
    }
    yd_ntb_set_dir(yd_ndev, group4, station_id, dst_addr, size);
    *src_addr = ioread64(&group4->dir_utd_base[station_id]);
    *result_size = size;
    return 0;
}

int yd_free_dir_map_win(uint32_t station_id, uint64_t addr)
{
    group4_t *group4 = NULL;
    struct yd_ntb_dev *yd_ndev = NULL;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }

    group4 = &yd_ndev->cfg->group4;
    if(yd_check_station_id_valid(yd_ndev, station_id))
    {
        pci_err(yd_ndev->pdev, "[%s]: station_id %d is invalid!!!\n", __func__, station_id);
        return -1;
    }

    if(yd_ld_dir_is_free(group4, station_id))
    {
        pci_err(yd_ndev->pdev, "[%s]: the entry of station id %d is !!!\n", __func__, station_id);
        return -1;
    }

    yd_ntb_set_dir(yd_ndev, group4, station_id, 0, 0);
    return 0;
}



int yd_ld_set_lut_offset(uint32_t offset)
{
    struct yd_ntb_dev *yd_ndev = NULL;
    group3_t *group3 = NULL;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    /*check align and addr valid*/
    mutex_lock(&yd_ndev->lut_lock);
    group3 = &yd_ndev->cfg->group3;
    iowrite32(YD_LUT_WIN_OFFSET, &group3->LUT_fix_offset);
    mutex_unlock(&yd_ndev->lut_lock);
    return 0;
}

/*动态分配得弄内存管理，暂时不考虑*/
int yd_ld_set_dir_offset(uint32_t offset)
{
    struct yd_ntb_dev *yd_ndev = NULL;
    group4_t *group4 = NULL;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    group4 = &yd_ndev->cfg->group4;
    return 0;
}

int yd_ld_get_dir_offset(void)
{
    struct yd_ntb_dev *yd_ndev = NULL;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    return yd_ndev->dir_max_size;
}

int yd_ld_get_lut_offset(void)
{
    struct yd_ntb_dev *yd_ndev = NULL;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    return yd_ndev->lut_max_size;
}

int yd_ld_init_lut(struct yd_ntb_dev *yd_ndev)
{
    group3_t *group3  = &yd_ndev->cfg->group3;
    dma_addr_t bar2_addr        = yd_ndev->bar2;
    size_t bar2_total_size      = yd_ndev->bar2_total_size;
    dma_addr_t align_base;
    
    align_base = ALIGN(bar2_addr, BIT(18));
    iowrite64(align_base, &group3->LUT_UTD_base);
    yd_ndev->lut_base = align_base;
   
    iowrite32(YD_LUT_WIN_OFFSET, &group3->LUT_fix_offset);

    yd_ndev->bar2_residue_size = bar2_total_size - (align_base - bar2_addr) - 32 * 2 * 4096;
    yd_ndev->lut_max_size = YD_LUT_WIN_SIZE;

    mutex_init(&yd_ndev->lut_lock);

    return 0;
}

void yd_ld_exit_lut(struct yd_ntb_dev *yd_ndev)
{
    group3_t *group3 = &yd_ndev->cfg->group3; 
    uint8_t i;
    
    for(i = 0;i < YD_LUT_ENTRY_CNT; i++)
    {
        yd_ntb_set_lut(yd_ndev, &group3->entrys[i], 0, 0, false);
    }
    iowrite64(0, &group3->LUT_UTD_base);
}


/*dir是初始化就给平均分配给每个dir，还是在分配时候来个内存管理，进行动态分配*/
int yd_ld_init_dir(struct yd_ntb_dev *yd_ndev)
{
    group4_t *group4 = &yd_ndev->cfg->group4;
    size_t residue_size, dir_offset;
    uint8_t i;
    dma_addr_t dir_base;
    uint32_t val;
    
    dir_base = yd_ndev->bar2 + (yd_ndev->bar2_total_size - yd_ndev->bar2_residue_size);
    residue_size = yd_ndev->bar2_residue_size;
    /*
    if(yd_ndev->mem_type == YD_ADDR_TYPE_32)  
    {
        residue_size = yd_ndev->bar2_residue_size;
    }
    else{
        residue_size = yd_ndev->bar2_residue_size + yd_ndev->bar3_residue_size;
    }
    */
    dir_offset = residue_size / YD_DIR_STATION_CNT;
    dir_offset = dir_offset / YD_NTB_ALIGN_SZIE * YD_NTB_ALIGN_SZIE;
    
    yd_ndev->dir_max_size = dir_offset;
    for(i = 0;i < YD_DIR_STATION_CNT;i++)
    {
        val = (dir_base  + i*dir_offset)& GENMASK(31, 0);
        iowrite32(val, &group4->dir_utd_base[i].DIR_UTD_base);
        val = ((dir_base + i*dir_offset) & GENMASK(63, 32)) >> 32;
        iowrite32(val, &group4->dir_utd_base[i].DIR_UTD_base_up);
    }

    mutex_init(&yd_ndev->dir_lock);
    return 0;
}

void yd_ld_exit_dir(struct yd_ntb_dev *yd_ndev)
{
    uint8_t i;
    group4_t *group4 = &yd_ndev->cfg->group4;
    for(i = 0;i<YD_DIR_STATION_CNT;i++)
    {
        iowrite32(0, &group4->dir_utd_base[i].DIR_UTD_base);
        iowrite32(0, &group4->dir_utd_base[i].DIR_UTD_base_up);
        yd_ntb_set_dir(yd_ndev, group4, i, 0, 0);
    }
}
