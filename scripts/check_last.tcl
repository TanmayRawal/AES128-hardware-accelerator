connect
targets -set -filter {name =~ "MicroBlaze #0"}
puts "Block 255 (0xC2000FF0):"
puts [mrd 0xC2000FF0 4]
disconnect
exit
