/*
 * main.c  --  AES-128 CTR Mode Image Encryption + Decryption
 * MicroBlaze / Vitis application for Nexys 4 DDR
 *
 * Flow (auto-starts on processor reset, no button wait):
 *  1. LED16_R = ON  (encrypting)
 *  2. Encrypt 1024 blocks from Input BRAM -> Output BRAM (CTR mode)
 *  3. LED16_B = ON  (decrypting)
 *  4. Decrypt 1024 blocks from Output BRAM -> Decrypt BRAM (CTR mode)
 *  5. Verify: compare Input BRAM vs Decrypt BRAM word-by-word
 *  6. LED16_G = ON if match, LED16_R blink if mismatch
 *
 * Image: 128 x 128 grayscale = 16,384 bytes = 1024 AES blocks
 * Data is loaded into Input BRAM via JTAG (mwr -bin -file) before reset.
 */

#include <stdint.h>
#include <string.h>
#include "xil_printf.h"
#include "xil_io.h"
#include "xparameters.h"
#include "aes_ip_driver.h"

/* ---- Project constants ---- */
#define IMAGE_BYTES      16384U  /* 128 x 128 grayscale */
#define BLOCK_BYTES      16U
#define NUM_BLOCKS       (IMAGE_BYTES / BLOCK_BYTES)  /* 1024 */

/* Input/Output/Decrypt BRAM base addresses (from xparameters.h) */
#define INPUT_BRAM_BASE   XPAR_AXI_BRAM_CTRL_0_BASEADDR
#define OUTPUT_BRAM_BASE  XPAR_AXI_BRAM_CTRL_1_BASEADDR
#define DECRYPT_BRAM_BASE XPAR_AXI_BRAM_CTRL_2_BASEADDR

/* GPIO base address */
#define GPIO_BASEADDR     XPAR_AXI_GPIO_0_BASEADDR
#define GPIO_DATA_OUT     (GPIO_BASEADDR + 0x00U)   /* LED outputs */
#define GPIO_TRI_OUT      (GPIO_BASEADDR + 0x04U)   /* direction: 0=output */
#define GPIO2_DATA_IN     (GPIO_BASEADDR + 0x08U)   /* button inputs */
#define GPIO2_TRI_IN      (GPIO_BASEADDR + 0x0CU)   /* direction: 1=input  */

/* GPIO output bit assignments (3-bit output: LED[0], LED16_R, LED16_G) */
#define LED0_BIT     (1U << 0)
#define LED16_R_BIT  (1U << 1)
#define LED16_G_BIT  (1U << 2)

/* ---- AES-128 demo key: 00 01 02 ... 0F ---- */
static const uint8_t AES_KEY[16] = {
    0x00,0x01,0x02,0x03, 0x04,0x05,0x06,0x07,
    0x08,0x09,0x0A,0x0B, 0x0C,0x0D,0x0E,0x0F
};

/* ---- Initial counter (big-endian, MSB at [0]) ---- */
static const uint8_t INIT_CTR[16] = {
    0xF0,0xE0,0xD0,0xC0, 0xB0,0xA0,0x90,0x80,
    0x70,0x60,0x50,0x40, 0x30,0x20,0x10,0x00
};

/* ---- Increment counter (big-endian: byte 15 is LSB) ---- */
static void counter_increment(uint8_t c[16]) {
    int i;
    for (i = 15; i >= 0; --i) {
        c[i]++;
        if (c[i] != 0) break;
    }
}

/* ---- GPIO helpers ---- */
static void gpio_init(void) {
    Xil_Out32(GPIO_TRI_OUT,  0x00U); /* all 3 bits output */
    Xil_Out32(GPIO2_TRI_IN,  0x03U); /* both button bits input */
    Xil_Out32(GPIO_DATA_OUT, 0x00U); /* all LEDs off */
}

static void led_set(uint32_t bits) {
    Xil_Out32(GPIO_DATA_OUT, bits);
}

/* ---- Read 16 bytes from BRAM at byte offset ---- */
static void bram_read_block(uint32_t base, uint32_t byte_offset, uint8_t out[16]) {
    uint32_t i, w;
    for (i = 0; i < 4; i++) {
        w = Xil_In32(base + byte_offset + i * 4);
        out[i*4+0] = (w >> 24) & 0xFF;
        out[i*4+1] = (w >> 16) & 0xFF;
        out[i*4+2] = (w >>  8) & 0xFF;
        out[i*4+3] =  w        & 0xFF;
    }
}

