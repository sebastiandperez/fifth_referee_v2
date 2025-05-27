### batch_exporter.py

**Purpose:**  

`batch_exporter.py` orchestrates the **batch extraction, normalization, and saving of match data**, optimized for processing multiple matches per run. It is designed to handle large volumes of matches for entire matchdays or seasons, leveraging concurrent processing to maximize speed and reliability.

**Key Features:**
- Loads configuration settings (such as input and output directories) from `root.json`.
- Processes batches of match data references for each matchday.
- Utilizes concurrent processing to efficiently handle large datasets.
- For each match reference:
    1. Acquires raw data via the `getter` module.
    2. Cleans and normalizes the data using the `normalizer` module.
    3. Saves the resulting JSON file in an organized folder structure, grouped by matchday.
- Records any errors encountered during the process for later review.

**Core Workflow:**

1. **Configuration Loading:**  
   Reads all directory paths and settings from `root.json`, dynamically adjusting input and output locations for each competition and season.

2. **Batch Processing:**  
   For every matchday, a batch of match data references is processed in parallel, ensuring high performance even with large datasets.

3. **Error Handling:**  
   All errors are logged in dedicated files within the corresponding output folders for transparency and debugging.

**How to use:**

```bash
python batch_exporter.py <competition> <season>
# Example:
python batch_exporter.py premier_league 2023_2024
