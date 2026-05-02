# =============================================================================
# create_project.tcl  –  Full Vivado 2024.2 Project + Block Design Automation
# AES-128 Image Encryption IP Core on Nexys 4 DDR (xc7a100tcsg324-1)
#
# USAGE (in Vivado TCL Console):
#   cd {C:/Users/Tanmay/Downloads/aes128_image_encryption_ipcore_nexys4ddr/aes128_image_encryption_ipcore_nexys4ddr}
#   source hw/vivado/create_project.tcl
# =============================================================================

set script_dir [file normalize [file dirname [info script]]]
set proj_root  [file normalize "$script_dir/../.."]

puts "=== AES-128 IP Core Project Builder ==="
puts "Project root: $proj_root"

# ---------------------------------------------------------------------------
# STEP 1: Package our custom AES-128 AXI-Lite IP
# ---------------------------------------------------------------------------
puts "\n--- Step 1: Packaging AES-128 AXI-Lite IP ---"

set ip_src_dir  "$proj_root/hw/ip/aes128_axilite"
set ip_hdl_dir  "$ip_src_dir/hdl"
set pack_proj   "C:/aes128_ip_pack_tmp"

# Remove any leftover tmp project
if {[file exists $pack_proj]} {
    file delete -force $pack_proj
}

create_project -force ip_pack_tmp $pack_proj -part xc7a100tcsg324-1
set_property target_language Verilog [current_project]

