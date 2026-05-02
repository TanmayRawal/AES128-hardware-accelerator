// =============================================================================
// aes128_core.v  –  AES-128 ECB Encryption Engine (FIPS-197)
// Target  : Xilinx Artix-7 (Nexys 4 DDR, xc7a100tcsg324-1)
// Latency : 12 clk cycles after start (1 key-expand + 11 rounds)
// =============================================================================
`timescale 1ns/1ps

module aes128_core (
    input  wire        clk,
    input  wire        rst_n,      // active-low synchronous reset
    input  wire        start,      // pulse high for 1 cycle to begin
    input  wire [127:0] key,
    input  wire [127:0] data_in,
    output reg  [127:0] data_out,
    output reg         done        // pulses high for 1 cycle when output valid
);

// ---------------------------------------------------------------------------
// AES S-box (forward, 256 entries)
// ---------------------------------------------------------------------------
function [7:0] sbox_f;
    input [7:0] x;
    case (x)
        8'h00:sbox_f=8'h63; 8'h01:sbox_f=8'h7c; 8'h02:sbox_f=8'h77; 8'h03:sbox_f=8'h7b;
        8'h04:sbox_f=8'hf2; 8'h05:sbox_f=8'h6b; 8'h06:sbox_f=8'h6f; 8'h07:sbox_f=8'hc5;
        8'h08:sbox_f=8'h30; 8'h09:sbox_f=8'h01; 8'h0a:sbox_f=8'h67; 8'h0b:sbox_f=8'h2b;
        8'h0c:sbox_f=8'hfe; 8'h0d:sbox_f=8'hd7; 8'h0e:sbox_f=8'hab; 8'h0f:sbox_f=8'h76;
        8'h10:sbox_f=8'hca; 8'h11:sbox_f=8'h82; 8'h12:sbox_f=8'hc9; 8'h13:sbox_f=8'h7d;
        8'h14:sbox_f=8'hfa; 8'h15:sbox_f=8'h59; 8'h16:sbox_f=8'h47; 8'h17:sbox_f=8'hf0;
        8'h18:sbox_f=8'had; 8'h19:sbox_f=8'hd4; 8'h1a:sbox_f=8'ha2; 8'h1b:sbox_f=8'haf;
        8'h1c:sbox_f=8'h9c; 8'h1d:sbox_f=8'ha4; 8'h1e:sbox_f=8'h72; 8'h1f:sbox_f=8'hc0;
        8'h20:sbox_f=8'hb7; 8'h21:sbox_f=8'hfd; 8'h22:sbox_f=8'h93; 8'h23:sbox_f=8'h26;
        8'h24:sbox_f=8'h36; 8'h25:sbox_f=8'h3f; 8'h26:sbox_f=8'hf7; 8'h27:sbox_f=8'hcc;
        8'h28:sbox_f=8'h34; 8'h29:sbox_f=8'ha5; 8'h2a:sbox_f=8'he5; 8'h2b:sbox_f=8'hf1;
        8'h2c:sbox_f=8'h71; 8'h2d:sbox_f=8'hd8; 8'h2e:sbox_f=8'h31; 8'h2f:sbox_f=8'h15;
        8'h30:sbox_f=8'h04; 8'h31:sbox_f=8'hc7; 8'h32:sbox_f=8'h23; 8'h33:sbox_f=8'hc3;
        8'h34:sbox_f=8'h18; 8'h35:sbox_f=8'h96; 8'h36:sbox_f=8'h05; 8'h37:sbox_f=8'h9a;
        8'h38:sbox_f=8'h07; 8'h39:sbox_f=8'h12; 8'h3a:sbox_f=8'h80; 8'h3b:sbox_f=8'he2;
        8'h3c:sbox_f=8'heb; 8'h3d:sbox_f=8'h27; 8'h3e:sbox_f=8'hb2; 8'h3f:sbox_f=8'h75;
        8'h40:sbox_f=8'h09; 8'h41:sbox_f=8'h83; 8'h42:sbox_f=8'h2c; 8'h43:sbox_f=8'h1a;
        8'h44:sbox_f=8'h1b; 8'h45:sbox_f=8'h6e; 8'h46:sbox_f=8'h5a; 8'h47:sbox_f=8'ha0;
        8'h48:sbox_f=8'h52; 8'h49:sbox_f=8'h3b; 8'h4a:sbox_f=8'hd6; 8'h4b:sbox_f=8'hb3;
        8'h4c:sbox_f=8'h29; 8'h4d:sbox_f=8'he3; 8'h4e:sbox_f=8'h2f; 8'h4f:sbox_f=8'h84;
        8'h50:sbox_f=8'h53; 8'h51:sbox_f=8'hd1; 8'h52:sbox_f=8'h00; 8'h53:sbox_f=8'hed;
        8'h54:sbox_f=8'h20; 8'h55:sbox_f=8'hfc; 8'h56:sbox_f=8'hb1; 8'h57:sbox_f=8'h5b;
        8'h58:sbox_f=8'h6a; 8'h59:sbox_f=8'hcb; 8'h5a:sbox_f=8'hbe; 8'h5b:sbox_f=8'h39;
        8'h5c:sbox_f=8'h4a; 8'h5d:sbox_f=8'h4c; 8'h5e:sbox_f=8'h58; 8'h5f:sbox_f=8'hcf;
        8'h60:sbox_f=8'hd0; 8'h61:sbox_f=8'hef; 8'h62:sbox_f=8'haa; 8'h63:sbox_f=8'hfb;
        8'h64:sbox_f=8'h43; 8'h65:sbox_f=8'h4d; 8'h66:sbox_f=8'h33; 8'h67:sbox_f=8'h85;
        8'h68:sbox_f=8'h45; 8'h69:sbox_f=8'hf9; 8'h6a:sbox_f=8'h02; 8'h6b:sbox_f=8'h7f;
        8'h6c:sbox_f=8'h50; 8'h6d:sbox_f=8'h3c; 8'h6e:sbox_f=8'h9f; 8'h6f:sbox_f=8'ha8;
        8'h70:sbox_f=8'h51; 8'h71:sbox_f=8'ha3; 8'h72:sbox_f=8'h40; 8'h73:sbox_f=8'h8f;
        8'h74:sbox_f=8'h92; 8'h75:sbox_f=8'h9d; 8'h76:sbox_f=8'h38; 8'h77:sbox_f=8'hf5;
        8'h78:sbox_f=8'hbc; 8'h79:sbox_f=8'hb6; 8'h7a:sbox_f=8'hda; 8'h7b:sbox_f=8'h21;
        8'h7c:sbox_f=8'h10; 8'h7d:sbox_f=8'hff; 8'h7e:sbox_f=8'hf3; 8'h7f:sbox_f=8'hd2;
        8'h80:sbox_f=8'hcd; 8'h81:sbox_f=8'h0c; 8'h82:sbox_f=8'h13; 8'h83:sbox_f=8'hec;
        8'h84:sbox_f=8'h5f; 8'h85:sbox_f=8'h97; 8'h86:sbox_f=8'h44; 8'h87:sbox_f=8'h17;
        8'h88:sbox_f=8'hc4; 8'h89:sbox_f=8'ha7; 8'h8a:sbox_f=8'h7e; 8'h8b:sbox_f=8'h3d;
        8'h8c:sbox_f=8'h64; 8'h8d:sbox_f=8'h5d; 8'h8e:sbox_f=8'h19; 8'h8f:sbox_f=8'h73;
        8'h90:sbox_f=8'h60; 8'h91:sbox_f=8'h81; 8'h92:sbox_f=8'h4f; 8'h93:sbox_f=8'hdc;
        8'h94:sbox_f=8'h22; 8'h95:sbox_f=8'h2a; 8'h96:sbox_f=8'h90; 8'h97:sbox_f=8'h88;
        8'h98:sbox_f=8'h46; 8'h99:sbox_f=8'hee; 8'h9a:sbox_f=8'hb8; 8'h9b:sbox_f=8'h14;
        8'h9c:sbox_f=8'hde; 8'h9d:sbox_f=8'h5e; 8'h9e:sbox_f=8'h0b; 8'h9f:sbox_f=8'hdb;
        8'ha0:sbox_f=8'he0; 8'ha1:sbox_f=8'h32; 8'ha2:sbox_f=8'h3a; 8'ha3:sbox_f=8'h0a;
        8'ha4:sbox_f=8'h49; 8'ha5:sbox_f=8'h06; 8'ha6:sbox_f=8'h24; 8'ha7:sbox_f=8'h5c;
        8'ha8:sbox_f=8'hc2; 8'ha9:sbox_f=8'hd3; 8'haa:sbox_f=8'hac; 8'hab:sbox_f=8'h62;
        8'hac:sbox_f=8'h91; 8'had:sbox_f=8'h95; 8'hae:sbox_f=8'he4; 8'haf:sbox_f=8'h79;
        8'hb0:sbox_f=8'he7; 8'hb1:sbox_f=8'hc8; 8'hb2:sbox_f=8'h37; 8'hb3:sbox_f=8'h6d;
        8'hb4:sbox_f=8'h8d; 8'hb5:sbox_f=8'hd5; 8'hb6:sbox_f=8'h4e; 8'hb7:sbox_f=8'ha9;
        8'hb8:sbox_f=8'h6c; 8'hb9:sbox_f=8'h56; 8'hba:sbox_f=8'hf4; 8'hbb:sbox_f=8'hea;
        8'hbc:sbox_f=8'h65; 8'hbd:sbox_f=8'h7a; 8'hbe:sbox_f=8'hae; 8'hbf:sbox_f=8'h08;
        8'hc0:sbox_f=8'hba; 8'hc1:sbox_f=8'h78; 8'hc2:sbox_f=8'h25; 8'hc3:sbox_f=8'h2e;
        8'hc4:sbox_f=8'h1c; 8'hc5:sbox_f=8'ha6; 8'hc6:sbox_f=8'hb4; 8'hc7:sbox_f=8'hc6;
        8'hc8:sbox_f=8'he8; 8'hc9:sbox_f=8'hdd; 8'hca:sbox_f=8'h74; 8'hcb:sbox_f=8'h1f;
        8'hcc:sbox_f=8'h4b; 8'hcd:sbox_f=8'hbd; 8'hce:sbox_f=8'h8b; 8'hcf:sbox_f=8'h8a;
        8'hd0:sbox_f=8'h70; 8'hd1:sbox_f=8'h3e; 8'hd2:sbox_f=8'hb5; 8'hd3:sbox_f=8'h66;
        8'hd4:sbox_f=8'h48; 8'hd5:sbox_f=8'h03; 8'hd6:sbox_f=8'hf6; 8'hd7:sbox_f=8'h0e;
        8'hd8:sbox_f=8'h61; 8'hd9:sbox_f=8'h35; 8'hda:sbox_f=8'h57; 8'hdb:sbox_f=8'hb9;
        8'hdc:sbox_f=8'h86; 8'hdd:sbox_f=8'hc1; 8'hde:sbox_f=8'h1d; 8'hdf:sbox_f=8'h9e;
        8'he0:sbox_f=8'he1; 8'he1:sbox_f=8'hf8; 8'he2:sbox_f=8'h98; 8'he3:sbox_f=8'h11;
        8'he4:sbox_f=8'h69; 8'he5:sbox_f=8'hd9; 8'he6:sbox_f=8'h8e; 8'he7:sbox_f=8'h94;
        8'he8:sbox_f=8'h9b; 8'he9:sbox_f=8'h1e; 8'hea:sbox_f=8'h87; 8'heb:sbox_f=8'he9;
        8'hec:sbox_f=8'hce; 8'hed:sbox_f=8'h55; 8'hee:sbox_f=8'h28; 8'hef:sbox_f=8'hdf;
        8'hf0:sbox_f=8'h8c; 8'hf1:sbox_f=8'ha1; 8'hf2:sbox_f=8'h89; 8'hf3:sbox_f=8'h0d;
        8'hf4:sbox_f=8'hbf; 8'hf5:sbox_f=8'he6; 8'hf6:sbox_f=8'h42; 8'hf7:sbox_f=8'h68;
        8'hf8:sbox_f=8'h41; 8'hf9:sbox_f=8'h99; 8'hfa:sbox_f=8'h2d; 8'hfb:sbox_f=8'h0f;
        8'hfc:sbox_f=8'hb0; 8'hfd:sbox_f=8'h54; 8'hfe:sbox_f=8'hbb; 8'hff:sbox_f=8'h16;
        default: sbox_f = 8'h00;
    endcase
endfunction

// ---------------------------------------------------------------------------
// xtime: multiply by 2 in GF(2^8)
// ---------------------------------------------------------------------------
function [7:0] xtime_f;
    input [7:0] b;
    xtime_f = b[7] ? ((b << 1) ^ 8'h1b) : (b << 1);
endfunction

// ---------------------------------------------------------------------------
// SubWord: apply S-box to all 4 bytes of a word
// ---------------------------------------------------------------------------
function [31:0] sub_word;
    input [31:0] w;
    sub_word = {sbox_f(w[31:24]), sbox_f(w[23:16]), sbox_f(w[15:8]), sbox_f(w[7:0])};
endfunction

// ---------------------------------------------------------------------------
// RotWord: left-rotate word by 1 byte
// ---------------------------------------------------------------------------
function [31:0] rot_word;
    input [31:0] w;
    rot_word = {w[23:0], w[31:24]};
endfunction

// ---------------------------------------------------------------------------
// Key expansion: produce all 11 round keys (1408 bits) combinationally
// AES-128: 4 words input key → 44 words (w[0..43])
// ---------------------------------------------------------------------------
// Rcon table (10 entries, indices 1..10)
function [7:0] rcon_f;
    input [3:0] i;
    case (i)
        4'd1:  rcon_f = 8'h01; 4'd2:  rcon_f = 8'h02;
        4'd3:  rcon_f = 8'h04; 4'd4:  rcon_f = 8'h08;
        4'd5:  rcon_f = 8'h10; 4'd6:  rcon_f = 8'h20;
        4'd7:  rcon_f = 8'h40; 4'd8:  rcon_f = 8'h80;
        4'd9:  rcon_f = 8'h1b; 4'd10: rcon_f = 8'h36;
        default: rcon_f = 8'h00;
    endcase
endfunction

// Expand key into 44 words; return flat 1408-bit bus [rk10..rk0]
// round_keys[r] = {w[4r], w[4r+1], w[4r+2], w[4r+3]}
task key_expand;
    input  [127:0] k;
    output [1407:0] rk; // rk[1407:1280]=rk0 ... rk[127:0]=rk10
    reg [31:0] w [0:43];
    integer i;
    reg [31:0] temp;
    begin
        // Load initial key words
        w[0] = k[127:96]; w[1] = k[95:64];
        w[2] = k[63:32];  w[3] = k[31:0];
        for (i = 4; i < 44; i = i + 1) begin
            temp = w[i-1];
            if (i % 4 == 0)
                temp = sub_word(rot_word(temp)) ^ {rcon_f(i/4), 24'h000000};
            w[i] = w[i-4] ^ temp;
        end
        // Pack into flat output [rk0 at top, rk10 at bottom]
        rk[1407:1280] = {w[0],  w[1],  w[2],  w[3]};
        rk[1279:1152] = {w[4],  w[5],  w[6],  w[7]};
        rk[1151:1024] = {w[8],  w[9],  w[10], w[11]};
        rk[1023:896]  = {w[12], w[13], w[14], w[15]};
        rk[895:768]   = {w[16], w[17], w[18], w[19]};
        rk[767:640]   = {w[20], w[21], w[22], w[23]};
        rk[639:512]   = {w[24], w[25], w[26], w[27]};
        rk[511:384]   = {w[28], w[29], w[30], w[31]};
        rk[383:256]   = {w[32], w[33], w[34], w[35]};
        rk[255:128]   = {w[36], w[37], w[38], w[39]};
        rk[127:0]     = {w[40], w[41], w[42], w[43]};
    end
endtask

// ---------------------------------------------------------------------------
// SubBytes on full 128-bit state (column-major: byte0=state[127:120])
// ---------------------------------------------------------------------------
function [127:0] sub_bytes_f;
    input [127:0] s;
    integer j;
    reg [127:0] out;
    begin
        for (j = 0; j < 16; j = j + 1)
            out[127 - j*8 -: 8] = sbox_f(s[127 - j*8 -: 8]);
        sub_bytes_f = out;
    end
endfunction

// ---------------------------------------------------------------------------
// ShiftRows — AES state stored row-major (row0=bytes 0,1,2,3 etc.)
// Byte ordering: state[127:120]=b0, [119:112]=b1 ... [7:0]=b15
// Row 0: b0,b1,b2,b3      shift 0
// Row 1: b4,b5,b6,b7      shift 1 left
// Row 2: b8,b9,b10,b11    shift 2 left
// Row 3: b12,b13,b14,b15  shift 3 left
// ---------------------------------------------------------------------------
function [127:0] shift_rows_f;
    input [127:0] s;
    reg [7:0] b [0:15];
    integer k;
    begin
        for (k=0;k<16;k=k+1) b[k] = s[127-k*8 -: 8];
        shift_rows_f = {
            b[0],  b[5],  b[10], b[15],   // row 0 unchanged, row 1 shift 1
            b[4],  b[9],  b[14], b[3],    // row 1 (was b4,b5,b6,b7) → b5,b6,b7,b4
            b[8],  b[13], b[2],  b[7],    // row 2 shift 2
            b[12], b[1],  b[6],  b[11]    // row 3 shift 3
        };
    end
endfunction

// ---------------------------------------------------------------------------
// MixColumns — operates on each column (4 bytes)
// Column c: bytes (c, c+4, c+8, c+12)
// ---------------------------------------------------------------------------
function [31:0] mix_col;
    input [31:0] col; // {s0,s1,s2,s3}
    reg [7:0] s0,s1,s2,s3,r0,r1,r2,r3;
    begin
        s0=col[31:24]; s1=col[23:16]; s2=col[15:8]; s3=col[7:0];
        r0 = xtime_f(s0) ^ (xtime_f(s1)^s1) ^ s2        ^ s3;
        r1 = s0          ^ xtime_f(s1)        ^ (xtime_f(s2)^s2) ^ s3;
        r2 = s0          ^ s1                 ^ xtime_f(s2)       ^ (xtime_f(s3)^s3);
        r3 = (xtime_f(s0)^s0) ^ s1           ^ s2                ^ xtime_f(s3);
        mix_col = {r0,r1,r2,r3};
    end
endfunction

function [127:0] mix_columns_f;
    input [127:0] s;
    reg [7:0] b [0:15];
    integer k;
    reg [31:0] c0,c1,c2,c3,m0,m1,m2,m3;
    begin
        for (k=0;k<16;k=k+1) b[k]=s[127-k*8 -: 8];
        // Column-major layout: consecutive 4 bytes = one column
        c0={b[0],b[1],b[2],b[3]};
        c1={b[4],b[5],b[6],b[7]};
        c2={b[8],b[9],b[10],b[11]};
        c3={b[12],b[13],b[14],b[15]};
        m0=mix_col(c0); m1=mix_col(c1); m2=mix_col(c2); m3=mix_col(c3);
        // Reassemble column-major
        mix_columns_f = {m0, m1, m2, m3};
    end
endfunction

// ---------------------------------------------------------------------------
// Helper: extract round key r (0..10) from flat 1408-bit array
// ---------------------------------------------------------------------------
function [127:0] get_rk;
    input [1407:0] rk_flat;
    input [3:0]    r;
    get_rk = rk_flat[1407 - r*128 -: 128];
endfunction

// ---------------------------------------------------------------------------
// State machine
// ---------------------------------------------------------------------------
localparam ST_IDLE    = 2'd0;
localparam ST_RUNNING = 2'd1;
localparam ST_DONE    = 2'd2;

reg [1:0]   state;
reg [3:0]   round;      // 1..10
reg [127:0] blk;        // current AES state
reg [1407:0] rk_reg;   // expanded round keys (stored at start)

always @(posedge clk) begin
    if (!rst_n) begin
        state    <= ST_IDLE;
        done     <= 1'b0;
        data_out <= 128'd0;
        blk      <= 128'd0;
        round    <= 4'd0;
        rk_reg   <= 1408'd0;
    end else begin
        done <= 1'b0; // default

        case (state)
        // ---- IDLE: wait for start pulse ----
        ST_IDLE: begin
            if (start) begin
                // Expand key
                key_expand(key, rk_reg);
                // Initial AddRoundKey (Round 0 key is exactly the input key)
                blk   <= data_in ^ key;
                round <= 4'd1;
                state <= ST_RUNNING;
            end
        end

        // ---- RUNNING: iterate rounds 1..10 ----
        ST_RUNNING: begin
            if (round < 4'd10) begin
                // Rounds 1-9: SubBytes, ShiftRows, MixColumns, AddRoundKey
                blk   <= mix_columns_f(shift_rows_f(sub_bytes_f(blk))) ^ get_rk(rk_reg, round);
                round <= round + 4'd1;
            end else begin
                // Round 10: SubBytes, ShiftRows, AddRoundKey (no MixColumns)
                blk   <= shift_rows_f(sub_bytes_f(blk)) ^ get_rk(rk_reg, 4'd10);
                state <= ST_DONE;
            end
        end

        // ---- DONE: output result for one cycle ----
        ST_DONE: begin
            data_out <= blk;
            done     <= 1'b1;
            state    <= ST_IDLE;
        end
        endcase
    end
end

endmodule
