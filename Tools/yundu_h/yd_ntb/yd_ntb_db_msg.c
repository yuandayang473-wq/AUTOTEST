#include "yd_ntb_db_msg.h"


#define YD_DR_IDB1_ENABLE    BIT(0)
#define YD_DR_IDB2_ENABLE    BIT(8)
#define YD_DR_IDB3_ENABLE    BIT(16)


#define YD_ODB_NUM  2
int yd_dm_knock_doorbell(uint32_t station_id, uint8_t db_num)
{
    int ret = 0;
    struct yd_ntb_dev *yd_ndev      = NULL;
    group7_t *group7 = NULL;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }

    group7 = &yd_ndev->cfg->group7;
    /*补充一个对方partition是否在拓扑中*/
    if(station_id == yd_ndev->station_id || station_id > YD_MAX_STATION_ID || db_num > 2)
    {
        pci_err(yd_ndev->pdev, "[%s]: station_id %d is invalid!!!\n", __func__, station_id);
        return -1;
    }

    mutex_lock(&yd_ndev->db_msg_lock);
    /*根据对端station id写odb寄存器*/
    if(db_num == 0)
    {
        group7->odb_regs[station_id].odb1 = 1;
        group7->odb_regs[station_id].odb1 = 0;
    }
    else if(db_num == 1)
    {
        group7->odb_regs[station_id].odb2 = 1;
        group7->odb_regs[station_id].odb2 = 0;
    }
    else if(db_num == 2){
#ifdef MUL_DW_PACKET
        group7->odb_regs[station_id].odb3 = 1;
        group7->odb_regs[station_id].odb3 = 0;
#else
        ret = -1;
#endif
    }
    else{
        ret = -1;
    }
    //iowrite8(YD_DR_IDB1_ENABLE, &db_regs->odb_regs[station_id]);
    mutex_unlock(&yd_ndev->db_msg_lock);
    
    return ret;
}

#define YD_DM_PIPE_MSG_SIZE 128
#define YD_DM_PIPE_MAX_ID   8

#define YD_DM_PIPE_OBMSG_CNT    32
int yd_dm_send_msg(uint8_t station_id, uint8_t pipe_id, uint8_t *val, size_t size)
{
    struct yd_ntb_dev *yd_ndev      = NULL;
    group5_t *group5  = NULL;

    group7_t *group7 = NULL;

    uint8_t start_field = 0, i, times, remainder;
    uint32_t tmp_val = 0;
    if(size <= 0 || size > YD_DM_PIPE_MSG_SIZE ||  station_id >= YD_MAX_STATION_ID)
    {
        return -1;
    }

    times = size / 4;
    remainder = size % 4;
    if(remainder)
    {
        times++;
    }

    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    group5 = &yd_ndev->cfg->group5;

    group7 = &yd_ndev->cfg->group7;
    mutex_lock(&yd_ndev->db_msg_lock);
    for(i = 0;i < (times - 1); i++)
    {

        iowrite32(*(uint32_t *)(&val[i*4]), &group5->obmsg_field[station_id][start_field++]);
    }
    
    if(remainder)
    {
        memcpy(&tmp_val, (uint32_t *)&val[i*4], remainder);
    }
    else{
        memcpy(&tmp_val, (uint32_t *)&val[i*4], 4);
    }
    
    iowrite32(tmp_val, &group5->obmsg_field[station_id][start_field++]);
#ifndef MUL_DW_PACKET
    group7->odb_regs[station_id].odb3 = 1;
    group7->odb_regs[station_id].odb3 = 0;
#endif
    mutex_unlock(&yd_ndev->db_msg_lock);
    return 0;

}

int yd_dm_get_max_pipe(void)
{
    return YD_DM_PIPE_MAX_ID;
}

/*需要遍历每个IBMSG_Valid，然后哪个有效就是哪个就是拿来数据了*/


static void yd_dm_run_callback(struct yd_callback_info *cb_info, uint32_t dst_partition, uint8_t *data, size_t size)
{
    struct yd_callback_info  *tmp_callback  = NULL;
    struct list_head *node_list             = NULL;
    list_for_each(node_list, &cb_info->list)
    {
        tmp_callback = list_entry(node_list, struct yd_callback_info, list);
        if(tmp_callback->cb_func)
        {
            tmp_callback->cb_func(0, dst_partition, data, size, tmp_callback->cb_arg);
        }
    }
}

