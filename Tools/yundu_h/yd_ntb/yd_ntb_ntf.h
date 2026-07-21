#include "yd_ntb_common.h"

enum ntf_cmd_type {
    NTF_USP_RES_INIT = 1,
    NTF_CS_PORT_SET,
    NTF_BUILD_CS_PATH,
    NTF_P2P_PORT_SET,
    NTF_DST_NT_BUS_SET,
    NTF_INTERNAL_SW_SET,
    NTF_INTERNAL_NT_BUS_SET,
    NTF_DETECT_OTHER_SW_NTB,
    NTF_SEND_MSG,
};

void ntf_usp_res_init(void);
void ntf_cs_station_set(uint8_t cs_station, uint8_t as_usp);
void ntf_build_cs_path(uint8_t cs_station);
void ntf_p2p_port_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t addr32_align, uint32_t addr64_align, uint8_t cs_station, uint32_t dev_bdf);
void ntf_dst_nt_bus_set(uint8_t cs_station, uint32_t dst_fabric_nt_bus);
void ntf_internal_sw_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t addr32_align, uint32_t addr64_align);
void ntf_internal_nt_bus_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t dev_bdf);
void ntf_detect_other_sw_ntb(uint8_t cs_station);
int ntf_send_msg(uint8_t cs_station, uint8_t ntf_id, uint8_t *data, uint8_t len);