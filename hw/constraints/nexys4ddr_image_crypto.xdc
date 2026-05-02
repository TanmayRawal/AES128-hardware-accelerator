# Nexys 4 DDR Constraints — AES-128 CTR Image Encryption
# Target: xc7a100tcsg324-1  |  Vivado 2024.2
#
# NOTE: sys_clock and reset ports are auto-constrained by
#       apply_bd_automation (board interface). Do NOT re-constrain them here.

set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]

# UART — USB-UART bridge on Nexys 4 DDR (FT2232HQ Channel B)
#   C4 = FPGA transmits to PC  (RsTx in Digilent master XDC)
#   D4 = FPGA receives from PC (RsRx in Digilent master XDC)
set_property PACKAGE_PIN C4  [get_ports UART_txd]
set_property IOSTANDARD LVCMOS33 [get_ports UART_txd]

set_property PACKAGE_PIN D4  [get_ports UART_rxd]
set_property IOSTANDARD LVCMOS33 [get_ports UART_rxd]

# GPIO LEDs (3-bit output from AXI GPIO channel 1)
#   GPIO_LEDS[0] → LED0   (H17)
#   GPIO_LEDS[1] → LED16_R (N15, RGB LED red)
#   GPIO_LEDS[2] → LED16_G (R11, RGB LED green)
set_property PACKAGE_PIN H17 [get_ports {GPIO_LEDS[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {GPIO_LEDS[0]}]
set_property PACKAGE_PIN N15 [get_ports {GPIO_LEDS[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {GPIO_LEDS[1]}]
set_property PACKAGE_PIN R11 [get_ports {GPIO_LEDS[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {GPIO_LEDS[2]}]

# GPIO Buttons (2-bit input from AXI GPIO channel 2)
#   GPIO_BTNS[0] → BTNC (N17, center button)
#   GPIO_BTNS[1] → BTND (P18, down button)
set_property PACKAGE_PIN N17 [get_ports {GPIO_BTNS[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {GPIO_BTNS[0]}]
set_property PACKAGE_PIN P18 [get_ports {GPIO_BTNS[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {GPIO_BTNS[1]}]
