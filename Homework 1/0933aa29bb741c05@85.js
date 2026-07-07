function _data(__query,FileAttachment,invalidation){return(
__query(FileAttachment("data.csv"),{from:{table:"data"},sort:[],slice:{to:null,from:null},filter:[],select:{columns:null}},invalidation)
)}

function _2(md){return(
md`# Best Video Games of All Time
## Exploring Metacritic's Top 100 Reviewed Games
 
This notebook visualizes data from Metacritic's highest-scoring video games.

Above, I loaded the original dataset, data.csv, into the notebook.

The dataset includes game titles, platforms, metascores, and release dates.
Let's dig into which platforms dominated, which eras produced the best games,
and whether rank actually correlates with Metascore.

I will visualize this dataset through a bar chart, a scatter plot, and parallel coordinates.
`
)}

function _3(md){return(
md`# Preliminary Work
## Clean the dataset
In this block, we will parse the date column into a javascript Date object, extract the year from each date, filter out any rows missing critical fields, and normalize the user_score variable to the same 0-100 scale that is used in Metacritic.`
)}

function _clean(data){return(
data
  .filter(d => d.Name && d.Platform && d.Metascore && d.Date)
  .map(d => {
    const parts = d.Date.split("-");        // e.g. "23-Nov-98"
    const parsed = new Date(d.Date);
    return {
      ...d,
      Metascore: +d.Metascore,
      Year: parsed.getFullYear(),
      // Correct Y2K: years parsed as e.g. 2098 → 1998
      Year: parsed.getFullYear() > 2025 ? parsed.getFullYear() - 100 : parsed.getFullYear()
    };
  })
)}

function _5(md){return(
md`## Inspect the Data
In this block, I'll preview the first 5 cleaned rows to make sure the parsing is correct`
)}

function _6(clean){return(
clean.slice(0, 5)
)}

function _7(md){return(
md`## Visualization 1: Bar Chart — Games per Platform
**Motivation:** 
This bar chart tells us which platforms produced the most top-ranked games. I did this to reveal which hardware generations dominated critical acclaim. A bar chart is ideal for comparing counts across discrete categories, such as platforms.

In this bar chart, I group the data by platform on the x-axis and count entries on the y-axis. I sort the data in descending order.
`
)}

function _8(d3,clean)
{
  const platformCounts = d3.rollups(
    clean,
    v => v.length,
    d => d.Platform
  )
  .map(([platform, count]) => ({ platform, count }))
  .sort((a, b) => b.count - a.count);

  const width = 700, height = 420;
  const margin = { top: 30, right: 30, bottom: 100, left: 50 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  const x = d3.scaleBand()
    .domain(platformCounts.map(d => d.platform))
    .range([0, innerW])
    .padding(0.3);

  const y = d3.scaleLinear()
    .domain([0, d3.max(platformCounts, d => d.count)])
    .nice()
    .range([innerH, 0]);

  const color = d3.scaleOrdinal(d3.schemeTableau10)
    .domain(platformCounts.map(d => d.platform));

  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height);

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  g.selectAll("rect")
    .data(platformCounts)
    .join("rect")
      .attr("x", d => x(d.platform))
      .attr("y", d => y(d.count))
      .attr("width", x.bandwidth())
      .attr("height", d => innerH - y(d.count))
      .attr("fill", d => color(d.platform))
      .attr("rx", 3); // rounded corners

  g.append("g")
    .attr("transform", `translate(0,${innerH})`)
    .call(d3.axisBottom(x))
    .selectAll("text")
      .attr("transform", "rotate(-40)")
      .style("text-anchor", "end")
      .style("font-size", "12px");

  g.append("g")
    .call(d3.axisLeft(y).ticks(6));

  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -innerH / 2)
    .attr("y", -40)
    .attr("text-anchor", "middle")
    .style("font-size", "13px")
    .text("Number of Top-Ranked Games");

  svg.append("text")
    .attr("x", width / 2)
    .attr("y", 20)
    .attr("text-anchor", "middle")
    .style("font-size", "15px")
    .style("font-weight", "bold")
    .text("Top-Ranked Games by Platform");

  return svg.node();
}


