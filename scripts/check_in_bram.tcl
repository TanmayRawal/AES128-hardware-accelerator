connect
targets -set -filter {name =~ "MicroBlaze #0"}
puts "Input BRAM (0xC0000000):"
puts [mrd 0xC0000000 4]
disconnect
exit
