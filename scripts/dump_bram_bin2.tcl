connect
targets -set -filter {name =~ "MicroBlaze #0"}
mrd -bin -file C:/Users/Tanmay/Downloads/aes128_image_encryption_ipcore_nexys4ddr/aes128_image_encryption_ipcore_nexys4ddr/encrypted_image.raw 0xC2000000 1024
disconnect
exit
