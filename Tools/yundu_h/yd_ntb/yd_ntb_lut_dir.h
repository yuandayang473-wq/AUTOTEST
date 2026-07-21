#ifndef __YD_NTB_LUT_DIR_H
#define __YD_NTB_LUT_DIR_H
#include "yd_ntb_common.h"



int yd_ld_init_lut(struct yd_ntb_dev *yd_ndev);
void yd_ld_exit_lut(struct yd_ntb_dev *yd_ndev);
int yd_ld_init_dir(struct yd_ntb_dev *yd_ndev);
void yd_ld_exit_dir(struct yd_ntb_dev *yd_ndev);
int yd_alloc_lut_map_win(uint32_t station_id, dma_addr_t dst_addr, size_t size, dma_addr_t *src_addr, size_t *result_size);
int yd_free_lut_map_win(uint32_t station_id, dma_addr_t dst_addr);
int yd_alloc_dir_map_win(uint32_t station_id, dma_addr_t dst_addr, size_t size, dma_addr_t *src_addr, size_t *result_size);
int yd_free_dir_map_win(uint32_t station_id, uint64_t addr) ;
int yd_ld_get_lut_offset(void);
int yd_ld_get_dir_offset(void);
#endif