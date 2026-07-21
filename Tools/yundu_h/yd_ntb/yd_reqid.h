#ifndef __YD_REQID_H
#define __YD_REQID_H
#include "yd_ntb_common.h"
int yd_reqid_init(struct yd_ntb_dev *yd_ndev);
int yd_reqid_exit(struct yd_ntb_dev *yd_ndev);
int yd_reqid_set(uint16_t req_id);
int yd_reqid_clear(uint16_t req_id);
int yd_reqid_get_free_entry_cnt(void);
#endif