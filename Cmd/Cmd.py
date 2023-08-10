class UUTOS:
    reboot = "reboot"
    dmidecode = "dmidecode {r_data}"


class BasicCmd:
    prefix = "ipmitool "


class Bmc(BasicCmd):
    bmc_prefix = "bmc "
    info = BasicCmd.prefix + bmc_prefix + "info"
    reset_cold = BasicCmd.prefix + bmc_prefix + "reset cold"


class Chassis(BasicCmd):
    chassis_prefix = "chassis "
    power_status = BasicCmd.prefix + chassis_prefix + "power status"
    power_on = BasicCmd.prefix + chassis_prefix + "power on"
    power_off = BasicCmd.prefix + chassis_prefix + "power off"
    power_cycle = BasicCmd.prefix + chassis_prefix + "power cycle"
    power_reset = BasicCmd.prefix + chassis_prefix + "power reset"
    power_diag = BasicCmd.prefix + chassis_prefix + "power diag"
    power_soft = BasicCmd.prefix + chassis_prefix + "power soft"
    policy_always_on = BasicCmd.prefix + chassis_prefix + "policy always-on"
    policy_previous = BasicCmd.prefix + chassis_prefix + "policy previous"
    status = BasicCmd.prefix + chassis_prefix + "power status"


class Fru(BasicCmd):
    fru_prefix = "fru "
    list = BasicCmd.prefix + fru_prefix + "list"
    _print = BasicCmd.prefix + fru_prefix + "print {c}"
    write = BasicCmd.prefix + fru_prefix + "write {fru_id} {fru_file}"
    read = BasicCmd.prefix + fru_prefix + "read {fru_id} {fru_file}"
    edit = BasicCmd.prefix + fru_prefix + "edit {fru_id} field {section} {index} {string}"


class Sdr(BasicCmd):
    sdr_prefix = "sdr "
    list = BasicCmd.prefix + sdr_prefix + "list"
    elist = BasicCmd.prefix + sdr_prefix + "elist"


class Sensor(BasicCmd):
    sensor_prefix = "sensor "
    list = BasicCmd.prefix + sensor_prefix + "list"


class Sel(BasicCmd):
    sel_prefix = "sel "
    list = BasicCmd.prefix + sel_prefix + "list"
    elist = BasicCmd.prefix + sel_prefix + "elist"
    clear = BasicCmd.prefix + sel_prefix + "clear"
    info = BasicCmd.prefix + sel_prefix + "info"


class Lan(BasicCmd):
    lan_prefix = "lan "
    set_ipsrc = BasicCmd.prefix + lan_prefix + "set {c} ipsrc {p}"
    lan_print = BasicCmd.prefix + lan_prefix + "print {c}"
    set_macaddr = BasicCmd.prefix + lan_prefix + "set {c} macaddr {p}"


class User(BasicCmd):
    user_prefix = "user "
    set_name = BasicCmd.prefix + user_prefix + "set name {u} {n}"
    set_password = BasicCmd.prefix + user_prefix + "set password {u} {p}"


class Sol(BasicCmd):
    sol_prefix = "sol "
    info = BasicCmd.prefix + sol_prefix + "info {c}"
    set = BasicCmd.prefix + sol_prefix + "set {c}"
    activate = BasicCmd.prefix + sol_prefix + "activate"
    deactivate = BasicCmd.prefix + sol_prefix + "deactivate"


class PEF(BasicCmd):
    pef_prefix = "pef "
    policy_list = BasicCmd.prefix + pef_prefix + "policy list"


class Raw(BasicCmd):
    raw_prefix = "raw "


class AliOEM(BasicCmd):
    alioem_prefix = "alioem "

    getdevicestatus = BasicCmd.prefix + alioem_prefix + "getdevicestatus"
    getdeviceinformation = BasicCmd.prefix + alioem_prefix + "getdeviceinformation"
    sel = BasicCmd.prefix + alioem_prefix + "sel"
    getloginfo = BasicCmd.prefix + alioem_prefix + "getloginfo"
    version = BasicCmd.prefix + alioem_prefix + "version"
    onekey = BasicCmd.prefix + alioem_prefix + "onekey"
    getbiosconf = BasicCmd.prefix + alioem_prefix + "getbiosconf"
    getsmbiosinformation = BasicCmd.prefix + alioem_prefix + "getsmbiosinformation"


class Netfn_0x00_Chassis(Raw):
    netfn_prefix = "0x00 "

    _0x02 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x02 {r_data}"


