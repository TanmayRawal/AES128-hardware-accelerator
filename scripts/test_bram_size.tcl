connect
targets -set -filter {name =~ "MicroBlaze #0"}
puts "0xC2000000:"
puts [mrd -value 0xC2000000]
puts "0xC2000400:"
puts [mrd -value 0xC2000400]
mwr 0xC2000400 0xDEADBEEF
puts "After write 0xC2000400:"
puts [mrd -value 0xC2000400]
mwr 0xC2000000 0xBEEFCAFE
puts "After write 0xC2000000:"
puts [mrd -value 0xC2000000]
puts "0xC2000400 again:"
puts [mrd -value 0xC2000400]
disconnect
exit
