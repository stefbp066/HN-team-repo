from pyspark.sql import SparkSession

def run_pipeline():
    spark = SparkSession.builder.getOrCreate()
    source_table = "databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.facilities"
    target_table = "workspace.default.gold_flagged_facilities"
    
    print(f"Reading from source shared table {source_table}...")
    
    # SQL query to build the gold contradiction validation table
    query = f"""
    CREATE TABLE IF NOT EXISTS {target_table} AS
    SELECT
      unique_id,
      name,
      address_city,
      address_stateOrRegion,
      description,
      capability,
      procedure,
      equipment,
      numberDoctors,
      capacity,
      
      -- Contradiction Rule 1: Claimed ICU but missing bed capacity
      CASE
        WHEN (capability ILIKE '%ICU%' OR description ILIKE '%ICU%') 
             AND (capacity IS NULL OR capacity = '0' OR capacity = '') THEN 1
        ELSE 0
      END as flag_icu_no_capacity,

      -- Contradiction Rule 2: Claimed emergency/trauma but zero/null doctors
      CASE
        WHEN (capability ILIKE '%emergency%' OR capability ILIKE '%trauma%') 
             AND (numberDoctors IS NULL OR numberDoctors = '0' OR numberDoctors = '') THEN 1
        ELSE 0
      END as flag_emergency_no_doctors,

      -- Contradiction Rule 3: Surgical procedures claimed but no anesthesia support mentioned
      CASE
        WHEN (procedure ILIKE '%surgery%' OR capability ILIKE '%surgery%') 
             AND (equipment NOT ILIKE '%anesthe%' AND equipment NOT ILIKE '%ventilator%' AND description NOT ILIKE '%anesthe%') THEN 1
        ELSE 0
      END as flag_surgery_no_anesthesia,

      -- Contradiction Rule 4: Critical Data Desert (completely empty meta metrics)
      CASE
        WHEN capacity IS NULL AND numberDoctors IS NULL AND yearEstablished IS NULL THEN 1
        ELSE 0
      END as flag_data_desert,

      -- Compute a Weighted Trust Score (0 - 100)
      100 - (
        (CASE WHEN (capability ILIKE '%ICU%' OR description ILIKE '%ICU%') AND (capacity IS NULL OR capacity = '0' OR capacity = '') THEN 30 ELSE 0 END) +
        (CASE WHEN (capability ILIKE '%emergency%' OR capability ILIKE '%trauma%') AND (numberDoctors IS NULL OR numberDoctors = '0' OR numberDoctors = '') THEN 35 ELSE 0 END) +
        (CASE WHEN (procedure ILIKE '%surgery%' OR capability ILIKE '%surgery%') AND (equipment NOT ILIKE '%anesthe%' AND equipment NOT ILIKE '%ventilator%' AND description NOT ILIKE '%anesthe%') THEN 20 ELSE 0 END) +
        (CASE WHEN capacity IS NULL AND numberDoctors IS NULL AND yearEstablished IS NULL THEN 15 ELSE 0 END)
      ) as trust_score,

      'PENDING' as review_status,
      CAST(NULL as string) as reviewer_notes
    FROM {source_table}
    """
    
    print(f"Initializing/populating gold validation table: {target_table}...")
    spark.sql(query)
    print("Gold validation table created successfully.")

if __name__ == "__main__":
    run_pipeline()