add_files -norecurse [glob $ip_hdl_dir/*.v]
set_property top aes128_axilite_wrapper [current_fileset]
update_compile_order -fileset sources_1

# Package the IP into hw/ip/aes128_axilite/
ipx::package_project \
    -root_dir       $ip_src_dir \
    -vendor         "user.org" \
    -library        "user" \
    -taxonomy       "/UserIP" \
    -set_current    false \
    -force

# Open packaged core and finalize
set ip_core [ipx::open_core "$ip_src_dir/component.xml"]

set_property name             {aes128_axilite}    $ip_core
set_property display_name     {AES-128 AXI-Lite}  $ip_core
set_property description      {AES-128 ECB Encryption Engine with AXI4-Lite Slave Interface} $ip_core
set_property vendor_display_name {User}           $ip_core
set_property version          {1.0}               $ip_core
set_property core_revision    {1}                 $ip_core

# Infer AXI interface from port names
ipx::infer_bus_interfaces xilinx.com:interface:aximm_rtl:1.0 $ip_core

ipx::create_xgui_files    $ip_core
ipx::update_checksums     $ip_core
ipx::check_integrity      $ip_core
ipx::save_core            $ip_core
ipx::unload_core          $ip_core

close_project
file delete -force $pack_proj

puts "AES-128 IP packaged successfully."

# ---------------------------------------------------------------------------
# STEP 2: Create main Vivado project
# ---------------------------------------------------------------------------
puts "\n--- Step 2: Creating Main Vivado Project ---"

set proj_name "aes128_image_ipcore"
set proj_dir  "C:/aes128_vivado_proj"

if {[file exists $proj_dir]} {
    file delete -force $proj_dir
}

create_project $proj_name $proj_dir -part xc7a100tcsg324-1
set_property target_language  Verilog [current_project]
set_property board_part       digilentinc.com:nexys4_ddr:part0:1.1 [current_project]

# Register custom IP repository
set_property ip_repo_paths [list "$proj_root/hw/ip"] [current_project]
update_ip_catalog -rebuild

# Add constraints
add_files -fileset constrs_1 -norecurse "$proj_root/hw/constraints/nexys4ddr_image_crypto.xdc"

puts "Project created and IP catalog updated."

# ---------------------------------------------------------------------------
# STEP 3: Create Block Design
# ---------------------------------------------------------------------------
puts "\n--- Step 3: Building Block Design ---"

create_bd_design "image_crypto_bd"
update_compile_order -fileset sources_1

# ---- 3a. Clocking Wizard ----
create_bd_cell -type ip -vlnv xilinx.com:ip:clk_wiz:* clk_wiz_0
set_property -dict [list \
    CONFIG.PRIMITIVE            {MMCM} \
    CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {22} \
    CONFIG.USE_LOCKED           {true} \
    CONFIG.USE_RESET            {true} \
    CONFIG.RESET_TYPE           {ACTIVE_HIGH} \
] [get_bd_cells clk_wiz_0]

# Use board automation for clock and reset inputs
apply_bd_automation -rule xilinx.com:bd_rule:board -config { Board_Interface {sys_clock} }  [get_bd_pins clk_wiz_0/clk_in1]
apply_bd_automation -rule xilinx.com:bd_rule:board -config { Board_Interface {reset} }  [get_bd_pins clk_wiz_0/reset]

# ---- 3b. MicroBlaze ----
create_bd_cell -type ip -vlnv xilinx.com:ip:microblaze:* microblaze_0
set_property -dict [list \
    CONFIG.C_DEBUG_ENABLED      {1} \
    CONFIG.C_D_AXI              {1} \
    CONFIG.C_D_LMB              {1} \
    CONFIG.C_I_LMB              {1} \
    CONFIG.C_USE_BARREL         {1} \
    CONFIG.C_USE_HW_MUL         {1} \
    CONFIG.C_AREA_OPTIMIZED     {1} \
] [get_bd_cells microblaze_0]

# Apply MicroBlaze automation (adds local memory, MDM)
apply_bd_automation -rule xilinx.com:bd_rule:microblaze \
    -config { \
        axi_intc       {0} \
        axi_periph     {Enabled} \
        axi_timebase   {Timer} \
        debug_module   {Debug Only} \
        local_mem      {32KB} \
        ecc            {None} \
        cache          {None} \
        uart           {None} \
    } [get_bd_cells microblaze_0]

# Vivado 2024.2's microblaze block automation already wired the clock and reset automatically!
# No manual connections needed here.

# ---- 3d. AXI UART Lite (115200 baud) ----
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_uartlite:* axi_uartlite_0
set_property -dict [list \
    CONFIG.C_BAUDRATE   {115200} \
    CONFIG.C_DATA_BITS  {8} \
    CONFIG.C_USE_PARITY {0} \
] [get_bd_cells axi_uartlite_0]

apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
    -config { Clk_master {/clk_wiz_0/clk_out1} Clk_slave {/clk_wiz_0/clk_out1} \
              Clk_xbar {/clk_wiz_0/clk_out1} Master {/microblaze_0 (Periph)} \
              Slave {/axi_uartlite_0/S_AXI} intc_ip {Auto} \
              master_apm {0} } \
    [get_bd_intf_pins axi_uartlite_0/S_AXI]

make_bd_intf_pins_external [get_bd_intf_pins axi_uartlite_0/UART]
set_property name UART [get_bd_intf_ports UART_0]

# ---- 3e. AXI GPIO (buttons input + LEDs output) ----
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:* axi_gpio_0
set_property -dict [list \
    CONFIG.C_GPIO_WIDTH     {3} \
    CONFIG.C_GPIO2_WIDTH    {2} \
    CONFIG.C_IS_DUAL        {1} \
    CONFIG.C_ALL_OUTPUTS    {1} \
    CONFIG.C_ALL_OUTPUTS_2  {0} \
    CONFIG.C_ALL_INPUTS_2   {1} \
] [get_bd_cells axi_gpio_0]
# GPIO  (output): 3 bits → LED[0], LED16_R, LED16_G
# GPIO2 (input) : 2 bits → BTNC, BTND

apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
    -config { Clk_master {/clk_wiz_0/clk_out1} Clk_slave {/clk_wiz_0/clk_out1} \
              Clk_xbar {/clk_wiz_0/clk_out1} Master {/microblaze_0 (Periph)} \
              Slave {/axi_gpio_0/S_AXI} intc_ip {Auto} \
              master_apm {0} } \
    [get_bd_intf_pins axi_gpio_0/S_AXI]

make_bd_pins_external [get_bd_pins axi_gpio_0/gpio_io_o]
make_bd_pins_external [get_bd_pins axi_gpio_0/gpio2_io_i]
set_property name GPIO_LEDS [get_bd_ports gpio_io_o_0]
set_property name GPIO_BTNS [get_bd_ports gpio2_io_i_0]

# ---- 3f. Input Image BRAM (pre-loaded with .coe) ----
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_bram_ctrl:* axi_bram_ctrl_0
set_property -dict [list \
    CONFIG.SINGLE_PORT_BRAM {1} \
    CONFIG.ECC_TYPE         {0} \
] [get_bd_cells axi_bram_ctrl_0]

apply_bd_automation -rule xilinx.com:bd_rule:bram_cntlr \
    -config {BRAM "New Blk_Mem_Gen"} \
    [get_bd_intf_pins axi_bram_ctrl_0/BRAM_PORTA]

# The automation creates a BRAM named axi_bram_ctrl_0_bram. We add our COE file to it.
set_property -dict [list \
    CONFIG.Load_Init_File {true} \
    CONFIG.Coe_File [file normalize "$proj_root/sample_assets/sample_64x64_gradient.coe"] \
] [get_bd_cells axi_bram_ctrl_0_bram]

apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
    -config { Clk_master {/clk_wiz_0/clk_out1} Clk_slave {/clk_wiz_0/clk_out1} \
              Clk_xbar {/clk_wiz_0/clk_out1} Master {/microblaze_0 (Periph)} \
              Slave {/axi_bram_ctrl_0/S_AXI} intc_ip {Auto} \
              master_apm {0} } \
    [get_bd_intf_pins axi_bram_ctrl_0/S_AXI]

# ---- 3g. Output Image BRAM ----
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_bram_ctrl:* axi_bram_ctrl_1
set_property -dict [list \
    CONFIG.SINGLE_PORT_BRAM {1} \
    CONFIG.ECC_TYPE         {0} \
] [get_bd_cells axi_bram_ctrl_1]

apply_bd_automation -rule xilinx.com:bd_rule:bram_cntlr \
    -config {BRAM "New Blk_Mem_Gen"} \
    [get_bd_intf_pins axi_bram_ctrl_1/BRAM_PORTA]

apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
    -config { Clk_master {/clk_wiz_0/clk_out1} Clk_slave {/clk_wiz_0/clk_out1} \
              Clk_xbar {/clk_wiz_0/clk_out1} Master {/microblaze_0 (Periph)} \
              Slave {/axi_bram_ctrl_1/S_AXI} intc_ip {Auto} \
              master_apm {0} } \
    [get_bd_intf_pins axi_bram_ctrl_1/S_AXI]

# ---- 3h. Custom AES-128 AXI-Lite IP ----
create_bd_cell -type ip -vlnv user.org:user:aes128_axilite:1.0 aes128_axilite_0

apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
    -config { Clk_master {/clk_wiz_0/clk_out1} Clk_slave {/clk_wiz_0/clk_out1} \
              Clk_xbar {/clk_wiz_0/clk_out1} Master {/microblaze_0 (Periph)} \
              Slave {/aes128_axilite_0/S_AXI} intc_ip {Auto} \
              master_apm {0} } \
    [get_bd_intf_pins aes128_axilite_0/S_AXI]

# ---------------------------------------------------------------------------
# STEP 4: Assign Addresses
# ---------------------------------------------------------------------------
puts "\n--- Step 4: Assigning Addresses ---"
assign_bd_address

# Force specific base addresses for easy reference in firmware
set_property offset 0x44A00000 [get_bd_addr_segs {microblaze_0/Data/SEG_aes128_axilite_0_reg0}]
set_property range  4K         [get_bd_addr_segs {microblaze_0/Data/SEG_aes128_axilite_0_reg0}]

set_property offset 0xC0000000 [get_bd_addr_segs {microblaze_0/Data/SEG_axi_bram_ctrl_0_Mem0}]
set_property range  8K         [get_bd_addr_segs {microblaze_0/Data/SEG_axi_bram_ctrl_0_Mem0}]

set_property offset 0xC2000000 [get_bd_addr_segs {microblaze_0/Data/SEG_axi_bram_ctrl_1_Mem0}]
set_property range  8K         [get_bd_addr_segs {microblaze_0/Data/SEG_axi_bram_ctrl_1_Mem0}]

# ---------------------------------------------------------------------------
# STEP 5: Validate, generate outputs, create wrapper
# ---------------------------------------------------------------------------
puts "\n--- Step 5: Validate & Generate ---"

validate_bd_design
save_bd_design

generate_target all [get_files "$proj_dir/${proj_name}.srcs/sources_1/bd/image_crypto_bd/image_crypto_bd.bd"]

make_wrapper -files [get_files "$proj_dir/${proj_name}.srcs/sources_1/bd/image_crypto_bd/image_crypto_bd.bd"] -top
add_files -norecurse "$proj_dir/${proj_name}.gen/sources_1/bd/image_crypto_bd/hdl/image_crypto_bd_wrapper.v"
set_property top image_crypto_bd_wrapper [current_fileset]
update_compile_order -fileset sources_1

puts "\n========================================================="
puts " DONE! Project ready at:"
puts "   $proj_dir/${proj_name}.xpr"
puts ""
puts " NEXT STEPS:"
puts "   1. Run Synthesis  (Flow Navigator)"
puts "   2. Run Implementation"
puts "   3. Generate Bitstream"
puts "   4. File > Export > Export Hardware (include bitstream)"
puts "   5. Open Vitis Unified IDE"
puts "========================================================="
