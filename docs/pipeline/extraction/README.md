# matchday_extractor

## Overview

`matchday_extractor` is a focused component of the football data workflow that **extracts, normalizes, and stores individual match data as JSON files, organized by matchday**.  
This module does **not** insert data into any database or perform analytics—it simply prepares clean, ready-to-use files for subsequent analysis or integration.

Each output folder represents a matchday and contains one JSON file per match, allowing for easy access and further processing in later stages of the data pipeline.

---

## Introduction

This pipeline segment is responsible for the **acquisition, normalization, and batch processing of raw football match data**.  
It is divided into three main components:

- **getter**: Handles the acquisition of raw match data from abstract sources. It provides a unified interface for obtaining data, regardless of the underlying source or protocol.
- **normalizer**: Cleans, restructures, and standardizes the raw data into a uniform format that downstream modules can consume.
- **batch_exporter**: Orchestrates the batch processing and normalization of multiple match data files using concurrent processing to maximize efficiency.

**Ethical Note**

This pipeline is intended for use with data acquired from authorized and ethical sources only.
No unauthorized extraction, scraping, or other practices violating terms of service are included or supported.
Please ensure all data sources comply with legal and ethical standards.
