connect
targets -set -filter {name =~ "MicroBlaze #0"}
puts "Uploading gradient image to Input BRAM..."
mwr -bin -file C:/Users/Tanmay/Downloads/aes128_image_encryption_ipcore_nexys4ddr/aes128_image_encryption_ipcore_nexys4ddr/gradient.raw 0xC0000000 1024
puts "Upload complete."
disconnect
exit