function _9(md){return(
md`## Visualization 2: Scatter Plot — Metascore over Time
**Motivation:** A scatter plot reveals whether top scores cluster in certain eras,
and whether platform diversity changed over time. Each point is a game, colored by platform.
Hover to see the game name.

Here, the x-axis is the release year, and the y-axis is the metascore. Each circle represents one game, colored by the video game platform. This reveals whether high-scoring games cluster in certain decades.`
)}

function _10(d3,clean)
{
  const width = 720, height = 450;
  const margin = { top: 30, right: 160, bottom: 60, left: 60 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  // --- Scales ---
  const x = d3.scaleLinear()
    .domain(d3.extent(clean, d => d.Year)).nice()
    .range([0, innerW]);

  const y = d3.scaleLinear()
    .domain([d3.min(clean, d => d.Metascore) - 1, 100])
    .range([innerH, 0]);

  const platforms = [...new Set(clean.map(d => d.Platform))];
  const color = d3.scaleOrdinal(d3.schemeTableau10).domain(platforms);

  // --- SVG ---
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height);

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // --- Gridlines ---
  g.append("g")
    .attr("class", "grid")
    .call(d3.axisLeft(y).ticks(6).tickSize(-innerW).tickFormat(""))
    .selectAll("line").style("stroke", "#e0e0e0");

  // --- Dots ---
  g.selectAll("circle")
    .data(clean)
    .join("circle")
      .attr("cx", d => x(d.Year))
      .attr("cy", d => y(d.Metascore))
      .attr("r", 6)
      .attr("fill", d => color(d.Platform))
      .attr("opacity", 0.75)
      .append("title")  // native tooltip on hover
        .text(d => `${d.Name} (${d.Platform})\nScore: ${d.Metascore} | Year: ${d.Year}`);

  // --- Axes ---
  g.append("g")
    .attr("transform", `translate(0,${innerH})`)
    .call(d3.axisBottom(x).tickFormat(d3.format("d")));

  g.append("g").call(d3.axisLeft(y));

  // --- Axis Labels ---
  g.append("text")
    .attr("x", innerW / 2).attr("y", innerH + 45)
    .attr("text-anchor", "middle")
    .style("font-size", "13px")
    .text("Release Year");

  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -innerH / 2).attr("y", -45)
    .attr("text-anchor", "middle")
    .style("font-size", "13px")
    .text("Metascore");

  // --- Legend ---
  const legend = svg.append("g")
    .attr("transform", `translate(${margin.left + innerW + 15}, ${margin.top})`);

  platforms.forEach((p, i) => {
    legend.append("circle").attr("cx", 0).attr("cy", i * 20).attr("r", 6).attr("fill", color(p));
    legend.append("text").attr("x", 12).attr("y", i * 20 + 4)
      .style("font-size", "11px").text(p);
  });

  // --- Title ---
  svg.append("text")
    .attr("x", width / 2 - margin.right / 2).attr("y", 20)
    .attr("text-anchor", "middle")
    .style("font-size", "15px").style("font-weight", "bold")
    .text("Metascore vs. Release Year by Platform");

  return svg.node();
}


function _11(md){return(
md`## Visualization 3: Parallel Coordinates — Multi-dimensional Game Profiles (Advanced)
**Motivation:** Parallel coordinates allow us to view multiple dimensions simultaneously. 
We can view the rank, metascore, and year across every game at once. Lines colored by the platform reveal
which platforms consistently appear across score and era ranges, something impossible to see in a CSV.`
)}

