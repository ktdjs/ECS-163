# Homework 2: Visualization Dashboard: Layout Design + Visual Encoding
For homework 2, you will create a dashboard with three visualization views. This homework will not be using Observable. Instead, you will be developing a web-based interface in JavaScript with D3.js, where we have provided one template.

To begin, you need to first fork this repository.
After the fork, clone the repository using the following commands:

```bash
  git clone https://github.com/<your-github-account-name>/ecs163-26s
  cd ecs163-26s/Homework2 
```
    
Create a new folder inside the Homework 2 directory in the forked repository. The name of the folder should be the same as your UC Davis email account name (without ' @ucdavis.edu'). **Inside this folder, you will add all your code.**

Before coding, please go over one of the following tutorials:

* D3.js : [Introduction](https://d3js.org/#introduction), [Core concepts](https://d3-graph-gallery.com/intro_d3js.html), [Selection](https://www.d3indepth.com/selections/), [Data Joins](https://www.d3indepth.com/datajoins/)

If you need to learn more about JavaScript, you can refer to [A re-introduction to JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript/A_re-introduction_to_JavaScript)

---

## Step 0: Choose a Dataset from the Following List
In this assignment, you can choose one of the following datasets:

* [Data Science Job Salary](https://www.kaggle.com/datasets/arnabchaki/data-science-salaries-2023)
* [Global Terrorism Database](https://www.kaggle.com/START-UMD/gtd)
* [Cosmetics](https://www.kaggle.com/datasets/kingabzpro/cosmetics-datasets)
* [Fitness Consumer Survey](https://www.kaggle.com/datasets/harshitaaswani/fitness-consumer-survey-data)
* [Student Mental Health](https://www.kaggle.com/datasets/shariful07/student-mental-health)
* [Student Alcohol Consumption](https://www.kaggle.com/uciml/student-alcohol-consumption)
* [Music and Mental Health Survey](https://www.kaggle.com/datasets/catherinerasgaitis/mxmh-survey-results)
* [List of Historical Ballot Measures in SF](https://data.sfgov.org/City-Management-and-Ethics/List-of-Historical-Ballot-Measures/xzie-ixjw)
* [Pokemon](https://www.kaggle.com/alopez247/pokemon)

  
To use a dataset, download the data file from the respective URL above and put it in the `./<your-template>/data` folder.

## Step 1: Set Up the Environment
We provided template using Javascript, you can find it and more technical details in `./Homework2/Template`. **DO NOT** directly modify on the template.

Note that you are free to use other existing frameworks and libraries in JavaScript to implement your interface, while d3.js remains required for completing this assignment.

To start the application, open folder which contains all your files in **VSCode**, then open *index.html* file, right click on the mouse and press "open with liver server". If you do not have this option, install the *Live Server* extension on your VSCode.


# Requirements
Your task is to create a visualization dashboard. The design of this dashboard should facilitate the exploration of a dataset in an effective or interesting way.

* This dashboard must have three visualization views, which should be created with different visualization methods (see below).
* Your visualizations should include at least one advanced visualization method.
* The visualizations should depict different dimensions or aspects of the dataset to be examined. 
* The three visualizations should fit on a fullscreen browser. Consider where each view should be placed while designing the layout of your dashboard.
* **Legends** for each view need to be provided as well as **axis labels** and **chart titles**.
* One of your three views should serve as an overview of the data.
* Choose appropriate visual encodings.
* Color choice matters and has an effect on the interpretability of the visualization. Depending on the data the type of color scale you will use will change (categorical, linear, etc).
* Carefully consider the design for each encoding that you will use and its effectiveness for portraying the data.  Depending on the data you are visualizing, certain pairings of marks and channels will be more effective.
* Your design choices and the rationale behind them will be part of the grading criteria.
* Submit your dashboard as is. You can add comment on canvas if you wish to explain anything (although the dashboard should be self-explanatory), but there's no need to format your web app as a report.

The design paradigm you will be following is referred to as focus + context. 

* A focus view is where the data of most interest is displayed at full size or with full details.
* A context view is a peripheral zone, an overview,  where elements are displayed at reduced size or in a simplified way.

Note that creating a bar chart and a histogram only counts as using only one method, since their implementation is nearly the same.

**Fundamental**
* Bar chart or histogram
* Pie or donut chart
* Line and area chart
* 2D heatmap or matrix view
* Scatter plot
* Node-link diagram
* Geographical map

**Advanced**
* Parallel set or parallel coordinates plot
* Sankey or alluvial diagram
* Star coordinates or plot
* Chord diagram
* Stream graph
* Arc diagram
* Dendrogram

# Submission
To submit for this assignment, you need to first [fork](https://docs.github.com/en/free-pro-team@latest/github/getting-started-with-github/fork-a-repo) this [repository](https://github.com/via-teaching/ecs163-26s). After the fork, clone the forked repository using the following commands: 
```bash
  git clone https://github.com/<your-github-account-name>/ecs163-26s
  cd ecs163-26s/Homework2
```

Create a new folder inside the Homework 2 directory in the forked repository. The name of the folder should be the same as your UC Davis email account name (without ' @ucdavis.edu'). Put all your codes inside this folder, and use "git add" to add all your codes, and then commit. 
```bash
git add <your-filename> 
git commit -m "Homework2" 
git push
```
After you push your code to your repository, follow the instructions [here](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork) to create a pull request for this repository. Finally, submit the hyperlink of the pull request to UCD Canvas. The hyperlink should look like this- "https://github.com/
via-teaching/ecs163-26s/pull/{your-pull-request-id}".