/*db_num : 0~2*/
static void yd_db_run_callback(struct yd_db_callback_info *cb_info, uint32_t dst_partition, uint8_t db_num)
{
    struct yd_db_callback_info  *tmp_callback  = NULL;
    struct list_head *node_list             = NULL;
    list_for_each(node_list, &cb_info->list)
    {
        tmp_callback = list_entry(node_list, struct yd_db_callback_info, list);
        if(tmp_callback->cb_func && tmp_callback->db_num == db_num)
        {
            tmp_callback->cb_func(0, dst_partition, db_num, tmp_callback->cb_arg);
        }
    }
}

enum ntf_to_host_cmd {
    NTF_MULITE_FABRIC_INFO = 1,
    NTF_INTERNAL_FABRIC_INFO,
    NTF_DETECT_RESP,
    NTF_LOCAL_MSG,
};
#define NTF_MSG_TO_HOST_POS 48
#define NTF_DETECT_ID_REG_POS    16
#define NTB_RESP_DETECT_ID_REG_POS   (NTF_DETECT_ID_REG_POS + 1)

static void yd_ntf_int_deal(struct yd_ntb_dev *yd_ndev, uint8_t ntf_cmd)
{
    uint32_t data[NTF_MSG_MAX_LEN], i;
    char print_buf[512]= {0};
    // if(!yd_ndev->ntf_callback.callback_info.flag) tmp#
    // {
    //     return;
    // }

    if(ntf_cmd == NTF_DETECT_RESP)
    {
        for(i = 0;i < NTF_MSG_MAX_LEN/4;i++)
        {
            data[i] = ioread32(&yd_ndev->cfg->group10[NTB_RESP_DETECT_ID_REG_POS + i].value);
            sprintf(print_buf + strlen(print_buf), "0x%x ", data[i]);
        }
    }
    else{
        for(i = 0;i < NTF_MSG_MAX_LEN/4;i++)
        {
            data[i] = ioread32(&yd_ndev->cfg->group10[NTF_MSG_TO_HOST_POS + i].value);
            sprintf(print_buf + strlen(print_buf), "0x%x ", data[i]);
        }
    }

    printk("[%s]: ntf cmd = %d, print buf %s\n", __func__, ntf_cmd, print_buf);
    printk("end\n");
    if(!yd_ndev->ntf_callback.callback_info.flag) 
    {
        return;
    }

    yd_ndev->ntf_callback.callback_info.cb_func(ntf_cmd, (uint8_t *)&data, 
            NTF_MSG_MAX_LEN, yd_ndev->ntf_callback.callback_info.cb_arg);
    
}


