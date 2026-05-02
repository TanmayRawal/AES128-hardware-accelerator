connect
targets -set -filter {name =~ "MicroBlaze #0"}

puts "Dumping Input BRAM..."
mrd -bin -file C:/Users/Tanmay/Downloads/aes128_image_encryption_ipcore_nexys4ddr/aes128_image_encryption_ipcore_nexys4ddr/input_image.raw 0xC0000000 1024

puts "Dumping Output BRAM..."
mrd -bin -file C:/Users/Tanmay/Downloads/aes128_image_encryption_ipcore_nexys4ddr/aes128_image_encryption_ipcore_nexys4ddr/output_image.raw 0xC2000000 1024

disconnect
exit