class Netfn_0x06_App(Raw):
    netfn_prefix = "0x06 "
    _0x02 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x02"
    _0x22 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x22"
    _0x24 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x24 {r_data}"
    masterWriteRead = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x52 {r_data}"


class Netfn_0x0c_Transport(Raw):
    netfn_prefix = "0x0c "
    set_sol_configuration_parameters = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x21 {r_data}"


class Netfn_0x0a_Storage(Raw):
    netfn_prefix = "0x0a "
    _0x23 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x23 {r_data}"


class Netfn_0x04_SensorEvent(Raw):
    netfn_prefix = "0x04 "
    _0x13 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x13 {r_data}"
    _0x2d = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x2d {r_data}"
    _0x27 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x27 {r_data}"
    _0x26 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x26 {r_data}"


class Netfn_0x3E(Raw):
    netfn_prefix = "0x3e "

    _0x31 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x31 {r_data}"
    _0x01 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x01 {r_data}"
    _0x07 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x07 {r_data}"
    _0x08 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x08 {r_data}"
    _0x5a = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x5a {r_data}"
    _0x5b = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x5b"
    _0x5c = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x5c {r_data}"
    _0x5d = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x5d {r_data}"
    _0x5f = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x5f {r_data}"
    _0x5e = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x5e {r_data}"
    _0x14 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x14 {r_data}"
    _0x15 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x15 {r_data}"
    _0x06 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x06 {r_data}"
    _0x03 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x03"
    _0x40 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x40 {r_data}"
    _0x09 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x09 {r_data}"
    _0x05 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x05 {r_data}"
    _0x41 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x41 {r_data}"
    _0x20 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x20 {r_data}"
    _0x21 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x21 {r_data}"
    _0x22 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x22 {r_data}"
    _0x23 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x23 {r_data}"
    _0x61 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x61 {r_data}"
    _0x3f = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x3f {r_data}"
    _0x0e = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x0e {r_data}"
    _0x1f = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x1f {r_data}"
    _0x12 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x12 {r_data}"
    _0x13 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x13 {r_data}"
    _0x19 = Raw.prefix + Raw.raw_prefix + netfn_prefix + "0x19 {r_data}"


get_sensor_value = Netfn_0x3E._0x31
set_device_status = Netfn_0x3E._0x01
get_version_info = Netfn_0x3E._0x07
set_version_info = Netfn_0x3E._0x08
set_security_status = Netfn_0x3E._0x5a
get_security_status = Netfn_0x3E._0x5b
write_bios_configuration = Netfn_0x3E._0x5c
read_bios_configuration = Netfn_0x3E._0x5d
get_bios_configuration_value = Netfn_0x3E._0x5f
set_bios_configuration_value = Netfn_0x3E._0x5e
get_bios_debug_level = Netfn_0x3E._0x14
set_bios_debug_level = Netfn_0x3E._0x15
get_log_info = Netfn_0x3E._0x06
get_device_status = Netfn_0x3E._0x03
get_device_information = Netfn_0x3E._0x40
set_debug_info_collection = Netfn_0x3E._0x09
get_log_entry = Netfn_0x3E._0x05
get_bios_boot_stage = Netfn_0x3E._0x41
set_bios_boot_stage = Netfn_0x3E._0x19
get_management_information = Netfn_0x3E._0x20
set_fan_mode = Netfn_0x3E._0x21
get_fan_mode = Netfn_0x3E._0x22
set_fan_PWM = Netfn_0x3E._0x23
get_bios_80_port_info = Netfn_0x3E._0x61
restore_to_manufacture = Netfn_0x3E._0x3f
set_remote_syslog_configuration = Netfn_0x3E._0x0e
get_remote_syslog_configuration = Netfn_0x3E._0x1f
get_smbios_information = Netfn_0x3E._0x12
set_smbios_information = Netfn_0x3E._0x13

# raw netfn cmd
# chassis
chassis_control = Netfn_0x00_Chassis._0x02

# application
cold_reset = Netfn_0x06_App._0x02
reset_watchdog_timer = Netfn_0x06_App._0x22
set_watchdog_timer = Netfn_0x06_App._0x24

# sensor event
get_pef_configuration_parameters = Netfn_0x04_SensorEvent._0x13
get_sensor_reading = Netfn_0x04_SensorEvent._0x2d
get_sensor_threshold = Netfn_0x04_SensorEvent._0x27
set_sensor_threshold = Netfn_0x04_SensorEvent._0x26

#storage
get_sdr = Netfn_0x0a_Storage._0x23


def build_cmd(cmd_prefix, request_data):
    return cmd_prefix.format(r_data=request_data)
