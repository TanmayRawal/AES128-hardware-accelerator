/*
 * aes_ip_driver.h  –  AXI-Lite Driver for AES-128 IP Core
 * Use with Vitis / MicroBlaze. Include xil_io.h (from BSP).
 *
 * AES IP Register Map (offsets from BASEADDR):
 *   0x00 CTRL    [W]  bit0=START, bit1=SOFT_RST
 *   0x04 STATUS  [R]  bit0=DONE
 *   0x08 KEY_W0  [W]  key[127:96]
 *   0x0C KEY_W1  [W]  key[95:64]
 *   0x10 KEY_W2  [W]  key[63:32]
 *   0x14 KEY_W3  [W]  key[31:0]
 *   0x18 DIN_W0  [W]  data_in[127:96]
 *   0x1C DIN_W1  [W]  data_in[95:64]
 *   0x20 DIN_W2  [W]  data_in[63:32]
 *   0x24 DIN_W3  [W]  data_in[31:0]
 *   0x28 DOUT_W0 [R]  data_out[127:96]
 *   0x2C DOUT_W1 [R]  data_out[95:64]
 *   0x30 DOUT_W2 [R]  data_out[63:32]
 *   0x34 DOUT_W3 [R]  data_out[31:0]
 */
#ifndef AES_IP_DRIVER_H
#define AES_IP_DRIVER_H

#include <stdint.h>
#include "xil_io.h"
#include "xparameters.h"

/* Base address — defined in xparameters.h after hardware export */
#define AES_IP_BASEADDR   XPAR_AES128_AXILITE_0_BASEADDR

/* Register offsets */
#define AES_REG_CTRL      0x00U
#define AES_REG_STATUS    0x04U
#define AES_REG_KEY_W0    0x08U
#define AES_REG_KEY_W1    0x0CU
#define AES_REG_KEY_W2    0x10U
#define AES_REG_KEY_W3    0x14U
#define AES_REG_DIN_W0    0x18U
#define AES_REG_DIN_W1    0x1CU
#define AES_REG_DIN_W2    0x20U
#define AES_REG_DIN_W3    0x24U
#define AES_REG_DOUT_W0   0x28U
#define AES_REG_DOUT_W1   0x2CU
#define AES_REG_DOUT_W2   0x30U
#define AES_REG_DOUT_W3   0x34U

#define AES_CTRL_START    (1U << 0)
#define AES_STATUS_DONE   (1U << 0)

/* Low-level R/W helpers */
#define AES_WRITE(offset, val)  Xil_Out32(AES_IP_BASEADDR + (offset), (val))
#define AES_READ(offset)        Xil_In32 (AES_IP_BASEADDR + (offset))

/* -------------------------------------------------------------------------
 * AES_WriteKey  –  Write 128-bit key (MSB first, big-endian byte order)
 * key[0] = MSB byte, key[15] = LSB byte
 * ------------------------------------------------------------------------- */
static inline void AES_WriteKey(const uint8_t key[16]) {
    AES_WRITE(AES_REG_KEY_W0, ((uint32_t)key[0]  << 24) | ((uint32_t)key[1]  << 16) |
                               ((uint32_t)key[2]  <<  8) |  (uint32_t)key[3]);
    AES_WRITE(AES_REG_KEY_W1, ((uint32_t)key[4]  << 24) | ((uint32_t)key[5]  << 16) |
                               ((uint32_t)key[6]  <<  8) |  (uint32_t)key[7]);
    AES_WRITE(AES_REG_KEY_W2, ((uint32_t)key[8]  << 24) | ((uint32_t)key[9]  << 16) |
                               ((uint32_t)key[10] <<  8) |  (uint32_t)key[11]);
    AES_WRITE(AES_REG_KEY_W3, ((uint32_t)key[12] << 24) | ((uint32_t)key[13] << 16) |
                               ((uint32_t)key[14] <<  8) |  (uint32_t)key[15]);
}

/* -------------------------------------------------------------------------
 * AES_WriteDataIn  –  Write 128-bit input block (big-endian)
 * ------------------------------------------------------------------------- */
static inline void AES_WriteDataIn(const uint8_t blk[16]) {
    AES_WRITE(AES_REG_DIN_W0, ((uint32_t)blk[0]  << 24) | ((uint32_t)blk[1]  << 16) |
                               ((uint32_t)blk[2]  <<  8) |  (uint32_t)blk[3]);
    AES_WRITE(AES_REG_DIN_W1, ((uint32_t)blk[4]  << 24) | ((uint32_t)blk[5]  << 16) |
                               ((uint32_t)blk[6]  <<  8) |  (uint32_t)blk[7]);
    AES_WRITE(AES_REG_DIN_W2, ((uint32_t)blk[8]  << 24) | ((uint32_t)blk[9]  << 16) |
                               ((uint32_t)blk[10] <<  8) |  (uint32_t)blk[11]);
    AES_WRITE(AES_REG_DIN_W3, ((uint32_t)blk[12] << 24) | ((uint32_t)blk[13] << 16) |
                               ((uint32_t)blk[14] <<  8) |  (uint32_t)blk[15]);
}

/* -------------------------------------------------------------------------
 * AES_Start  –  Pulse the START bit
 * ------------------------------------------------------------------------- */
static inline void AES_Start(void) {
    AES_WRITE(AES_REG_CTRL, AES_CTRL_START);
}

/* -------------------------------------------------------------------------
 * AES_WaitDone  –  Poll STATUS until DONE=1 (blocking)
 * ------------------------------------------------------------------------- */
static inline void AES_WaitDone(void) {
    while (!(AES_READ(AES_REG_STATUS) & AES_STATUS_DONE)) { /* poll */ }
}

/* -------------------------------------------------------------------------
 * AES_ReadDataOut  –  Read 128-bit output block (big-endian)
 * ------------------------------------------------------------------------- */
static inline void AES_ReadDataOut(uint8_t out[16]) {
    uint32_t w0 = AES_READ(AES_REG_DOUT_W0);
    uint32_t w1 = AES_READ(AES_REG_DOUT_W1);
    uint32_t w2 = AES_READ(AES_REG_DOUT_W2);
    uint32_t w3 = AES_READ(AES_REG_DOUT_W3);
    out[0]  = (w0 >> 24) & 0xFF; out[1]  = (w0 >> 16) & 0xFF;
    out[2]  = (w0 >>  8) & 0xFF; out[3]  =  w0        & 0xFF;
    out[4]  = (w1 >> 24) & 0xFF; out[5]  = (w1 >> 16) & 0xFF;
    out[6]  = (w1 >>  8) & 0xFF; out[7]  =  w1        & 0xFF;
    out[8]  = (w2 >> 24) & 0xFF; out[9]  = (w2 >> 16) & 0xFF;
    out[10] = (w2 >>  8) & 0xFF; out[11] =  w2        & 0xFF;
    out[12] = (w3 >> 24) & 0xFF; out[13] = (w3 >> 16) & 0xFF;
    out[14] = (w3 >>  8) & 0xFF; out[15] =  w3        & 0xFF;
}

/* -------------------------------------------------------------------------
 * AES_EncryptBlock  –  One-shot: write, start, wait, read
 * ------------------------------------------------------------------------- */
static inline void AES_EncryptBlock(const uint8_t in[16], uint8_t out[16]) {
    AES_WriteDataIn(in);
    AES_Start();
    AES_WaitDone();
    AES_ReadDataOut(out);
}

#endif /* AES_IP_DRIVER_H */
