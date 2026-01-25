# Flow Requirements: Demo Simple

## Flow Information

- Name: demo_simple
- Purpose: Demo flow that generates dummy data, applies a simple transformation, and loads to a temporary directory with verification
- Layer: Bronze

## Source Requirements

- Type: Generated Data (Dummy)
- Location: In-memory DataFrame generation
- Format: Spark DataFrame
- Extraction mode: Full load (generates data on each run)
- Data generation:
  - Generate 100 rows of dummy data
  - Schema:
    - `id`: Integer (sequential, 1 to 100)
    - `name`: String (generated as "Item_{id}")
    - `value`: Double (random between 0.0 and 100.0)
    - `category`: String (random from: "A", "B", "C")
    - `created_at`: Timestamp (current timestamp for all rows)

## Target Requirements

- Type: Directory (Temporary)
- Location: Temporary directory (use Python tempfile or Spark temp directory)
- Format: Parquet
- Load strategy: Overwrite
- Verification: After load, verify that:
  - The directory exists
  - Files were created (at least one .parquet file)
  - Data can be read back
  - Row count matches expected (100 rows)

## Transformation Requirements

- Complexity: Simple (no steps directory needed)
- Transformations:
  1. Add a computed column `value_doubled` = `value * 2`
  2. Add a computed column `is_high_value` = `value > 50.0` (boolean)
  3. Select final columns: `id`, `name`, `value`, `value_doubled`, `is_high_value`, `category`, `created_at`

## Flow Behavior

- Use CDC: false
- Change detection: false
- Restart capability: false
- First run detection: Not needed
- Execution: Simple ETL flow, no special state management required

## Configuration

- Environment variables: None required
- Error path: Optional (can use temp directory for errors if needed)
- Partitioning: Single partition (small dataset)
- Num partitions: 1

## Special Requirements

### Data Generation

- Generate exactly 100 rows
- Use Spark's built-in functions to generate data
- Ensure reproducible results (use seed if using random values)

### Load Verification

After loading, the flow must:
1. Verify the output directory exists
2. List files in the directory and verify at least one .parquet file exists
3. Read back the data and verify row count is 100
4. If verification passes, return Status with status_value="OK" and message="Load completed and verified successfully"
5. If verification fails, return Status with status_value="ERROR" and appropriate error message

### Status Return

- On success: Return `Status(status_value="OK", message="Load completed and verified successfully")`
- On failure: Return `Status(status_value="ERROR", message="<error description>")`

## Implementation Notes

### Extract

- Use `spark.range(1, 101)` to generate IDs
- Use Spark SQL functions to generate other columns:
  - `concat(lit("Item_"), col("id"))` for names
  - `rand() * 100` for values (with seed for reproducibility)
  - `when(rand() < 0.33, "A").when(rand() < 0.66, "B").otherwise("C")` for categories
  - `current_timestamp()` for created_at

### Transform

- Simple column additions using `withColumn()`
- No complex aggregations or joins needed

### Load

- Write to temporary directory using `tempfile.mkdtemp()` or Spark's temp directory
- Use `mode("overwrite")` and `format("parquet")`
- After write, verify:
  - Verify directory exists
  - List .parquet files
  - Read back and count rows
  - Return appropriate Status

## Expected Output

- Output directory: Temporary directory with Parquet files
- File count: At least 1 Parquet file (may be partitioned)
- Row count: Exactly 100 rows
- Status: OK if verification passes

## Notes

- This is a simple demo flow for testing the agent
- No external dependencies required
- All data is generated in-memory
- Perfect for quick testing and validation
- Can be extended later with more complex requirements
