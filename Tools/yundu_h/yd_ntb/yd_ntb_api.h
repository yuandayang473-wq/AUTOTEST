#ifndef __YD_NTB_API_H
#define __YD_NTB_API_H

#include "yd_ntb_common.h"
#include "yd_ntb_db_msg.h"
#include "yd_ntb_lut_dir.h"
#include "yd_reqid.h"
#include "yd_ntb_ntf.h"

int sudo_alloc_lut_map_win(uint32_t station_id, dma_addr_t dst_addr, size_t size, dma_addr_t *src_addr, size_t *result_size);
int sudo_free_lut_map_win(uint32_t partirion_id, dma_addr_t dst_addr);
int sudo_alloc_dir_map_win(uint32_t station_id, dma_addr_t dst_addr, size_t size, dma_addr_t *src_addr, size_t *result_size);
int sudo_free_dir_map_win(uint32_t station_id, uint64_t addr);
int sudo_ntb_register_msg_cb(uint32_t station_id, uint32_t pipe_id, yd_cb_func_t func, void *arg);
int sudo_ntb_unregister_msg_cb(uint32_t station_id, uint32_t pipe_id);
int sudo_ntb_register_db_cb(uint32_t station_id, uint8_t db_num, yd_db_func_t func, void *arg);
int sudo_ntb_unregister_db_cb(uint32_t station_id, uint8_t db_num);
int sudo_ntb_knock_doorbell(uint32_t station_id, uint8_t db_num);
int sudo_ntb_send_msg(uint8_t station_id, uint8_t pipe_id, uint8_t *val, size_t size);
int sudo_ntb_get_max_pipe(void);
int sudo_ntb_get_topo(uint32_t *station_array, uint32_t *station_cnt);
int sudo_ntb_get_local_station_id(void);
int sudo_ntb_set_req_id(uint16_t req_id);
int sudo_ntb_clear_req_id(uint16_t req_id);
int sudo_ntb_free_req_id_cnt(void);
int sudo_ntb_get_lut_size(void);
int sudo_ntb_get_dir_size(void);


void sudo_ntf_cs_station_set(uint8_t cs_station, uint8_t as_usp);
void sudo_ntf_build_cs_path(uint8_t cs_station);
void sudo_ntf_p2p_port_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t addr32_align, uint32_t addr64_align, uint8_t cs_station, uint32_t dev_bdf);
void sudo_ntf_dst_nt_bus_set(uint8_t cs_station, uint32_t dst_fabric_nt_bus);
void sudo_ntf_internal_sw_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t addr32_align, uint32_t addr64_align);
void sudo_ntf_internal_nt_bus_set(uint8_t src_fabric_station, uint8_t dst_fabric_station, uint32_t dev_bdf);
void sudo_ntf_detect_other_sw_ntb(uint8_t cs_station);
int sudo_ntf_send_msg(uint8_t cs_station, uint8_t ntf_id, uint8_t *data, uint8_t len);
int sudo_ntf_msg_cb_register(yd_ntf_func_t func, void *arg);
#endif