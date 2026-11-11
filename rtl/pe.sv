// Weight-stationary INT8 MAC processing element.
// Contract (must match model/golden.py:pe_step):
//   load_w=1 : weight <= w_in ; psum_out <= psum_in        (no MAC this cycle)
//   load_w=0 : psum_out <= psum_in + a_in * weight         (INT32, wraps)
//   a_out <= a_in every cycle
// Reset (active low, synchronous): all registers to 0.
//
// TODO (yours to write - you must be able to defend every line in an interview):
//   1. Declare the registers.
//   2. Implement the sequential update above.
//   3. Decide: should psum_out be registered? What does that do to array latency and timing?
module pe (
    input  logic               clk,
    input  logic               rst_n,
    input  logic               load_w,
    input  logic signed [7:0]  w_in,
    input  logic signed [7:0]  a_in,
    input  logic signed [31:0] psum_in,
    output logic signed [7:0]  a_out,
    output logic signed [31:0] psum_out
);
    // Stub: outputs tied off so the testbench fails until you implement the PE.
    //assign a_out    = '0;
    //assign psum_out = '0;
    logic signed [7:0]  weight;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_out <= '0;
            psum_out <= '0;
            weight <= '0;
        end else begin
            a_out <= a_in;
            if (load_w) begin
                psum_out <= psum_in;
                weight <= w_in;
            end else begin
                psum_out <= psum_in + a_in * weight;
            end
        end
    end
endmodule
