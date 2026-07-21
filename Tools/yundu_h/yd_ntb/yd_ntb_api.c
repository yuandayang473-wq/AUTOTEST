#include "yd_ntb_api.h"

int sudo_alloc_lut_map_win(uint32_t station_id, dma_addr_t dst_addr, size_t size, dma_addr_t *src_addr, size_t *result_size) 
{
    return yd_alloc_lut_map_win(station_id, dst_addr, size, src_addr, result_size);
}
EXPORT_SYMBOL(sudo_alloc_lut_map_win);

int sudo_free_lut_map_win(uint32_t partirion_id, dma_addr_t dst_addr) 
{
    return yd_free_lut_map_win(partirion_id, dst_addr);
}
EXPORT_SYMBOL(sudo_free_lut_map_win);

int sudo_alloc_dir_map_win(uint32_t station_id, dma_addr_t dst_addr, size_t size, dma_addr_t *src_addr, size_t *result_size) 
{
    return yd_alloc_dir_map_win(station_id, dst_addr, size, src_addr, result_size);
}
EXPORT_SYMBOL(sudo_alloc_dir_map_win);

int sudo_free_dir_map_win(uint32_t station_id, uint64_t addr) 
{
    return yd_free_dir_map_win(station_id, addr);
}
EXPORT_SYMBOL(sudo_free_dir_map_win);

int sudo_ntb_register_msg_cb(uint32_t station_id, uint32_t pipe_id, yd_cb_func_t func, void *arg)
{
    return yd_msg_callback_register(station_id, pipe_id, func, arg);
}
EXPORT_SYMBOL(sudo_ntb_register_msg_cb);

int sudo_ntb_unregister_msg_cb(uint32_t station_id, uint32_t pipe_id)
{
    return yd_msg_callback_unregister(station_id, pipe_id);
}
EXPORT_SYMBOL(sudo_ntb_unregister_msg_cb);

int sudo_ntb_register_db_cb(uint32_t station_id, uint8_t db_num, yd_db_func_t func, void *arg)
{
    return yd_db_callback_register(station_id, db_num, func, arg);
}
EXPORT_SYMBOL(sudo_ntb_register_db_cb);

int sudo_ntb_unregister_db_cb(uint32_t station_id, uint8_t db_num)
{
    return yd_db_callback_unregister(station_id, db_num);
}
EXPORT_SYMBOL(sudo_ntb_unregister_db_cb);

int sudo_ntb_knock_doorbell(uint32_t station_id, uint8_t db_num)
{
    return yd_dm_knock_doorbell(station_id, db_num);
}
EXPORT_SYMBOL(sudo_ntb_knock_doorbell);

int sudo_ntb_send_msg(uint8_t station_id, uint8_t pipe_id, uint8_t *val, size_t size)
{
    return yd_dm_send_msg(station_id, pipe_id, val, size);
}
EXPORT_SYMBOL(sudo_ntb_send_msg);

int sudo_ntb_get_max_pipe(void)
{
    return yd_dm_get_max_pipe();
}
EXPORT_SYMBOL(sudo_ntb_get_max_pipe);

int sudo_ntb_get_topo(uint32_t *station_array, uint32_t *station_cnt)
{
    return yd_topo_get_live_station(station_array,  station_cnt);
}
EXPORT_SYMBOL(sudo_ntb_get_topo);

int sudo_ntb_get_local_station_id(void)
{
    return yd_common_get_local_station_id();
}
EXPORT_SYMBOL(sudo_ntb_get_local_station_id);

int sudo_ntb_set_req_id(uint16_t req_id)
{
    return yd_reqid_set(req_id);
}
EXPORT_SYMBOL(sudo_ntb_set_req_id);

int sudo_ntb_clear_req_id(uint16_t req_id)
{
    return yd_reqid_clear(req_id);
}
EXPORT_SYMBOL(sudo_ntb_clear_req_id);

int sudo_ntb_free_req_id_cnt(void)
{
    return yd_reqid_get_free_entry_cnt();
}
EXPORT_SYMBOL(sudo_ntb_free_req_id_cnt);

int sudo_ntb_get_lut_size(void)
{
    return yd_ld_get_lut_offset();
}
EXPORT_SYMBOL(sudo_ntb_get_lut_size);

int sudo_ntb_get_dir_size(void)
{
    return yd_ld_get_dir_offset();
}
EXPORT_SYMBOL(sudo_ntb_get_dir_size);





void sudo_ntf_cs_station_set(uint8_t cs_station, uint8_t as_usp)
{
    ntf_cs_station_set(cs_station, as_usp);
}
EXPORT_SYMBOL(sudo_ntf_cs_station_set);

void sudo_ntf_build_cs_path(uint8_t cs_station)
{
    ntf_build_cs_path(cs_station);
}
EXPORT_SYMBOL(sudo_ntf_build_cs_path);

void sudo_ntf_p2p_port_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t addr32_align, uint32_t addr64_align, uint8_t cs_station, uint32_t dev_bdf)
{
    ntf_p2p_port_set(src_fabric_station, dst_fabric_station, addr32_align, addr64_align, cs_station, dev_bdf);
}
EXPORT_SYMBOL(sudo_ntf_p2p_port_set);

void sudo_ntf_dst_nt_bus_set(uint8_t cs_station, uint32_t dst_fabric_nt_bus)
{
    ntf_dst_nt_bus_set(cs_station, dst_fabric_nt_bus);
}
EXPORT_SYMBOL(sudo_ntf_dst_nt_bus_set);

void sudo_ntf_internal_sw_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t addr32_align, uint32_t addr64_align)
{
    ntf_internal_sw_set(src_fabric_station, dst_fabric_station, addr32_align, addr64_align);
}
EXPORT_SYMBOL(sudo_ntf_internal_sw_set);

void sudo_ntf_internal_nt_bus_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t dev_bdf)
{
    ntf_internal_nt_bus_set(src_fabric_station, dst_fabric_station, dev_bdf);
}
EXPORT_SYMBOL(sudo_ntf_internal_nt_bus_set);

void sudo_ntf_detect_other_sw_ntb(uint8_t cs_station)
{
    ntf_detect_other_sw_ntb(cs_station);
}
EXPORT_SYMBOL(sudo_ntf_detect_other_sw_ntb);

int sudo_ntf_send_msg(uint8_t cs_station, uint8_t ntf_id, uint8_t *data, uint8_t len)
{
    return ntf_send_msg(cs_station, ntf_id, data, len);
}
EXPORT_SYMBOL(sudo_ntf_send_msg);

int sudo_ntf_msg_cb_register(yd_ntf_func_t func, void *arg)
{
    return yd_ntf_callback_register(func, arg);
}

EXPORT_SYMBOL(sudo_ntf_msg_cb_register);