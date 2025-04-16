# Adventure Advisor

> Personalized, AI-based outdoor activity recommender system for activities such as hiking, running, cycling, via ferrata, climbing, mountaineering.

[Project description & requirements](https://docs.google.com/document/d/1fnTi8bGLr4bmyiPhwUcyi8KCYAVgEAzMyFstvKaeqNs/edit?usp=sharing)

# Architecture
![Architecture](assets/architecture.png)

# Requirements
## Environment
Create conda environment file: `conda env export --from-history | grep -v "^prefix: " > environment.yml`

- numpy
- pandas
- geopandas
- osmnx