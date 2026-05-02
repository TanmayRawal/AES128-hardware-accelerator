connect
targets -set -filter {name =~ "MicroBlaze #0"}
mwr 0xC0000000 0xA0A0A0A0
puts [mrd 0xC0000000]
disconnect
exit
