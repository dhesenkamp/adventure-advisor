# Adventure Advisor

> Personalized, AI-based outdoor activity recommender system for activities such as hiking, running, cycling, via ferrata, climbing, mountaineering.

[Project description & requirements](https://docs.google.com/document/d/1fnTi8bGLr4bmyiPhwUcyi8KCYAVgEAzMyFstvKaeqNs/edit?usp=sharing)

# Architecture
![Architecture](assets/architecture.png)

# Agents
Our first setup uses Google's Gemini models: [Gemini API tutorial](https://colab.research.google.com/github/google-gemini/cookbook/blob/main/quickstarts/Get_started.ipynb)


- [Create own Gemini API key](https://aistudio.google.com/app/apikey) (NB: don't commit API key to repo)
- Set API key as environment variable (instructions for Mac/Linux with zsh):
  1. `echo "export API_KEY='yourkey'" >> ~/.zshrc`
  2. Update shell `source ~/.zshrc`
  3. Confirm with `echo $API_KEY`
  4. Use in Python script with `os.environ["API_KEY"]`


# Requirements
## Environment
Create conda environment file: `conda env export --from-history | grep -v "^prefix: " > environment.yml`

- numpy
- pandas
- geopandas
- osmnx
- streamlit
- google-genai