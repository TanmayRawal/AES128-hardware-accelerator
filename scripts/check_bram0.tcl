connect
targets -set -filter {name =~ "MicroBlaze #0"}
puts "Output BRAM Block 0:"
puts [mrd 0xC2000000 4]
disconnect
exit
