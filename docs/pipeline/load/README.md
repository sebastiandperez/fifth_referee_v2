# Database Loaders

## Overview

The `loaders` module provides a set of classes designed to **reliably and efficiently insert extracted and normalized football data into a PostgreSQL database**.  
Each loader is responsible for a specific set of entities (teams, matches, players, stats, etc.), ensuring clear separation of concerns, robust error handling, and proper transaction management.

All loaders inherit from a common `BaseLoader` that handles logging and provides utility methods.  
Each loader receives an active database connection (`conn`), which should be managed at the pipeline or application level (open once, pass everywhere, close when done).

---

All insertion methods validate incoming DataFrames and log actions and errors.
