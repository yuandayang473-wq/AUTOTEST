#include "yd_reqid.h"

#define YD_REQID_MAX_ENTRY_CNT  32

#define YD_REQID_LID_VALID_BIT  BIT(24)

#define YD_REQID_REQID_DOMAIN(x) (x & GENMASK(15, 0))

/*找到一个空闲的附上reqid,然后valid*/
int yd_reqid_set(uint16_t req_id)
{
    struct yd_ntb_dev *yd_ndev = NULL;
    org_req_id_regs_t *org_reqid_reg = NULL, *tmp_reg = NULL;
    uint8_t i;
    uint32_t val, result;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    mutex_lock(&yd_ndev->req_id_lock);
    org_reqid_reg = yd_ndev->cfg->group1.ori_regs;
    for(i = 0;i < YD_REQID_MAX_ENTRY_CNT; i++)
    {
        tmp_reg = &org_reqid_reg[i];
        val = ioread32(tmp_reg);
        
        if(!(val & YD_REQID_LID_VALID_BIT))
        {
            val &= ~(YD_REQID_REQID_DOMAIN(0xffff));
        
            val |= (YD_REQID_LID_VALID_BIT | YD_REQID_REQID_DOMAIN(req_id));

            iowrite32(val, tmp_reg);
            
	    result = ioread32(tmp_reg);
	    if(result != val)
	    {
		    goto err;
	    }
            mutex_unlock(&yd_ndev->req_id_lock);
	    
            return i;
        }
        
    }
err:
    mutex_unlock(&yd_ndev->req_id_lock);
    pci_err(yd_ndev->pdev, "[%s]: set reqid failed\n", __func__);
    return -1;
}

/*找到reqid对应的entry,给赋值invalid*/
int yd_reqid_clear(uint16_t req_id)
{
    struct yd_ntb_dev *yd_ndev = NULL;
    org_req_id_regs_t *org_reqid_reg = NULL, *tmp_reg = NULL;
    uint8_t i;
    uint32_t val;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    mutex_lock(&yd_ndev->req_id_lock);
    org_reqid_reg = yd_ndev->cfg->group1.ori_regs;
    for(i = 0;i < YD_REQID_MAX_ENTRY_CNT; i++)
    {
        tmp_reg = &org_reqid_reg[i];
        val = ioread32(tmp_reg);
        if(YD_REQID_REQID_DOMAIN(val) == req_id)
        {
            val &= ~(YD_REQID_LID_VALID_BIT);
            iowrite32(val, tmp_reg);
            mutex_unlock(&yd_ndev->req_id_lock);
            
            return i;
        }
        
    }
    mutex_unlock(&yd_ndev->req_id_lock);
    pci_err(yd_ndev->pdev, "[%s]: clear failed\n", __func__);
    return -1;
}

int yd_reqid_get_free_entry_cnt(void)
{
    struct yd_ntb_dev *yd_ndev = NULL;
    uint8_t i, cnt = 0;
    uint32_t val;
    org_req_id_regs_t *org_reqid_reg = NULL, *tmp_reg = NULL;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    mutex_lock(&yd_ndev->req_id_lock);
    org_reqid_reg = yd_ndev->cfg->group1.ori_regs;
    for(i = 0;i < YD_REQID_MAX_ENTRY_CNT; i++)
    {
        tmp_reg = &org_reqid_reg[i];
        val = ioread32(tmp_reg);
        if(val & YD_REQID_LID_VALID_BIT)
        {
            cnt++;
        }
        
    }
    mutex_unlock(&yd_ndev->req_id_lock);
    return (YD_REQID_MAX_ENTRY_CNT - cnt);

}

int yd_reqid_init(struct yd_ntb_dev *yd_ndev)
{
    uint8_t i;
    uint32_t val;
    org_req_id_regs_t *org_reqid_reg = NULL, *tmp_reg = NULL;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    mutex_init(&yd_ndev->req_id_lock);
    mutex_lock(&yd_ndev->req_id_lock);
    org_reqid_reg = yd_ndev->cfg->group1.ori_regs;
    for(i = 0;i < YD_REQID_MAX_ENTRY_CNT; i++)
    {
        tmp_reg = &org_reqid_reg[i];
        val = ioread32(tmp_reg);
        val &= !YD_REQID_LID_VALID_BIT;
        iowrite32(val, tmp_reg);
    }
    mutex_unlock(&yd_ndev->req_id_lock);
    return 0;
}

int yd_reqid_exit(struct yd_ntb_dev *yd_ndev)
{
    return 0;
}
