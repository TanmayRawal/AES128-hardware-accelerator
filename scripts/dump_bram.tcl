# dump_bram.tcl — Read encrypted data from Output BRAM via JTAG
# Run with: C:\Xilinx\Vitis\2024.2\bin\xsct.bat dump_bram.tcl

connect
after 500

# Target the MicroBlaze
targets -set -filter {name =~ "MicroBlaze #0"}
after 200

puts "\n========================================"
puts "  AES-128 CTR Encrypted Output (BRAM)"
puts "========================================"

# Output BRAM base address
set base 0xC2000000

# Read first 16 blocks (256 bytes) = blocks 0-15
for {set blk 0} {$blk < 16} {incr blk} {
    set offset [expr {$blk * 16}]
    set addr [expr {$base + $offset}]

    # Read 4 words (16 bytes)
    set w0 [mrd -force $addr]
    set w1 [mrd -force [expr {$addr + 4}]]
    set w2 [mrd -force [expr {$addr + 8}]]
    set w3 [mrd -force [expr {$addr + 12}]]

    # Format output
    puts [format "BLOCK %03d: %s %s %s %s" $blk $w0 $w1 $w2 $w3]
}

puts "\n... (showing first 16 of 256 blocks)"
puts "========================================"
puts "DONE"

disconnect
exit
