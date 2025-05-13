# Fifth Referee: Football Data Analyst Playground

## Welcome to Fifth Referee v2

**Fifth Referee v2** is a modular system designed to organize, structure, and analyze historical data from football competitions, teams, and players.  
It's aimed at those who want to practice their Data Science skills using solid tools like **Python**, **PostgreSQL**, and **object-oriented design principles**.

You won’t find scrapers or raw data here—just the core logic needed to transform `.json` files into clean, queryable databases, create dynamic representations of each season, and explore team performance through reusable, well-documented, and forward-thinking code.

This repository is a complete overhaul of the original prototype, with a strong focus on clarity, architecture, and professionalism.  
If you're into data analytics applied to sports, you're in the right place!

---

## What Problem Does It Solve?

Fifth Referee v2 provides a clean solution for organizing and working with structured sports data, removing the need for ad-hoc scripts, fragile pipelines, or unreliable data sources.

It is designed for scenarios where data is already available in JSON format (from public sources, private providers, or simulated sets), but there's a need to:

- Convert it into clean, tabular structures.
- Load it into a relational database using a well-defined schema.
- Model key sports entities (such as seasons, teams, and players) using object-oriented programming.
- Run analysis and extract insights without being tied to any specific external tools or libraries.

By decoupling the **data extraction process** (which is out of scope) from the **organization, transformation, and modeling**, this project allows anyone with compatible data to use or extend the system without having to modify it from scratch.

---

## Key Features

- **Structured JSON File Loader**  
  Transforms preformatted JSON files into clean, standardized DataFrames ready for analysis or storage.

- **Data Cleaning and Processing**  
  Includes logic for validating, transforming, and cleaning data to ensure schema consistency and handle missing or malformed values.

- **PostgreSQL Database Injection**  
  Processed data is automatically inserted into a PostgreSQL database, enabling efficient queries and reliable persistence.

- **Object-Oriented Modeling**  
  Competitions, seasons, teams, and players are modeled as object instances, encapsulating relevant behavior and enabling intuitive data navigation.

- **Built-in Analysis and Visualization Methods**  
  Each instance includes methods to explore team and player performance, calculate statistics, and generate meaningful insights.

- **Interactive Jupyter Notebook**  
  A guided notebook walks users through the full workflow—from data loading to insight generation—ideal for exploratory analysis and presentation.

- **Modular and Extensible Design**  
  Clear separation of concerns between loading, processing, modeling, and analysis. The architecture supports easy scaling and adaptation to new data formats or use cases.

---

## Author & Contact

This project was developed by **Sebastian**, a Computer Science student passionate about data architecture, clean design, and football analytics.

If you have questions, suggestions, or want to collaborate, feel free to reach out via:

- Email: [sebastiand.perez@outlook.com]
- LinkedIn: [https://www.linkedin.com/in/sebastian-perez-pantoja/]

Feel free to open issues or contribute via pull requests—feedback is always welcome!