static void yd_msg_int_deal(struct yd_ntb_dev *yd_ndev, uint8_t station_id)
{
    group6_t *group6      = NULL;
    struct yd_msg_callack *msg_callback = NULL;


    uint32_t i,val, data[YD_DM_PIPE_OBMSG_CNT];
    uint8_t start_field = 0, data_len;
    uint8_t num = 0;
    printk("[%s]: %d: enter\n", __func__, __LINE__);
#ifdef MUL_DW_PACKET
    uint8_t start_flag = 0, end_flag = 0;
#endif
    msg_callback = &yd_ndev->msg_callback;
    group6 = &yd_ndev->cfg->group6;
    data_len = 0;
    memset(&data, 0, sizeof(uint32_t) * YD_DM_PIPE_OBMSG_CNT);
    start_field = 0;
    for(i = 0;i<YD_NTB_IBMSG_GROUP_NUM;i++)
    {
        val = ioread32(&group6->ibmsg_valid_field[station_id][i]);
    	printk("[%s]: %d: enter i = %d, val = %d\n", __func__, __LINE__, i, val);

#ifdef MUL_DW_PACKET   
        printk("[%s]: %d: i = %d, val = %x,continue\n", __func__, __LINE__, i , val);
        if(!val)
        {
            /*如果前面已经发现有msg header了，并且这里发现再往后没有数据了就截至通知给用户*/
            if(start_flag)
            {
		        printk("[%s]: %d i = %d, data len = %d, will run callback\n", __func__, __LINE__, i, data_len);
                yd_dm_run_callback(&msg_callback->callback_info[station_id], station_id, (uint8_t *)data, data_len*4);
                break;
            }
            start_field += 4;
            continue;
        }
        start_flag = 1;

        if(val & BIT(0))
        {
            end_flag = 1;
            //iowrite32(BIT(0), &ibmsg_cfg->ibmsg_valid_field[station_id][i]);
            group6->ibmsg_valid_field[station_id][i].ibmsg0_valid = 1;
            data[data_len++] = ioread32(&group6->ibmsg_field[station_id][start_field]);
	        printk("[%s]: %d: data = 0x%x, data len = %d\n", __func__, __LINE__, (data[data_len-1]), data_len);
            
        }
        else{
            if(end_flag)
            {
                printk("[%s]: %d i = %d, data len = %d, will run callback\n", __func__, __LINE__, i, data_len);
                yd_dm_run_callback(&msg_callback->callback_info[station_id], station_id, (uint8_t *)data, data_len*4);
                break;
            }
        }
        start_field++;
        if(val & BIT(8))
        {
            end_flag = 1;
            group6->ibmsg_valid_field[station_id][i].ibmsg1_valid = 1;
            //iowrite32(BIT(8), &ibmsg_cfg->ibmsg_valid_field[station_id][i]);
            data[data_len++] = ioread32(&group6->ibmsg_field[station_id][start_field]);
	        printk("[%s]: %d: data = 0x%x, data len = %d\n", __func__, __LINE__, (data[data_len-1]), data_len);
            
        }
        else{
            if(end_flag)
            {
                printk("[%s]: %d i = %d, data len = %d, will run callback\n", __func__, __LINE__, i, data_len);
                yd_dm_run_callback(&msg_callback->callback_info[station_id], station_id, (uint8_t *)data, data_len*4);
                break;
            }
        }
        start_field++;
        if(val & BIT(16))
        {
            end_flag = 1;
            group6->ibmsg_valid_field[station_id][i].ibmsg2_valid = 1;
            //iowrite32(BIT(16), &ibmsg_cfg->ibmsg_valid_field[station_id][i]);
            data[data_len++] = ioread32(&group6->ibmsg_field[station_id][start_field]);
	        printk("[%s]: %d: data = 0x%x, data len = %d\n", __func__, __LINE__, (data[data_len-1]), data_len);
           
        }
        else{
            if(end_flag)
            {
                printk("[%s]: %d i = %d, data len = %d, will run callback\n", __func__, __LINE__, i, data_len);
                yd_dm_run_callback(&msg_callback->callback_info[station_id], station_id, (uint8_t *)data, data_len*4);
                break;
            }
        }
        start_field++;
        if(val & BIT(24))
        {
            end_flag = 1;
            group6->ibmsg_valid_field[station_id][i].ibmsg3_valid = 1;
            //iowrite32(BIT(24), &ibmsg_cfg->ibmsg_valid_field[station_id][i]);
            data[data_len++] = ioread32(&group6->ibmsg_field[station_id][start_field]);
	        printk("[%s]: %d: data = 0x%x, data len = %d\n", __func__, __LINE__, (data[data_len-1]), data_len);
            
        }
        else{
            if(end_flag)
            {
                printk("[%s]: %d i = %d, data len = %d, will run callback\n", __func__, __LINE__, i, data_len);
                yd_dm_run_callback(&msg_callback->callback_info[station_id], station_id, (uint8_t *)data, data_len*4);
                break;
            }
        }
        start_field++;
        
#else
        if(!val)
        {
            if(data_len)
                yd_dm_run_callback(&msg_callback->callback_info[station_id], station_id, (uint8_t *)data, data_len*4);
            break;
        } 
        iowrite32(val, &group6->ibmsg_valid_field[station_id][i]);
        num = fls(val) / 8 + 1;
        if(num  == 4)
        {
            /**/
            data[data_len++] = ioread32(&group6->ibmsg_field[station_id][start_field++]);
            data[data_len++] = ioread32(&group6->ibmsg_field[station_id][start_field++]);
            data[data_len++] = ioread32(&group6->ibmsg_field[station_id][start_field++]);
            data[data_len++] = ioread32(&group6->ibmsg_field[station_id][start_field++]);
        }
        else{
            while(num--)
            {
                data[data_len++] = ioread32(&group6->ibmsg_field[station_id][start_field++]);
            }
            yd_dm_run_callback(&msg_callback->callback_info[station_id], station_id, (uint8_t *)data, data_len*4);
            break;
                
        }
#endif
    }
}


#define NTF_TO_HOST_CMD_POS 15

