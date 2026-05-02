/*
 * main.c  –  AES-128 CTR Mode Image Encryption
 * MicroBlaze / Vitis application for Nexys 4 DDR
 *
 * Flow:
 *  1. Wait for BTNC press (GPIO2 input bit 0)
 *  2. LED16_R = ON  (running)
 *  3. Write AES key to AES IP
 *  4. For each of 256 16-byte image blocks:
 *       a. Read 16 bytes from Input BRAM
 *       b. Write counter block to AES IP, start, wait done
 *       c. Read keystream from AES IP
 *       d. XOR keystream with image block → cipher block
 *       e. Write cipher block to Output BRAM
 *       f. Print "BLOCK NNN: <32 hex chars>" via UART
 *       g. Increment counter (big-endian, byte 15 = LSB)
 *  5. LED16_G = ON, LED16_R = OFF
 *  6. Print "DONE" and loop forever
 *
 * UART format (115200 8N1):
 *   BLOCK 000: 3A1B7F...  (32 hex chars = 16 bytes)
 *   ...
 *   BLOCK 255: ...
 *   DONE
 */

#include <stdint.h>
#include <string.h>
#include "xil_printf.h"
#include "xil_io.h"
#include "xparameters.h"
#include "aes_ip_driver.h"

/* ---- Project constants ---- */
#define IMAGE_BYTES      4096U   /* 64 × 64 grayscale */
#define BLOCK_BYTES      16U
#define NUM_BLOCKS       (IMAGE_BYTES / BLOCK_BYTES)  /* 256 */

/* Input/Output BRAM base addresses (from xparameters.h after HW export) */
#define INPUT_BRAM_BASE   XPAR_AXI_BRAM_CTRL_0_BASEADDR
#define OUTPUT_BRAM_BASE  XPAR_AXI_BRAM_CTRL_1_BASEADDR

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

/* GPIO input bit assignments */
#define BTNC_BIT     (1U << 0)
#define BTND_BIT     (1U << 1)

/* ---- AES-128 demo key: 00 01 02 ... 0F ---- */
static const uint8_t AES_KEY[16] = {
    0x00,0x01,0x02,0x03, 0x04,0x05,0x06,0x07,
    0x08,0x09,0x0A,0x0B, 0x0C,0x0D,0x0E,0x0F
};

/* ---- Initial counter (big-endian, MSB at [0]) ---- */
/* matches software_reference_ctr.py default: F0E0D0C0B0A090807060504030201000 */
static uint8_t ctr[16] = {
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

static uint32_t btn_read(void) {
    return Xil_In32(GPIO2_DATA_IN);
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

/* ===================================================================== */
int main(void)
{
    uint32_t blk_idx;
    uint8_t  plain[16], keystream[16], cipher[16];
    uint8_t  ctr_copy[16];
    uint32_t i;

    xil_printf("\r\n");
    xil_printf("==============================================\r\n");
    xil_printf(" AES-128 CTR Image Encryption  –  Nexys 4 DDR\r\n");
    xil_printf(" Key : 000102030405060708090A0B0C0D0E0F\r\n");
    xil_printf(" CTR0: F0E0D0C0B0A090807060504030201000\r\n");
    xil_printf(" Press BTNC (center) to start encryption...\r\n");
    xil_printf("==============================================\r\n");

    gpio_init();
    led_set(LED0_BIT); /* LED0 on = waiting for button */

    /* Wait for BTNC */
    while (!(btn_read() & BTNC_BIT)) { /* spin */ }
    /* Debounce */
    for (volatile int d = 0; d < 500000; d++) {}
    while (btn_read() & BTNC_BIT) {}   /* wait release */

    xil_printf("Starting encryption...\r\n");
    led_set(LED16_R_BIT); /* Red = running */
    /* Vitis rebuild trigger comment */

    /* Write AES key once (key doesn't change per block in CTR) */
    AES_WriteKey(AES_KEY);

    /* Reset counter to initial value */
    memcpy(ctr_copy, ctr, 16);

    /* ---- Process all 256 blocks ---- */
    for (blk_idx = 0; blk_idx < NUM_BLOCKS; blk_idx++) {
        uint32_t byte_off = blk_idx * BLOCK_BYTES;

        /* 1. Read 16 plaintext bytes from Input BRAM */
        bram_read_block(INPUT_BRAM_BASE, byte_off, plain);

        /* 2. Encrypt counter block using AES IP */
        AES_WriteDataIn(ctr_copy);
        AES_Start();
        AES_WaitDone();
        AES_ReadDataOut(keystream);

        /* 3. XOR keystream with plaintext → ciphertext */
        for (i = 0; i < 16; i++) cipher[i] = plain[i] ^ keystream[i];

        /* 4. Write ciphertext to Output BRAM */
        bram_write_block(OUTPUT_BRAM_BASE, byte_off, cipher);

        /* 5. Increment counter */
        counter_increment(ctr_copy);

        /* 6. Print block over UART */
        xil_printf("BLOCK %03lu: ", (unsigned long)blk_idx);
        for (i = 0; i < 16; i++) xil_printf("%02X", cipher[i]);
        xil_printf("\r\n");
    }

    /* Done */
    led_set(LED16_G_BIT); /* Green = done */
    xil_printf("DONE\r\n");
    xil_printf("Encrypted %u bytes (%u blocks) successfully.\r\n",
               (unsigned)IMAGE_BYTES, (unsigned)NUM_BLOCKS);

    while (1) { /* hang */ }
    return 0;
}
