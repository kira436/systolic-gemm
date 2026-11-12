module systolic_array #(parameter int ROWS = 4, COLS = 4) (
    input  logic                    clk, rst_n,
    // weight write port
    input  logic                    wr_en,
    input  logic [$clog2(ROWS)-1:0] wr_row,
    input  logic [$clog2(COLS)-1:0] wr_col,
    input  logic signed [7:0]       wr_data,
    // activations, one INT8 per row (row r = bits [8*r +: 8])
    input  logic [ROWS*8-1:0]       a_in,
    // bottom-row partial sums, one INT32 per column (col c = bits [32*c +: 32])
    output logic [COLS*32-1:0]      psum_out
);
    // TODO: generate ROWS x COLS PEs; per-PE load_w = wr_en && wr_row==r && wr_col==c;
    //       a: west->east, psum: north->south, top-row psum_in = 0, w_in = wr_data for all PEs.

    generate 
        for (genvar r = 0; r < ROWS; r++) begin : row_loop
            for (genvar c = 0; c < COLS; c++) begin : col_loop
                logic signed [7:0]  a_in_pe, w_in_pe, a_out;
                logic signed [31:0] psum_in_pe, psum_out_pe, psum_out_int;

                // Connect activations from west to east
                if (c == 0) begin
                    assign a_in_pe = a_in[8*r +: 8]; // Input activation for the first column
                end else begin
                    assign a_in_pe = row_loop[r].col_loop[c-1].a_out; // From the left PE
                end

                // Connect partial sums from north to south
                if (r == 0) begin
                    assign psum_in_pe = '0; // Top row has no incoming psum
                end else begin
                    assign psum_in_pe = row_loop[r-1].col_loop[c].psum_out_int; // From the above PE
                end

                // Weight input for the PE
                assign w_in_pe = (wr_en && wr_row == r && wr_col == c) ? wr_data : '0;

                // Instantiate the processing element
                pe pe_inst (
                    .clk(clk),
                    .rst_n(rst_n),
                    .load_w(wr_en && wr_row == r && wr_col == c),
                    .w_in(w_in_pe),
                    .a_in(a_in_pe),
                    .psum_in(psum_in_pe),
                    .a_out(row_loop[r].col_loop[c].a_out),
                    .psum_out(row_loop[r].col_loop[c].psum_out_int)
                );

                // Connect the output partial sums to the final output bus
                assign psum_out[32*c +: 32] = row_loop[ROWS-1].col_loop[c].psum_out_int;
            end
        end
    endgenerate
endmodule