static irqreturn_t yd_dm_msg_work(struct yd_ntb_dev *yd_ndev)
{
    
    struct yd_db_callack *db_callback = NULL;
    group7_t *group7 = NULL;
    uint32_t ntf_cmd;
    irqreturn_t iret = IRQ_NONE;

    uint32_t i,val;
    
    db_callback = &yd_ndev->db_callback;
    group7 = &yd_ndev->cfg->group7;

    ntf_cmd = ioread32(&yd_ndev->cfg->group10[NTF_TO_HOST_CMD_POS].value);
    printk("[%s]: ntf cmd = %d\n", __func__, ntf_cmd);
    if(ntf_cmd)
    {
        iret = IRQ_HANDLED;
        yd_ntf_int_deal(yd_ndev, ntf_cmd);
        iowrite32(0, &yd_ndev->cfg->group10[NTF_TO_HOST_CMD_POS].value);
    }
    for(i = 0;i<YD_MAX_STATION_ID;i++)
    {
        val = ioread32(&group7->idb_regs[i]);
        iowrite32(val, &group7->idb_regs[i]);
        printk("idb reg val 0x%x", val);
        if(val & BIT(8))
        {
            iret = IRQ_HANDLED;
            yd_db_run_callback(&db_callback->callback_info[i], i, 0);  
            
        }
        if(val & BIT(16))
        {
            iret = IRQ_HANDLED;
            yd_db_run_callback(&db_callback->callback_info[i], i, 1);  
        }
        if(val & BIT(24))
        {
            iret = IRQ_HANDLED;
#ifndef MUL_DW_PACKET
            yd_msg_int_deal(yd_ndev, i);
#else
            yd_db_run_callback(&db_callback->callback_info[i], i, 1);  
#endif 
        }
        if(val & BIT(0))
        {
            iret = IRQ_HANDLED;
#ifdef MUL_DW_PACKET
            yd_msg_int_deal(yd_ndev, i);
#endif
        }
    }
   
    return iret;
}

static irqreturn_t yd_dm_msg_notify(int irq, void *dev)
{
    /*从ibmsg寄存器取数据，然后回调给事务层*/
    return IRQ_WAKE_THREAD;
}

/*server接受到数据得回调*/
static irqreturn_t yd_dm_msg_isr(int irq, void *dev)
{
    /*从ibmsg寄存器取数据，然后回调给事务层*/
    struct yd_ntb_dev *yd_ndev = (struct yd_ntb_dev *)dev;
    //schedule_work(&yd_ndev->message_work);
    printk("[%s]: enter", __func__);
    return yd_dm_msg_work(yd_ndev);
}

static void yd_dm_db_work(struct work_struct *work)
{

}

int yd_ntf_callback_register(yd_ntf_func_t func, void *arg)
{
    struct yd_ntb_dev *yd_ndev  = NULL;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }

    if(yd_ndev->ntf_callback.callback_info.flag)
    {
        return -1;
    }

    yd_ndev->ntf_callback.callback_info.cb_func = func;
    yd_ndev->ntf_callback.callback_info.cb_arg = arg;
    yd_ndev->ntf_callback.callback_info.flag = 1;
    return 0;

}

int yd_db_callback_register(uint32_t station_id, uint8_t db_num, yd_db_func_t func, void *arg)
{
    struct yd_db_callack *db_callback     = NULL;
    struct yd_db_callback_info *callback_info  = NULL;
    struct list_head *db_list, *node_list  = NULL;
    struct yd_ntb_dev *yd_ndev              = NULL;
 
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    db_callback    = &yd_ndev->db_callback;
    db_list        = &db_callback->callback_info[station_id].list;
    list_for_each(node_list, db_list)
    {
        callback_info = list_entry(node_list, struct yd_db_callback_info, list);
        if(callback_info->db_num == db_num)
        {
            pci_dbg(yd_ndev->pdev, "[%s]: db num already register!!!\n", __func__);
            return -1;
        }
    }

    callback_info = kzalloc(sizeof(struct yd_db_callback_info), GFP_KERNEL);
    if(!callback_info)
    {
        pci_dbg(yd_ndev->pdev, "[%s]: callback_info kzalloc failed!!!\n", __func__);
        return -1;
    }
    callback_info->cb_func = func;
    callback_info->cb_arg = arg;
    callback_info->db_num = db_num;
    list_add(&callback_info->list, db_list);
    return 0;
}


