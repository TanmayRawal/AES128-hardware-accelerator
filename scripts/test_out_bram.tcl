connect
targets -set -filter {name =~ "MicroBlaze #0"}
puts "Output BRAM 0xC2000400:"
puts [mrd 0xC2000400]
disconnect
exit
