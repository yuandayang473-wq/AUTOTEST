#ifndef __YD_NTB_DB_MSG_H_
#define __YD_NTB_DB_MSG_H_
#include "yd_ntb_common.h"

#define YD_DB_IBMSG0_VALID  BIT(0)
#define YD_DB_IBMSG1_VALID  BIT(8)
#define YD_DB_IBMSG2_VALID  BIT(16)
#define YD_DB_IBMSG3_VALID  BIT(24)

int yd_dm_knock_doorbell(uint32_t station_id, uint8_t db_num);
int yd_dm_send_msg(uint8_t station_id, uint8_t pipe_id, uint8_t *val, size_t size);
int yd_dm_get_max_pipe(void);
int yd_msg_callback_register(uint32_t station_id, uint32_t pipe_id, yd_cb_func_t func, void *arg);
int yd_msg_callback_unregister(uint32_t station_id, uint32_t pipe_id);
int yd_db_callback_register(uint32_t station_id, uint8_t db_num, yd_db_func_t func, void *arg);
int yd_db_callback_unregister(uint32_t station_id, uint8_t db_num);
int yd_ntb_init_db_msg(struct yd_ntb_dev *yd_ndev);
void yd_ntb_exit_db_msg(struct yd_ntb_dev *yd_ndev);
int yd_ntf_callback_register(yd_ntf_func_t func, void *arg);
#endif