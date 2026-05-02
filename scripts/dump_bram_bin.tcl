connect
targets -set -filter {name =~ "MicroBlaze #0"}
puts "Dumping 4096 bytes from Output BRAM (0xC2000000)..."
mrd -bin -file encrypted_image.raw 0xC2000000 1024
puts "Dump complete: encrypted_image.raw"
disconnect
exit
