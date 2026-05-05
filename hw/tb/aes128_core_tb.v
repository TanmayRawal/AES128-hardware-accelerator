// =============================================================================
// aes128_core_tb.v — Self-Checking Testbench for AES-128 Core
//
// Tests:
//   1. FIPS-197 Appendix B Known Answer Test (KAT)
//   2. All-zeros key + plaintext
//   3. All-ones key + plaintext
//   4. CTR-mode roundtrip (encrypt counter, XOR, re-encrypt, XOR → recover)
//   5. Avalanche: 1-bit plaintext change → ~50% ciphertext bits differ
//
// Usage:
//   iverilog -o tb aes128_core_tb.v ../ip/aes128_axilite/hdl/aes128_core.v
//   vvp tb
//
//   -- or with Vivado xsim --
//   xvlog aes128_core_tb.v ../ip/aes128_axilite/hdl/aes128_core.v
//   xelab aes128_core_tb -s sim
//   xsim sim -runall
// =============================================================================
`timescale 1ns/1ps

module aes128_core_tb;

    // ---- DUT signals ----
    reg         clk;
    reg         rst_n;
    reg         start;
    reg  [127:0] key;
    reg  [127:0] data_in;
    wire [127:0] data_out;
    wire        done;

    // ---- Test tracking ----
    integer test_num;
    integer pass_count;
    integer fail_count;
    integer total_tests;
    reg [127:0] expected;
    reg [127:0] result;

    // ---- Instantiate DUT ----
    aes128_core uut (
        .clk      (clk),
        .rst_n    (rst_n),
        .start    (start),
        .key      (key),
        .data_in  (data_in),
        .data_out (data_out),
        .done     (done)
    );

    // ---- Clock: 10ns period (100 MHz) ----
    initial clk = 0;
    always #5 clk = ~clk;

    // ---- Helper task: run one encryption and check result ----
    task run_encrypt;
        input [127:0] t_key;
        input [127:0] t_data;
        input [127:0] t_expected;
        input [256*8-1:0] t_name;  // test name string (up to 256 chars)
        begin
            @(posedge clk);
            key     <= t_key;
            data_in <= t_data;
            start   <= 1'b1;
            @(posedge clk);
            start   <= 1'b0;

            // Wait for done
            wait (done == 1'b1);
            @(posedge clk);

            result = data_out;
            test_num = test_num + 1;

            if (result === t_expected) begin
                $display("  [PASS] Test %0d: %0s", test_num, t_name);
                pass_count = pass_count + 1;
            end else begin
                $display("  [FAIL] Test %0d: %0s", test_num, t_name);
                $display("         Key:      %h", t_key);
                $display("         Input:    %h", t_data);
                $display("         Expected: %h", t_expected);
                $display("         Got:      %h", result);
                fail_count = fail_count + 1;
            end

            // Small gap between tests
            repeat(2) @(posedge clk);
        end
    endtask

    // ---- Helper task: run encryption, return result (no check) ----
    task run_encrypt_get;
        input  [127:0] t_key;
        input  [127:0] t_data;
        output [127:0] t_result;
        begin
            @(posedge clk);
            key     <= t_key;
            data_in <= t_data;
            start   <= 1'b1;
            @(posedge clk);
            start   <= 1'b0;

            wait (done == 1'b1);
            @(posedge clk);
            t_result = data_out;
            repeat(2) @(posedge clk);
        end
    endtask

    // ---- Count differing bits between two 128-bit values ----
    function integer count_diff_bits;
        input [127:0] a;
        input [127:0] b;
        reg [127:0] diff;
        integer i, count;
        begin
            diff = a ^ b;
            count = 0;
            for (i = 0; i < 128; i = i + 1)
                count = count + diff[i];
            count_diff_bits = count;
        end
    endfunction

    // ---- Main test sequence ----
    initial begin
        $display("");
        $display("===========================================================");
        $display("  AES-128 Core Testbench — FIPS-197 Verification");
        $display("===========================================================");
        $display("");

        test_num   = 0;
        pass_count = 0;
        fail_count = 0;
        total_tests = 5;

        // ---- Reset ----
        rst_n = 1'b0;
        start = 1'b0;
        key   = 128'd0;
        data_in = 128'd0;
        repeat(5) @(posedge clk);
        rst_n = 1'b1;
        repeat(2) @(posedge clk);

        // ============================================================
        // TEST 1: FIPS-197 Appendix B Known Answer Test
        // ============================================================
        // Key:       2b7e1516 28aed2a6 abf71588 09cf4f3c
        // Plaintext: 3243f6a8 885a308d 313198a2 e0370734
        // Expected:  3925841d 02dc09fb dc118597 196a0b32
        run_encrypt(
            128'h2b7e151628aed2a6abf7158809cf4f3c,
            128'h3243f6a8885a308d313198a2e0370734,
            128'h3925841d02dc09fbdc118597196a0b32,
            "FIPS-197 Appendix B KAT"
        );

        // ============================================================
        // TEST 2: All-zeros key + plaintext
        // ============================================================
        // Key:       00000000 00000000 00000000 00000000
        // Plaintext: 00000000 00000000 00000000 00000000
        // Expected:  66e94bd4 ef8a2c3b 884cfa59 ca342b2e
        run_encrypt(
            128'h00000000000000000000000000000000,
            128'h00000000000000000000000000000000,
            128'h66e94bd4ef8a2c3b884cfa59ca342b2e,
            "All-zeros key + plaintext"
        );

        // ============================================================
        // TEST 3: All-ones key + plaintext
        // ============================================================
        // Key:       ffffffff ffffffff ffffffff ffffffff
        // Plaintext: ffffffff ffffffff ffffffff ffffffff
        // Expected:  a1f6258c 877d5fcd 8964484538bfc92c
        run_encrypt(
            128'hffffffffffffffffffffffffffffffff,
            128'hffffffffffffffffffffffffffffffff,
            128'ha1f6258c877d5fcd8964484538bfc92c,
            "All-ones key + plaintext"
        );

        // ============================================================
        // TEST 4: CTR-mode roundtrip
        // ============================================================
        // Encrypt(counter) → keystream
        // ciphertext = plaintext XOR keystream
        // Encrypt(counter) again → same keystream
        // recovered = ciphertext XOR keystream → must equal plaintext
        begin
            reg [127:0] ctr_key, ctr_counter, plaintext_block;
            reg [127:0] keystream1, keystream2;
            reg [127:0] ciphertext, recovered;

            ctr_key       = 128'h000102030405060708090a0b0c0d0e0f;
            ctr_counter   = 128'hf0e0d0c0b0a090807060504030201000;
            plaintext_block = 128'hdeadbeefcafebabe1234567890abcdef;

            // First encryption: get keystream
            run_encrypt_get(ctr_key, ctr_counter, keystream1);

            // XOR to get ciphertext
            ciphertext = plaintext_block ^ keystream1;

            // Second encryption: same counter → same keystream
            run_encrypt_get(ctr_key, ctr_counter, keystream2);

            // XOR ciphertext with keystream → recover plaintext
            recovered = ciphertext ^ keystream2;

            test_num = test_num + 1;
            if (recovered === plaintext_block) begin
                $display("  [PASS] Test %0d: CTR-mode roundtrip", test_num);
                pass_count = pass_count + 1;
            end else begin
                $display("  [FAIL] Test %0d: CTR-mode roundtrip", test_num);
                $display("         Plaintext: %h", plaintext_block);
                $display("         Recovered: %h", recovered);
                fail_count = fail_count + 1;
            end
            repeat(2) @(posedge clk);
        end

        // ============================================================
        // TEST 5: Avalanche effect — 1-bit change in plaintext
        // ============================================================
        begin
            reg [127:0] av_key, pt_original, pt_flipped;
            reg [127:0] ct_original, ct_flipped;
            integer diff_bits;

            av_key      = 128'h000102030405060708090a0b0c0d0e0f;
            pt_original = 128'h00000000000000000000000000000000;
            pt_flipped  = 128'h00000000000000000000000000000001; // bit 0 flipped

            run_encrypt_get(av_key, pt_original, ct_original);
            run_encrypt_get(av_key, pt_flipped,  ct_flipped);

            diff_bits = count_diff_bits(ct_original, ct_flipped);

            test_num = test_num + 1;
            // Avalanche: expect ~64 bits different (50% of 128)
            // Accept range: 40-90 bits (31%-70%) — very generous for single sample
            if (diff_bits >= 40 && diff_bits <= 90) begin
                $display("  [PASS] Test %0d: Avalanche effect (%0d/128 bits differ = %0d%%)",
                         test_num, diff_bits, (diff_bits * 100) / 128);
                pass_count = pass_count + 1;
            end else begin
                $display("  [FAIL] Test %0d: Avalanche effect (%0d/128 bits differ = %0d%%)",
                         test_num, diff_bits, (diff_bits * 100) / 128);
                $display("         Expected ~64 bits (50%%), got %0d bits", diff_bits);
                fail_count = fail_count + 1;
            end
        end

        // ============================================================
        // Summary
        // ============================================================
        $display("");
        $display("===========================================================");
        if (fail_count == 0) begin
            $display("  ALL %0d TESTS PASSED", pass_count);
        end else begin
            $display("  RESULT: %0d PASSED, %0d FAILED (out of %0d)",
                     pass_count, fail_count, pass_count + fail_count);
        end
        $display("===========================================================");
        $display("");

        #100;
        $finish;
    end

    // Timeout watchdog — 10,000 cycles max
    initial begin
        #100000;
        $display("");
        $display("  [ERROR] Simulation timed out after 100,000 ns!");
        $display("");
        $finish;
    end

endmodule
