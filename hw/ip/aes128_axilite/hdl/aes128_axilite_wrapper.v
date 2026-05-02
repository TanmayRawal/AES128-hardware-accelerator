// =============================================================================
// aes128_axilite_wrapper.v  –  AXI4-Lite Slave Wrapper for AES-128 Core
// Vivado 2024.2 / Artix-7  –  32-bit AXI-Lite, 14-bit address
// =============================================================================
// Register Map (byte offsets):
//   0x00  CTRL   [W]  bit[0]=START, bit[1]=SOFT_RST
//   0x04  STATUS [R]  bit[0]=DONE (latched until next START)
//   0x08  KEY_W0 [W]  key[127:96]
//   0x0C  KEY_W1 [W]  key[95:64]
//   0x10  KEY_W2 [W]  key[63:32]
//   0x14  KEY_W3 [W]  key[31:0]
//   0x18  DIN_W0 [W]  data_in[127:96]
//   0x1C  DIN_W1 [W]  data_in[95:64]
//   0x20  DIN_W2 [W]  data_in[63:32]
//   0x24  DIN_W3 [W]  data_in[31:0]
//   0x28  DOUT_W0[R]  data_out[127:96]
//   0x2C  DOUT_W1[R]  data_out[95:64]
//   0x30  DOUT_W2[R]  data_out[63:32]
//   0x34  DOUT_W3[R]  data_out[31:0]
// =============================================================================
`timescale 1ns/1ps

module aes128_axilite_wrapper #(
    parameter C_S_AXI_DATA_WIDTH = 32,
    parameter C_S_AXI_ADDR_WIDTH = 6    // 2^6 = 64 bytes covers all regs
)(
    // AXI4-Lite Slave Interface
    input  wire                          S_AXI_ACLK,
    input  wire                          S_AXI_ARESETN,
    // Write address
    input  wire [C_S_AXI_ADDR_WIDTH-1:0] S_AXI_AWADDR,
    input  wire [2:0]                    S_AXI_AWPROT,
    input  wire                          S_AXI_AWVALID,
    output wire                          S_AXI_AWREADY,
    // Write data
    input  wire [C_S_AXI_DATA_WIDTH-1:0] S_AXI_WDATA,
    input  wire [C_S_AXI_DATA_WIDTH/8-1:0] S_AXI_WSTRB,
    input  wire                          S_AXI_WVALID,
    output wire                          S_AXI_WREADY,
    // Write response
    output wire [1:0]                    S_AXI_BRESP,
    output wire                          S_AXI_BVALID,
    input  wire                          S_AXI_BREADY,
    // Read address
    input  wire [C_S_AXI_ADDR_WIDTH-1:0] S_AXI_ARADDR,
    input  wire [2:0]                    S_AXI_ARPROT,
    input  wire                          S_AXI_ARVALID,
    output wire                          S_AXI_ARREADY,
    // Read data
    output wire [C_S_AXI_DATA_WIDTH-1:0] S_AXI_RDATA,
    output wire [1:0]                    S_AXI_RRESP,
    output wire                          S_AXI_RVALID,
    input  wire                          S_AXI_RREADY
);

// ---------------------------------------------------------------------------
// Internal signals
// ---------------------------------------------------------------------------
    reg [C_S_AXI_ADDR_WIDTH-1:0] axi_awaddr;
    reg  axi_awready, axi_wready, axi_bvalid;
    reg [C_S_AXI_ADDR_WIDTH-1:0] axi_araddr;
    reg  axi_arready, axi_rvalid;
    reg [C_S_AXI_DATA_WIDTH-1:0] axi_rdata;

    assign S_AXI_AWREADY = axi_awready;
    assign S_AXI_WREADY  = axi_wready;
    assign S_AXI_BRESP   = 2'b00;   // OKAY
    assign S_AXI_BVALID  = axi_bvalid;
    assign S_AXI_ARREADY = axi_arready;
    assign S_AXI_RDATA   = axi_rdata;
    assign S_AXI_RRESP   = 2'b00;
    assign S_AXI_RVALID  = axi_rvalid;

// ---------------------------------------------------------------------------
// Registers
// ---------------------------------------------------------------------------
    reg [31:0] reg_key_w0, reg_key_w1, reg_key_w2, reg_key_w3;
    reg [31:0] reg_din_w0, reg_din_w1, reg_din_w2, reg_din_w3;
    reg [31:0] reg_dout_w0, reg_dout_w1, reg_dout_w2, reg_dout_w3;
    reg        reg_status_done;

    wire [127:0] aes_key     = {reg_key_w0, reg_key_w1, reg_key_w2, reg_key_w3};
    wire [127:0] aes_data_in = {reg_din_w0, reg_din_w1, reg_din_w2, reg_din_w3};

    reg  aes_start;
    wire [127:0] aes_data_out;
    wire         aes_done;

// ---------------------------------------------------------------------------
// AES core instance
// ---------------------------------------------------------------------------
    aes128_core u_aes (
        .clk      (S_AXI_ACLK),
        .rst_n    (S_AXI_ARESETN),
        .start    (aes_start),
        .key      (aes_key),
        .data_in  (aes_data_in),
        .data_out (aes_data_out),
        .done     (aes_done)
    );

// ---------------------------------------------------------------------------
// AXI Write Channel
// ---------------------------------------------------------------------------
    // AWREADY: assert after AWVALID + WVALID both seen
    reg aw_en;
    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) begin
            axi_awready <= 1'b0; aw_en <= 1'b1;
        end else begin
            if (!axi_awready && S_AXI_AWVALID && S_AXI_WVALID && aw_en) begin
                axi_awready <= 1'b1; aw_en <= 1'b0;
            end else if (S_AXI_BREADY && axi_bvalid) begin
                aw_en <= 1'b1; axi_awready <= 1'b0;
            end else begin
                axi_awready <= 1'b0;
            end
        end
    end

    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) axi_awaddr <= 0;
        else if (!axi_awready && S_AXI_AWVALID && S_AXI_WVALID && aw_en)
            axi_awaddr <= S_AXI_AWADDR;
    end

    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) axi_wready <= 1'b0;
        else axi_wready <= (!axi_wready && S_AXI_WVALID && S_AXI_AWVALID && aw_en);
    end

    // Write data to registers
    wire slv_reg_wren = axi_wready && S_AXI_WVALID && axi_awready && S_AXI_AWVALID;
    wire [5:0] waddr = axi_awaddr[5:0];

    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) begin
            reg_key_w0 <= 0; reg_key_w1 <= 0; reg_key_w2 <= 0; reg_key_w3 <= 0;
            reg_din_w0 <= 0; reg_din_w1 <= 0; reg_din_w2 <= 0; reg_din_w3 <= 0;
            aes_start  <= 1'b0;
        end else begin
            aes_start <= 1'b0; // default: no start pulse
            if (slv_reg_wren) begin
                case (waddr)
                    6'h00: begin // CTRL
                        if (S_AXI_WDATA[0]) aes_start <= 1'b1;
                        // bit[1] = soft reset handled by ARESETN equivalent (ignored here)
                    end
                    6'h08: reg_key_w0 <= S_AXI_WDATA;
                    6'h0C: reg_key_w1 <= S_AXI_WDATA;
                    6'h10: reg_key_w2 <= S_AXI_WDATA;
                    6'h14: reg_key_w3 <= S_AXI_WDATA;
                    6'h18: reg_din_w0 <= S_AXI_WDATA;
                    6'h1C: reg_din_w1 <= S_AXI_WDATA;
                    6'h20: reg_din_w2 <= S_AXI_WDATA;
                    6'h24: reg_din_w3 <= S_AXI_WDATA;
                    default: ;
                endcase
            end
        end
    end

    // Capture AES output when done
    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) begin
            reg_dout_w0 <= 0; reg_dout_w1 <= 0;
            reg_dout_w2 <= 0; reg_dout_w3 <= 0;
            reg_status_done <= 1'b0;
        end else begin
            if (aes_done) begin
                reg_dout_w0     <= aes_data_out[127:96];
                reg_dout_w1     <= aes_data_out[95:64];
                reg_dout_w2     <= aes_data_out[63:32];
                reg_dout_w3     <= aes_data_out[31:0];
                reg_status_done <= 1'b1;
            end
            // Clear done when START is written
            if (aes_start) reg_status_done <= 1'b0;
        end
    end

    // BVALID
    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) axi_bvalid <= 0;
        else if (axi_awready && S_AXI_AWVALID && !axi_bvalid && axi_wready && S_AXI_WVALID)
            axi_bvalid <= 1'b1;
        else if (S_AXI_BREADY && axi_bvalid)
            axi_bvalid <= 1'b0;
    end

// ---------------------------------------------------------------------------
// AXI Read Channel
// ---------------------------------------------------------------------------
    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) begin
            axi_arready <= 1'b0; axi_araddr <= 0;
        end else begin
            if (!axi_arready && S_AXI_ARVALID) begin
                axi_arready <= 1'b1; axi_araddr <= S_AXI_ARADDR;
            end else axi_arready <= 1'b0;
        end
    end

    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) axi_rvalid <= 0;
        else if (axi_arready && S_AXI_ARVALID && !axi_rvalid)
            axi_rvalid <= 1'b1;
        else if (axi_rvalid && S_AXI_RREADY)
            axi_rvalid <= 1'b0;
    end

    wire [5:0] raddr = axi_araddr[5:0];
    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) axi_rdata <= 0;
        else if (!axi_rvalid) begin
            case (raddr)
                6'h00: axi_rdata <= 32'd0;                        // CTRL (write-only, read 0)
                6'h04: axi_rdata <= {31'd0, reg_status_done};     // STATUS
                6'h08: axi_rdata <= reg_key_w0;
                6'h0C: axi_rdata <= reg_key_w1;
                6'h10: axi_rdata <= reg_key_w2;
                6'h14: axi_rdata <= reg_key_w3;
                6'h18: axi_rdata <= reg_din_w0;
                6'h1C: axi_rdata <= reg_din_w1;
                6'h20: axi_rdata <= reg_din_w2;
                6'h24: axi_rdata <= reg_din_w3;
                6'h28: axi_rdata <= reg_dout_w0;
                6'h2C: axi_rdata <= reg_dout_w1;
                6'h30: axi_rdata <= reg_dout_w2;
                6'h34: axi_rdata <= reg_dout_w3;
                default: axi_rdata <= 32'd0;
            endcase
        end
    end

endmodule
