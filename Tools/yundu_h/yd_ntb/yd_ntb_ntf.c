#include "yd_ntb_ntf.h"




static void ntf_set_sw(void)
{
    struct yd_ntb_dev *yd_ndev      = NULL;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return;
    }
    //group13_rsvint_trgr_ntb_rsvint0 = &yd_ndev->cfg->group13_rsvint_trgr_ntb_rsvint0;
    iowrite32(0x1, &yd_ndev->cfg->group13_rsvint_trgr_ntb_rsvint0);
}

void ntf_usp_res_init(void)
{
    struct yd_ntb_dev *yd_ndev      = NULL;
    uint32_t val;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return ;
    }

    /*cmd*/
    val = NTF_USP_RES_INIT;
    iowrite32(val, &yd_ndev->cfg->group10[0].value);

    ntf_set_sw();

}

void ntf_cs_station_set(uint8_t cs_station, uint8_t as_usp)
{
    struct yd_ntb_dev *yd_ndev      = NULL;
    uint32_t val;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return;
    }

    /*cmd*/
    val = NTF_CS_PORT_SET;
    iowrite32(val, &yd_ndev->cfg->group10[0].value);

    val = cs_station;
    iowrite32(val, &yd_ndev->cfg->group10[1].value);

    val = as_usp;
    iowrite32(val, &yd_ndev->cfg->group10[2].value);

    ntf_set_sw();
}

void ntf_build_cs_path(uint8_t cs_station)
{
    struct yd_ntb_dev *yd_ndev      = NULL;
    uint32_t val;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return;
    }

    /*cmd*/
    val = NTF_BUILD_CS_PATH;
    iowrite32(val, &yd_ndev->cfg->group10[0].value);

    val = cs_station;
    iowrite32(val, &yd_ndev->cfg->group10[1].value);

    ntf_set_sw();
}

void ntf_p2p_port_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t addr32_align, uint32_t addr64_align, uint8_t cs_station, uint32_t dev_bdf)
{
    struct yd_ntb_dev *yd_ndev      = NULL;
    uint32_t val;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return;
    }

    /*cmd*/
    val = NTF_P2P_PORT_SET;
    iowrite32(val, &yd_ndev->cfg->group10[0].value);

    val = src_fabric_station;
    iowrite32(val, &yd_ndev->cfg->group10[1].value);

    val = dst_fabric_station;
    iowrite32(val, &yd_ndev->cfg->group10[2].value);

    val = addr32_align;
    iowrite32(val, &yd_ndev->cfg->group10[3].value);

    val = addr64_align;
    iowrite32(val, &yd_ndev->cfg->group10[4].value);

    val = cs_station;
    iowrite32(val, &yd_ndev->cfg->group10[5].value);

    val = dev_bdf;
    iowrite32(val, &yd_ndev->cfg->group10[6].value);

    ntf_set_sw();
}

void ntf_dst_nt_bus_set(uint8_t cs_station, uint32_t dst_fabric_nt_bus)
{
    struct yd_ntb_dev *yd_ndev      = NULL;
    uint32_t val;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return;
    }

    /*cmd*/
    val = NTF_DST_NT_BUS_SET;
    iowrite32(val, &yd_ndev->cfg->group10[0].value);

    val = cs_station;
    iowrite32(val, &yd_ndev->cfg->group10[1].value);

    val = dst_fabric_nt_bus;
    iowrite32(val, &yd_ndev->cfg->group10[2].value);

    ntf_set_sw();
}

void ntf_internal_sw_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t addr32_align, uint32_t addr64_align)
{
    struct yd_ntb_dev *yd_ndev      = NULL;
    uint32_t val;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return;
    }

    /*cmd*/
    val = NTF_INTERNAL_SW_SET;
    iowrite32(val, &yd_ndev->cfg->group10[0].value);

    val = src_fabric_station;
    iowrite32(val, &yd_ndev->cfg->group10[1].value);

    val = dst_fabric_station;
    iowrite32(val, &yd_ndev->cfg->group10[2].value);

    val = addr32_align;
    iowrite32(val, &yd_ndev->cfg->group10[3].value);

    val = addr64_align;
    iowrite32(val, &yd_ndev->cfg->group10[4].value);

    ntf_set_sw();
}


void ntf_internal_nt_bus_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t dev_bdf)
{
    struct yd_ntb_dev *yd_ndev      = NULL;
    uint32_t val;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return;
    }

    /*cmd*/
    val = NTF_INTERNAL_NT_BUS_SET;
    iowrite32(val, &yd_ndev->cfg->group10[0].value);

    val = src_fabric_station;
    iowrite32(val, &yd_ndev->cfg->group10[1].value);

    val = dst_fabric_station;
    iowrite32(val, &yd_ndev->cfg->group10[2].value);

    val = dev_bdf;
    iowrite32(val, &yd_ndev->cfg->group10[3].value);

    ntf_set_sw();
}

void ntf_detect_other_sw_ntb(uint8_t cs_station)
{
    struct yd_ntb_dev *yd_ndev      = NULL;
    uint32_t val;
    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return;
    }
    val = NTF_DETECT_OTHER_SW_NTB;
    iowrite32(val, &yd_ndev->cfg->group10[0].value);

    val = cs_station;
    iowrite32(val, &yd_ndev->cfg->group10[1].value);

    ntf_set_sw();
}


int ntf_send_msg(uint8_t cs_station, uint8_t ntf_id, uint8_t *data, uint8_t len)
{
    struct yd_ntb_dev *yd_ndev      = NULL;
    uint32_t val, i;

    if(len > NTF_MSG_MAX_LEN)
    {
        return -1;
    }

    yd_ndev = yd_common_get_global_ndev();
    if(!yd_ndev)
    {
        return -1;
    }
    val = NTF_SEND_MSG;
    iowrite32(val, &yd_ndev->cfg->group10[0].value);

    val = cs_station;
    iowrite32(val, &yd_ndev->cfg->group10[1].value);

    val = ntf_id;
    iowrite32(val, &yd_ndev->cfg->group10[2].value);

    for(i = 3; i < (3 + NTF_MSG_MAX_LEN);i++)
    {
        val = data[i-3];
        iowrite32(val, &yd_ndev->cfg->group10[i].value);
    }

    ntf_set_sw();
    return 0;
}