function _12(d3,clean)
{
  const width = 720, height = 420;
  const margin = { top: 50, right: 60, bottom: 40, left: 60 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  // Dimensions to show on parallel axes
  const dimensions = ["Rank", "Metascore", "Year"];

  // --- Scales: one y-scale per dimension ---
  const yScales = {};
  dimensions.forEach(dim => {
    yScales[dim] = d3.scaleLinear()
      .domain(d3.extent(clean, d => d[dim])).nice()
      .range([innerH, 0]);
  });

  // --- X scale: evenly space the axes ---
  const x = d3.scalePoint()
    .domain(dimensions)
    .range([0, innerW]);

  const platforms = [...new Set(clean.map(d => d.Platform))];
  const color = d3.scaleOrdinal(d3.schemeTableau10).domain(platforms);

  // --- Path generator for each game ---
  const line = d3.line();
  const path = d => line(dimensions.map(dim => [x(dim), yScales[dim](d[dim])]));

  // --- SVG ---
  const svg = d3.create("svg")
    .attr("width", width)
    .attr("height", height);

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // --- Draw one line per game ---
  g.selectAll("path")
    .data(clean)
    .join("path")
      .attr("d", path)
      .attr("fill", "none")
      .attr("stroke", d => color(d.Platform))
      .attr("stroke-width", 1.5)
      .attr("opacity", 0.5)
      .append("title")
        .text(d => `${d.Name} | ${d.Platform} | Score: ${d.Metascore} | Year: ${d.Year}`);

  // --- Draw each vertical axis ---
  dimensions.forEach(dim => {
    const axisG = g.append("g")
      .attr("transform", `translate(${x(dim)},0)`);

    // Axis line + ticks
    axisG.call(d3.axisLeft(yScales[dim]).ticks(6));

    // Axis label
    axisG.append("text")
      .attr("y", -15)
      .attr("text-anchor", "middle")
      .style("font-size", "13px")
      .style("font-weight", "bold")
      .style("fill", "#333")
      .text(dim);
  });

  // --- Legend ---
  const legend = svg.append("g")
    .attr("transform", `translate(${margin.left}, ${height - margin.bottom + 10})`);

  platforms.forEach((p, i) => {
    legend.append("circle").attr("cx", i * 90).attr("cy", 0).attr("r", 5).attr("fill", color(p));
    legend.append("text").attr("x", i * 90 + 9).attr("y", 4)
      .style("font-size", "10px").text(p);
  });

  // --- Title ---
  svg.append("text")
    .attr("x", width / 2).attr("y", 20)
    .attr("text-anchor", "middle")
    .style("font-size", "15px").style("font-weight", "bold")
    .text("Parallel Coordinates: Rank, Metascore & Year by Platform");

  return svg.node();
}


function _13(md){return(
md`## Insight 1: PlayStation platforms dominate the top rankings
From the bar chart and scatter plot, PlayStation consoles (PS, PS2, PS3, PS4)
collectively account for the largest share of top-ranked games.
This suggests Sony's hardware generations consistently attracted the highest-scoring titles,
while platforms like the Dreamcast appear rarely but with surprisingly high scores (e.g. SoulCalibur, NFL 2K1).`
)}

function _14(md){return(
md`## Insight 2: The late 1990s–2000s were the golden era of critically acclaimed games
The scatter plot shows a clear concentration of near-perfect Metascores (97–99)
clustered between 1998 and 2004 — including Ocarina of Time (99), SoulCalibur (98),
and GTA III (97). Post-2010 games still rank highly but rarely break past 97,
suggesting critics have become harder to impress, or the definition of "perfect" has shifted over time.`
)}

export default function define(runtime, observer) {
  const main = runtime.module();
  function toString() { return this.url; }
  const fileAttachments = new Map([
    ["data.csv", {url: new URL("./files/65a935417bee711bb823c174149ea8d8c73c533a48d59ce7bafb4372f5575b804b9e40c843dc1276cf6b831a14bc2a2ff418544e294d8d51af156d985e89fc34.csv", import.meta.url), mimeType: "text/csv", toString}]
  ]);
  main.builtin("FileAttachment", runtime.fileAttachments(name => fileAttachments.get(name)));
  main.variable(observer("data")).define("data", ["__query","FileAttachment","invalidation"], _data);
  main.variable(observer()).define(["md"], _2);
  main.variable(observer()).define(["md"], _3);
  main.variable(observer("clean")).define("clean", ["data"], _clean);
  main.variable(observer()).define(["md"], _5);
  main.variable(observer()).define(["clean"], _6);
  main.variable(observer()).define(["md"], _7);
  main.variable(observer()).define(["d3","clean"], _8);
  main.variable(observer()).define(["md"], _9);
  main.variable(observer()).define(["d3","clean"], _10);
  main.variable(observer()).define(["md"], _11);
  main.variable(observer()).define(["d3","clean"], _12);
  main.variable(observer()).define(["md"], _13);
  main.variable(observer()).define(["md"], _14);
  return main;
}