/* ---- Write 16 bytes to BRAM at byte offset ---- */
static void bram_write_block(uint32_t base, uint32_t byte_offset, const uint8_t in[16]) {
    uint32_t i, w;
    for (i = 0; i < 4; i++) {
        w = ((uint32_t)in[i*4+0] << 24) | ((uint32_t)in[i*4+1] << 16) |
            ((uint32_t)in[i*4+2] <<  8) |  (uint32_t)in[i*4+3];
        Xil_Out32(base + byte_offset + i * 4, w);
    }
}

/* ---- CTR encrypt/decrypt a full image between two BRAMs ---- */
static void ctr_process(uint32_t src_base, uint32_t dst_base) {
    uint8_t ctr_copy[16];
    uint8_t block_in[16], keystream[16], block_out[16];
    uint32_t blk_idx, i;

    memcpy(ctr_copy, INIT_CTR, 16);

    for (blk_idx = 0; blk_idx < NUM_BLOCKS; blk_idx++) {
        uint32_t byte_off = blk_idx * BLOCK_BYTES;

        /* Read source block */
        bram_read_block(src_base, byte_off, block_in);

        /* Encrypt counter block using AES IP */
        AES_WriteDataIn(ctr_copy);
        AES_Start();
        AES_WaitDone();
        AES_ReadDataOut(keystream);

        /* XOR keystream with source -> destination */
        for (i = 0; i < 16; i++) block_out[i] = block_in[i] ^ keystream[i];

        /* Write to destination BRAM */
        bram_write_block(dst_base, byte_off, block_out);

        /* Increment counter */
        counter_increment(ctr_copy);
    }
}

/* ===================================================================== */
int main(void)
{
    uint32_t i, mismatch_count;

    gpio_init();

    xil_printf("\r\n");
    xil_printf("==============================================\r\n");
    xil_printf(" AES-128 CTR Encrypt+Decrypt  -  Nexys 4 DDR\r\n");
    xil_printf(" Image : 128x128 (16384 bytes, 1024 blocks)\r\n");
    xil_printf(" Key   : 000102030405060708090A0B0C0D0E0F\r\n");
    xil_printf(" CTR0  : F0E0D0C0B0A090807060504030201000\r\n");
    xil_printf("==============================================\r\n");

    /* ---- Phase 1: ENCRYPT (Input BRAM -> Output BRAM) ---- */
    xil_printf("Phase 1: Encrypting...\r\n");
    led_set(LED16_R_BIT);  /* Red = encrypting */

    /* Write AES key */
    AES_WriteKey(AES_KEY);

    /* CTR encrypt */
    ctr_process(INPUT_BRAM_BASE, OUTPUT_BRAM_BASE);

    xil_printf("Encryption complete. 1024 blocks processed.\r\n");

    /* ---- Phase 2: DECRYPT (Output BRAM -> Decrypt BRAM) ---- */
    xil_printf("Phase 2: Decrypting...\r\n");
    led_set(LED16_R_BIT | LED16_G_BIT);  /* Yellow = decrypting */

    /* CTR decrypt (same operation, same key, same initial counter) */
    ctr_process(OUTPUT_BRAM_BASE, DECRYPT_BRAM_BASE);

    xil_printf("Decryption complete. 1024 blocks processed.\r\n");

    /* ---- Phase 3: VERIFY (Input BRAM vs Decrypt BRAM) ---- */
    xil_printf("Phase 3: Verifying roundtrip...\r\n");
    mismatch_count = 0;

    for (i = 0; i < IMAGE_BYTES; i += 4) {
        uint32_t original  = Xil_In32(INPUT_BRAM_BASE + i);
        uint32_t recovered = Xil_In32(DECRYPT_BRAM_BASE + i);
        if (original != recovered) {
            mismatch_count++;
            if (mismatch_count <= 4) {
                xil_printf("MISMATCH at offset 0x%04lX: orig=0x%08lX recv=0x%08lX\r\n",
                           (unsigned long)i, (unsigned long)original, (unsigned long)recovered);
            }
        }
    }

    if (mismatch_count == 0) {
        led_set(LED16_G_BIT);  /* Green = verified */
        xil_printf("VERIFY: PASS - Roundtrip byte-perfect match!\r\n");
    } else {
        /* Blink red for error */
        xil_printf("VERIFY: FAIL - %lu word mismatches detected!\r\n",
                   (unsigned long)mismatch_count);
        while (1) {
            led_set(LED16_R_BIT);
            for (volatile int d = 0; d < 500000; d++) {}
            led_set(0);
            for (volatile int d = 0; d < 500000; d++) {}
        }
    }

    xil_printf("==============================================\r\n");
    xil_printf("DONE\r\n");

    while (1) { /* hang */ }
    return 0;
}
