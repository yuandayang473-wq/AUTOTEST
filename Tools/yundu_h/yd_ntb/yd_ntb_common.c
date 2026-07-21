#include "yd_ntb_common.h"

struct yd_ntb_dev *g_yd_ndev;

int yd_common_set_global_ndev(struct yd_ntb_dev *yd_ndev)
{
    g_yd_ndev = yd_ndev;
    return 0;
}

struct yd_ntb_dev *yd_common_get_global_ndev(void)
{
    return g_yd_ndev;
}

#define YD_TOPO_STATION0_LIVE   BIT(0)
#define YD_TOPO_STATION1_LIVE   BIT(1)
#define YD_TOPO_STATION2_LIVE   BIT(2)
#define YD_TOPO_STATION3_LIVE   BIT(3)
#define YD_TOPO_STATION4_LIVE   BIT(4)
#define YD_TOPO_STATION5_LIVE   BIT(5)
#define YD_TOPO_STATION6_LIVE   BIT(6)

#define YD_TOPO_STATION0_ID     0x0
#define YD_TOPO_STATION1_ID     0x1
#define YD_TOPO_STATION2_ID     0x2
#define YD_TOPO_STATION3_ID     0x3
#define YD_TOPO_STATION4_ID     0x4
#define YD_TOPO_STATION5_ID     0x5
#define YD_TOPO_STATION6_ID     0x6

int yd_topo_init_live_station(void)
{
    struct yd_ntb_dev *yd_ndev          = NULL;
    uint32_t val, i                     = 0;
    group0_t *group0    = NULL;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
    
        return -1;
    }
    group0 = &yd_ndev->cfg->group0;
   
    val = readw(group0);

    if(val & YD_TOPO_STATION0_LIVE)
    {
        yd_ndev->station_topo[i++] = YD_TOPO_STATION0_ID;
    }
    if(val & YD_TOPO_STATION1_LIVE)
    {
       
        yd_ndev->station_topo[i++] = YD_TOPO_STATION1_ID;
    }
    if(val & YD_TOPO_STATION2_LIVE)
    {
        
        yd_ndev->station_topo[i++] = YD_TOPO_STATION2_ID;
    }
    if(val & YD_TOPO_STATION3_LIVE)
    {
       
        yd_ndev->station_topo[i++] = YD_TOPO_STATION3_ID;

    }
    if(val & YD_TOPO_STATION4_LIVE)
    {
        
        yd_ndev->station_topo[i++] = YD_TOPO_STATION4_ID;
    }
    if(val & YD_TOPO_STATION5_LIVE)
    {
        
        yd_ndev->station_topo[i++] = YD_TOPO_STATION5_ID;
    }
    if(val & YD_TOPO_STATION6_LIVE)
    {

        yd_ndev->station_topo[i++] = YD_TOPO_STATION6_ID;

    }
    yd_ndev->ntb_cnt = i;
    return 0;
}
int yd_topo_get_live_station(uint32_t *station_array, uint32_t *station_cnt)
{
    struct yd_ntb_dev *yd_ndev  = NULL;
    uint32_t i                  = 0;

    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }

    for(i = 0;i< yd_ndev->ntb_cnt;i++)
    {
        station_array[i] = yd_ndev->station_topo[i];
    }
    *station_cnt = yd_ndev->ntb_cnt;

    return 0;
}

#define YD_COMMON_ORG_ENTRY_DOMAIN(x) (((uint32_t)x & GENMASK(23, 16)) > 16)
int yd_common_get_local_station_id(void)
{
    struct yd_ntb_dev *yd_ndev = NULL;

    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    
    return yd_ndev->station_id;
}

int yd_common_init_local_station_id(void)
{
    struct yd_ntb_dev *yd_ndev = NULL;
    group1_t *group1 = NULL;
    uint32_t val;
    uint8_t df_index = 0;

    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        
        return -1;
    }

    group1 = &yd_ndev->cfg->group1;
    val = ioread32(&group1->ori_regs[0]);
    df_index = (val & GENMASK(23, 16)) >> 16;
    return (df_index + 1)/32;
}

bool yd_common_station_id_valid(uint8_t station_id)
{
    uint8_t i;
    struct yd_ntb_dev *yd_ndev = NULL;

    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    for(i = 0;i< YD_MAX_STATION_ID;i++)
    {
        if(yd_ndev->station_topo[i] == station_id){
            return true;
        }
    }
    return false;
}