int yd_msg_callback_register(uint32_t station_id, uint32_t pipe_id, yd_cb_func_t func, void *arg)
{
    struct yd_msg_callack *msg_callback     = NULL;
    struct yd_callback_info *callback_info  = NULL;
    struct list_head *msg_list, *node_list  = NULL;
    struct yd_ntb_dev *yd_ndev              = NULL;
 
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    msg_callback    = &yd_ndev->msg_callback;
    msg_list        = &msg_callback->callback_info[station_id].list;
    list_for_each(node_list, msg_list)
    {
        callback_info = list_entry(node_list, struct yd_callback_info, list);
        if(callback_info->pipe_id == pipe_id)
        {
            pci_err(yd_ndev->pdev, "[%s]: pipe id already register!!!\n", __func__);
            return -1;
        }
    }

    callback_info = kzalloc(sizeof(struct yd_callback_info), GFP_KERNEL);
    if(!callback_info)
    {
        pci_err(yd_ndev->pdev, "[%s]: callback_info kzalloc failed!!!\n", __func__);
        return -1;
    }
    callback_info->cb_func = func;
    callback_info->cb_arg = arg;
    list_add(&callback_info->list, msg_list);
    return 0;
}


int yd_ntf_callback_unregister(void)
{
    struct yd_ntb_dev *yd_ndev = NULL;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }

    yd_ndev->ntf_callback.callback_info.flag = 0;
    return 0;
    
}

int yd_msg_callback_unregister(uint32_t station_id, uint32_t pipe_id)
{
    struct yd_msg_callack *msg_callback     = NULL;
    struct yd_callback_info *callback_info  = NULL;
    struct list_head *msg_list, *node_list  = NULL;
    struct yd_ntb_dev *yd_ndev = NULL;
 
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    msg_callback = &yd_ndev->msg_callback;
    msg_list = &msg_callback->callback_info[station_id].list;

    list_for_each(node_list, msg_list)
    {
        callback_info = list_entry(node_list, struct yd_callback_info, list);
        if(callback_info->pipe_id == pipe_id)
        {
            
            list_del(&callback_info->list);
            kfree(callback_info);
            return 0;
        }
    }
    return -1;
}


int yd_db_callback_unregister(uint32_t station_id, uint8_t db_num)
{
    struct yd_db_callack *db_callback     = NULL;
    struct yd_db_callback_info *callback_info  = NULL;
    struct list_head *db_list, *node_list  = NULL;
    struct yd_ntb_dev *yd_ndev = NULL;
 
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    db_callback = &yd_ndev->db_callback;
    db_list = &db_callback->callback_info[station_id].list;

    list_for_each(node_list, db_list)
    {
        callback_info = list_entry(node_list, struct yd_db_callback_info, list);
        if(callback_info->db_num == db_num)
        {
            
            list_del(&callback_info->list);
            kfree(callback_info);
            return 0;
        }
    }
    return -1;
}

int yd_ntb_init_db_msg(struct yd_ntb_dev *yd_ndev)
{
    /*获取中断号，给每个中断进行注册回调函数*/
    int ret;
    struct device *dev                      = NULL;
    struct yd_callback_info *msg_callback_info  = NULL;
    struct yd_db_callback_info *db_callback_info  = NULL;
    uint8_t i;
    dev = &yd_ndev->pdev->dev;


    ret = request_threaded_irq(yd_ndev->ibmsg_irq, yd_dm_msg_notify, yd_dm_msg_isr,
                    IRQF_SHARED, KBUILD_MODNAME, yd_ndev);
/*
    ret = request_irq(yd_ndev->ibmsg_irq, yd_dm_msg_isr,
                    0, KBUILD_MODNAME, yd_ndev);
                    */
    if(ret)
    {
        return ret;
    }


    //INIT_WORK(&yd_ndev->message_work, yd_dm_msg_work);
    INIT_WORK(&yd_ndev->doorbell_work, yd_dm_db_work);
    
    for(i = 0; i < YD_MAX_STATION_ID; i++)
    {
        msg_callback_info = &yd_ndev->msg_callback.callback_info[i];
        INIT_LIST_HEAD(&msg_callback_info->list);
        db_callback_info = &yd_ndev->db_callback.callback_info[i];
        INIT_LIST_HEAD(&db_callback_info->list);
    }
    
    mutex_init(&yd_ndev->db_msg_lock);
    return 0;
    free_irq(yd_ndev->ibmsg_irq, yd_ndev);
    return ret;
}

void yd_ntb_exit_db_msg(struct yd_ntb_dev *yd_ndev)
{
    struct device *dev  = NULL;

    dev = &yd_ndev->pdev->dev;
    
    free_irq(yd_ndev->ibmsg_irq, yd_ndev);
   
}
