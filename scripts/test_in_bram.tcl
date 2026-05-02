connect
targets -set -filter {name =~ "MicroBlaze #0"}
puts [mrd 0xC0000400]
disconnect
exit
