#include "yd_ntb_common.h"

int yd_ntb_msi_init(struct yd_ntb_dev *yd_ndev)
{
    group13_msi_g0_t *group13_msi_g0 = NULL;
    group13_msi_g0 = &yd_ndev->cfg->group13_msi_g0;
    iowrite32(0x80808080, &group13_msi_g0->value);
    iowrite32(0x80808080, &group13_msi_g0->value);
    return 0;
}