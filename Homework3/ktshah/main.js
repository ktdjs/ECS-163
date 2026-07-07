
// All possible genres in preferred display order
var GENRES = [
  'Classical','Country','EDM','Folk','Gospel','Hip-Hop',
  'Jazz','K-Pop','Latin','Lofi','Metal','Pop','R&B','Rap','Rock','Video game music'
];

// Mental health condition keys (match cleaned data fields)
var CONDITIONS = ['Anxiety','Depression','Insomnia','OCD'];

// PCP axes: which numeric fields to show and their fixed domains
var PCP_DIMS = [
  { key: 'age',         label: 'Age',        domain: [10, 90] },
  { key: 'hoursPerDay', label: 'Hours/Day',  domain: [0,  24] },
  { key: 'anxiety',     label: 'Anxiety',    domain: [0,  10] },
  { key: 'depression',  label: 'Depression', domain: [0,  10] },
  { key: 'insomnia',    label: 'Insomnia',   domain: [0,  10] },
  { key: 'ocd',         label: 'OCD',        domain: [0,  10] }
];

// One color per genre — ordinal scale
var colorScale = d3.scaleOrdinal()
  .domain(GENRES)
  .range([
    '#c084fc','#38bdf8','#fb7185','#34d399','#fbbf24','#a78bfa',
    '#f472b6','#60a5fa','#4ade80','#f87171','#e879f9','#86efac',
    '#fde68a','#67e8f9','#fdba74','#a5f3fc'
  ]);

// Animation duration (ms) used for all transitions — keeps them consistent
var T_DUR = 450;

// ─────────────────────────────────────────────────────────────────────────────
// SHARED FILTER STATE
// When either interaction fires, we update this object then call updateAll().
// ─────────────────────────────────────────────────────────────────────────────
var filterState = {
  selectedGenre: null,    // string | null  — set by bar-chart click
  brushExtents:  {}       // { dimKey: [lo, hi] } — set by PCP brushes
};

// ─────────────────────────────────────────────────────────────────────────────
// TOOLTIP HELPERS
// ─────────────────────────────────────────────────────────────────────────────
var tooltip = document.getElementById('tooltip');

function showTip(html, event) {
  tooltip.innerHTML = html;
  tooltip.style.display = 'block';
  tooltip.style.left = (event.clientX + 14) + 'px';
  tooltip.style.top  = (event.clientY - 10) + 'px';
}
function hideTip() { tooltip.style.display = 'none'; }

// ─────────────────────────────────────────────────────────────────────────────
// FILTER HELPER — returns the subset of data that passes all active filters
// ─────────────────────────────────────────────────────────────────────────────
function applyFilters(data) {
  return data.filter(function(d) {
    // Genre selection filter (from bar-chart click)
    if (filterState.selectedGenre && d.genre !== filterState.selectedGenre) return false;

    // PCP brush filter — every active brush extent must include this row
    var extents = filterState.brushExtents;
    for (var key in extents) {
      if (!extents.hasOwnProperty(key)) continue;
      var ext = extents[key];
      if (ext && (d[key] < ext[0] || d[key] > ext[1])) return false;
    }
    return true;
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// MODULE-LEVEL REFERENCES — filled in by each draw function so updateAll()
// can reach into them without globals per chart.
// ─────────────────────────────────────────────────────────────────────────────
var barUpdate    = null;   // function(filteredData)
var heatUpdate   = null;   // function(filteredData)
var pcpUpdate    = null;   // function(filteredData)

// ─────────────────────────────────────────────────────────────────────────────
// MASTER UPDATE — called after any filter change
// ─────────────────────────────────────────────────────────────────────────────
function updateAll(allData) {
  var filtered = applyFilters(allData);
  if (barUpdate)  barUpdate(filtered);
  if (heatUpdate) heatUpdate(filtered);
  if (pcpUpdate)  pcpUpdate(filtered);
}

// ─────────────────────────────────────────────────────────────────────────────
// INIT DASHBOARD — called once from index.html after CSV loads
// ─────────────────────────────────────────────────────────────────────────────
function initDashboard(allData) {
  drawBarChart(allData);
  drawHeatmap(allData);
  drawPCP(allData);

  // Reset button clears all filters and re-renders with full dataset
  document.getElementById('reset-btn').addEventListener('click', function() {
    filterState.selectedGenre = null;
    filterState.brushExtents  = {};
    updateAll(allData);
    // Also clear any visual brush selections drawn on the PCP axes
    d3.selectAll('.brush').call(d3.brush().move, null);
  });
}

// =============================================================================
// CHART 1: BAR CHART — Genre Popularity (Overview)
// INTERACTION: click a bar to select that genre; all views update.
// TRANSITION: bar heights animate on every filter update (Filtering transition).
// =============================================================================
function drawBarChart(allData) {
  var container = document.getElementById('bar-chart');
  var W = container.clientWidth;
  var H = container.clientHeight;
  var margin = { top: 12, right: 12, bottom: 60, left: 42 };
  var w = W - margin.left - margin.right;
  var h = H - margin.top - margin.bottom;

  // Count all data by genre for the initial x-domain (order never changes)
  var allCounts = d3.nest()
    .key(function(d) { return d.genre; })
    .rollup(function(v) { return v.length; })
    .entries(allData)
    .sort(function(a, b) { return b.value - a.value; });

  var genreOrder = allCounts.map(function(d) { return d.key; });

  var svg = d3.select('#bar-chart').append('svg')
    .attr('width', W).attr('height', H);

  var g = svg.append('g')
    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

  // X scale — domain fixed to full genre order so bars don't jump around
  var x = d3.scaleBand()
    .domain(genreOrder)
    .range([0, w])
    .padding(0.25);

  // Y scale — domain will stretch to filtered max
  var y = d3.scaleLinear()
    .domain([0, d3.max(allCounts, function(d) { return d.value; }) * 1.12])
    .range([h, 0]);

  // Dashed grid lines (drawn once, behind bars)
  g.append('g').attr('class', 'grid')
    .call(d3.axisLeft(y).ticks(5).tickSize(-w).tickFormat(''))
    .call(function(sel) { sel.select('.domain').remove(); })
    .selectAll('line')
      .attr('stroke', '#1e2235')
      .attr('stroke-dasharray', '3,3');

  // Bars — start at zero height, will be set by first updateBars() call
  var bars = g.selectAll('.bar')
    .data(genreOrder)
    .enter().append('rect')
      .attr('class', 'bar')
      .attr('x', function(d) { return x(d); })
      .attr('y', h)                    // start at baseline for enter animation
      .attr('width', x.bandwidth())
      .attr('height', 0)
      .attr('rx', 3)
      .attr('fill', function(d) { return colorScale(d); })
      // INTERACTION: click selects/deselects a genre
      .on('click', function(genre) {
        if (filterState.selectedGenre === genre) {
          filterState.selectedGenre = null;   // second click = deselect
        } else {
          filterState.selectedGenre = genre;
        }
        updateAll(allData);
      })
      .on('mousemove', function(genre) {
        var count = allData.filter(function(d) { return d.genre === genre; }).length;
        showTip('<strong>' + genre + '</strong><br/>' + count + ' respondents', d3.event);
      })
      .on('mouseleave', hideTip);

  // Count labels above bars
  var labels = g.selectAll('.bar-label')
    .data(genreOrder)
    .enter().append('text')
      .attr('class', 'bar-label')
      .attr('x', function(d) { return x(d) + x.bandwidth() / 2; })
      .attr('y', h)
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--muted)')
      .attr('font-size', 9)
      .attr('font-family', 'DM Mono, monospace')
      .text('');

  // X axis (drawn once — genre labels)
  var xAxisG = g.append('g').attr('class', 'axis')
    .attr('transform', 'translate(0,' + h + ')')
    .call(d3.axisBottom(x));
  xAxisG.selectAll('text')
    .attr('transform', 'rotate(-38)')
    .attr('text-anchor', 'end')
    .attr('dx', '-4').attr('dy', '4');

  // Y axis — will be re-called on update
  var yAxisG = g.append('g').attr('class', 'axis');

  // Y axis label
  g.append('text').attr('class', 'axis-label')
    .attr('transform', 'rotate(-90)')
    .attr('x', -h / 2).attr('y', -32)
    .attr('text-anchor', 'middle')
    .text('# Respondents');

  // ── Update function — called by updateAll() ──────────────────────────────
  // TRANSITION TYPE: Filtering — bars animate to new heights smoothly
  barUpdate = function(filteredData) {
    // Recount for filtered subset
    var countMap = {};
    filteredData.forEach(function(d) {
      countMap[d.genre] = (countMap[d.genre] || 0) + 1;
    });

    // Rescale Y to filtered max so small selections stay readable
    var maxVal = d3.max(genreOrder, function(g) { return countMap[g] || 0; }) || 1;
    y.domain([0, maxVal * 1.12]);

    // Animate Y axis rescale (Substrate Transformation transition)
    yAxisG.transition().duration(T_DUR)
      .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format('d')))
      .call(function(sel) { sel.select('.domain').remove(); });

    // Animate bar heights (Filtering transition)
    bars.transition().duration(T_DUR)
      .attr('y', function(genre) { return y(countMap[genre] || 0); })
      .attr('height', function(genre) { return h - y(countMap[genre] || 0); })
      // Dim bars that are not the selected genre
      .attr('opacity', function(genre) {
        if (!filterState.selectedGenre) return 1;
        return filterState.selectedGenre === genre ? 1 : 0.18;
      });

    // Animate count labels
    labels.transition().duration(T_DUR)
      .attr('y', function(genre) { return y(countMap[genre] || 0) - 3; })
      .text(function(genre) { return countMap[genre] || 0; });
  };

  // Trigger initial render
  barUpdate(allData);
}

// =============================================================================
// CHART 2: HEATMAP — Genre × Condition Avg Severity (Context)
// TRANSITION: cell opacity animates when filter changes (Filtering transition).
// =============================================================================
function drawHeatmap(allData) {
  var container = document.getElementById('heatmap');
  var W = container.clientWidth;
  var H = container.clientHeight;
  var margin = { top: 12, right: 95, bottom: 55, left: 95 };
  var w = W - margin.left - margin.right;
  var h = H - margin.top - margin.bottom;

  // Genres present in the full dataset, in GENRES order
  var presentGenres = GENRES.filter(function(g) {
    return allData.some(function(d) { return d.genre === g; });
  });

  var svg = d3.select('#heatmap').append('svg')
    .attr('width', W).attr('height', H);

  var g = svg.append('g')
    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

  var xScale = d3.scaleBand().domain(CONDITIONS).range([0, w]).padding(0.08);
  var yScale = d3.scaleBand().domain(presentGenres).range([0, h]).padding(0.06);

  // Sequential color scale: dark purple → pink/red = low → high severity
  var colorMap = d3.scaleSequential(
    d3.interpolateRgbBasis(['#0d0f14','#1e1040','#7c3aed','#c084fc','#fb7185'])
  ).domain([2, 9]);

  // Pre-compute avg scores for full data (used for cell fill — doesn't change)
  var allAvg = {};
  presentGenres.forEach(function(genre) {
    var rows = allData.filter(function(d) { return d.genre === genre; });
    CONDITIONS.forEach(function(cond) {
      var key = genre + '|' + cond;
      allAvg[key] = d3.mean(rows, function(d) { return d[cond.toLowerCase()]; });
    });
  });

  // Build flat array for cell binding
  var cellData = [];
  presentGenres.forEach(function(genre) {
    CONDITIONS.forEach(function(cond) {
      cellData.push({ genre: genre, cond: cond });
    });
  });

  // Draw cells — fill uses full-data average (context stays visible)
  var cells = g.selectAll('.heatmap-cell')
    .data(cellData)
    .enter().append('rect')
      .attr('class', 'heatmap-cell')
      .attr('x', function(d) { return xScale(d.cond); })
      .attr('y', function(d) { return yScale(d.genre); })
      .attr('width', xScale.bandwidth())
      .attr('height', yScale.bandwidth())
      .attr('fill', function(d) { return colorMap(allAvg[d.genre + '|' + d.cond]); })
      .attr('rx', 3)
      .on('mousemove', function(d) {
        showTip(
          '<strong>' + d.genre + '</strong><br/>' +
          d.cond + ': ' + allAvg[d.genre + '|' + d.cond].toFixed(2) + ' avg (all data)',
          d3.event
        );
      })
      .on('mouseleave', hideTip);

  // Value text inside cells
  var cellTexts = g.selectAll('.cell-text')
    .data(cellData)
    .enter().append('text')
      .attr('class', 'cell-text')
      .attr('x', function(d) { return xScale(d.cond) + xScale.bandwidth() / 2; })
      .attr('y', function(d) { return yScale(d.genre) + yScale.bandwidth() / 2 + 3; })
      .attr('text-anchor', 'middle')
      .attr('font-size', 8)
      .attr('font-family', 'DM Mono, monospace')
      .attr('fill', function(d) { return allAvg[d.genre + '|' + d.cond] > 6 ? '#fff' : 'var(--muted)'; })
      .text(function(d) { return allAvg[d.genre + '|' + d.cond].toFixed(1); });

  // X axis — condition labels
  g.append('g').attr('class', 'axis')
    .attr('transform', 'translate(0,' + h + ')')
    .call(d3.axisBottom(xScale))
    .call(function(sel) { sel.select('.domain').remove(); sel.selectAll('line').remove(); });

  // Y axis — genre labels
  g.append('g').attr('class', 'axis')
    .call(d3.axisLeft(yScale))
    .call(function(sel) { sel.select('.domain').remove(); sel.selectAll('line').remove(); });

  // X axis label
  g.append('text').attr('class', 'axis-label')
    .attr('x', w / 2).attr('y', h + 42)
    .attr('text-anchor', 'middle')
    .text('Mental Health Condition');

  // ── Gradient legend ──────────────────────────────────────────────────────
  var legendH = h * 0.6;
  var legendW = 12;
  var defs = svg.append('defs');
  var grad = defs.append('linearGradient')
    .attr('id', 'hm-grad')
    .attr('x1','0').attr('x2','0').attr('y1','1').attr('y2','0');

  [2, 4, 5.5, 7, 9].forEach(function(val, i, arr) {
    grad.append('stop')
      .attr('offset', (i / (arr.length - 1) * 100) + '%')
      .attr('stop-color', colorMap(val));
  });

  var lg = g.append('g')
    .attr('transform', 'translate(' + (w + 18) + ',' + ((h - legendH) / 2) + ')');
  lg.append('rect')
    .attr('width', legendW).attr('height', legendH)
    .attr('fill', 'url(#hm-grad)').attr('rx', 3);

  var legendScale = d3.scaleLinear().domain([2, 9]).range([legendH, 0]);
  lg.append('g').attr('class', 'axis')
    .attr('transform', 'translate(' + legendW + ',0)')
    .call(d3.axisRight(legendScale).ticks(4).tickFormat(function(d) { return d.toFixed(0); }))
    .call(function(sel) {
      sel.select('.domain').remove();
      sel.selectAll('line').attr('stroke', 'var(--border)');
    });
  lg.append('text')
    .attr('x', legendW / 2).attr('y', -6)
    .attr('text-anchor', 'middle')
    .attr('font-size', 9).attr('font-family', 'DM Mono, monospace')
    .attr('fill', 'var(--muted)').text('Score');

  // ── Update function ───────────────────────────────────────────────────────
  // TRANSITION TYPE: Filtering — rows for unselected genres fade out
  heatUpdate = function(filteredData) {
    // Determine which genres appear in filtered set
    var activeGenres = d3.set(filteredData.map(function(d) { return d.genre; })).values();
    var activeSet = {};
    activeGenres.forEach(function(g) { activeSet[g] = true; });

    // Animate cell opacity — inactive genres dim (Filtering transition)
    cells.transition().duration(T_DUR)
      .attr('opacity', function(d) {
        // If there's any active filter, dim genres not in filtered set
        var hasFilter = filterState.selectedGenre || Object.keys(filterState.brushExtents).length > 0;
        if (!hasFilter) return 1;
        return activeSet[d.genre] ? 1 : 0.1;
      });

    cellTexts.transition().duration(T_DUR)
      .attr('opacity', function(d) {
        var hasFilter = filterState.selectedGenre || Object.keys(filterState.brushExtents).length > 0;
        if (!hasFilter) return 1;
        return activeSet[d.genre] ? 1 : 0.1;
      });
  };

  heatUpdate(allData);
}

// =============================================================================
// CHART 3: PARALLEL COORDINATES PLOT — Multi-dim Explorer (Focus / Advanced)
// INTERACTION: drag on any axis to brush a value range → filters all views.
// TRANSITION: lines fade in/out as brush filter changes (Filtering transition).
// =============================================================================
function drawPCP(allData) {
  var container = document.getElementById('pcp-chart');
  var W = container.clientWidth;
  var H = container.clientHeight;
  var margin = { top: 34, right: 40, bottom: 14, left: 40 };
  var w = W - margin.left - margin.right;
  var h = H - margin.top - margin.bottom;

  var svg = d3.select('#pcp-chart').append('svg')
    .attr('width', W).attr('height', H);

  var g = svg.append('g')
    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

  // One y-scale per dimension (fixed domains so axes don't rescale on filter)
  var yScales = {};
  PCP_DIMS.forEach(function(dim) {
    yScales[dim.key] = d3.scaleLinear()
      .domain(dim.domain)
      .range([h, 0])
      .clamp(true);
  });

  // X scale — evenly spaces the axes
  var xScale = d3.scalePoint()
    .domain(PCP_DIMS.map(function(d) { return d.key; }))
    .range([0, w]);

  // Dark background panel for readability
  g.append('rect')
    .attr('x', 0).attr('y', 0)
    .attr('width', w).attr('height', h)
    .attr('fill', '#0d0f14').attr('rx', 6).attr('opacity', 0.45);

  // Sample up to 350 rows so the chart stays performant
  var sample = allData.slice()
    .sort(function() { return Math.random() - 0.5; })
    .slice(0, 350);

  // Line path generator
  function lineFor(d) {
    return d3.line()(
      PCP_DIMS.map(function(dim) {
        return [xScale(dim.key), yScales[dim.key](d[dim.key])];
      })
    );
  }

  // Draw lines
  var lines = g.selectAll('.pcp-line')
    .data(sample)
    .enter().append('path')
      .attr('class', 'pcp-line')
      .attr('d', lineFor)
      .attr('stroke', function(d) { return colorScale(d.genre); })
      .on('mousemove', function(d) {
        showTip(
          '<strong>' + d.genre + '</strong><br/>' +
          'Age: ' + d.age + '<br/>' +
          'Hours/day: ' + d.hoursPerDay + '<br/>' +
          'Anxiety: ' + d.anxiety.toFixed(1) + '<br/>' +
          'Depression: ' + d.depression.toFixed(1) + '<br/>' +
          'Insomnia: ' + d.insomnia.toFixed(1) + '<br/>' +
          'OCD: ' + d.ocd.toFixed(1),
          d3.event
        );
      })
      .on('mouseleave', hideTip);

  // Draw each axis with a brush
  PCP_DIMS.forEach(function(dim) {
    var axisG = g.append('g')
      .attr('class', 'axis')
      .attr('transform', 'translate(' + xScale(dim.key) + ',0)');

    // Axis ticks
    axisG.call(d3.axisLeft(yScales[dim.key]).ticks(5))
      .call(function(sel) {
        sel.select('.domain').attr('stroke', 'var(--border)');
        sel.selectAll('line').attr('stroke', 'var(--border)');
      });

    // Axis label above axis
    axisG.append('text')
      .attr('class', 'pcp-axis-label')
      .attr('y', -18)
      .text(dim.label);

    // INTERACTION: vertical brush on each axis
    // Each brush covers a ±16px band around the axis (narrow so it's clear)
    var brushHeight = h;
    var brush = d3.brushY()
      .extent([[-16, 0], [16, brushHeight]])
      .on('brush end', function() {
        if (!d3.event.selection) {
          // Brush was cleared — remove extent for this dimension
          delete filterState.brushExtents[dim.key];
        } else {
          // Convert pixel selection to data values
          var sel = d3.event.selection;
          filterState.brushExtents[dim.key] = [
            yScales[dim.key].invert(sel[1]),   // invert: pixels → values
            yScales[dim.key].invert(sel[0])    // [1] is bottom (lower value after invert)
          ];
        }
        updateAll(allData);
      });

    // Attach brush to this axis group
    axisG.append('g')
      .attr('class', 'brush')
      .call(brush);
  });

  // Genre color legend
  var legendContainer = document.getElementById('pcp-legend');
  var presentGenres = d3.set(sample.map(function(d) { return d.genre; })).values().sort();
  presentGenres.forEach(function(genre) {
    var item = document.createElement('div');
    item.className = 'legend-item';
    item.innerHTML =
      '<div class="legend-swatch" style="background:' + colorScale(genre) + '"></div>' +
      genre;
    legendContainer.appendChild(item);
  });

  // ── Update function ───────────────────────────────────────────────────────
  // TRANSITION TYPE: Filtering — lines that fail the filter fade to near-invisible
  pcpUpdate = function(filteredData) {
    // Build a Set of the filtered rows that are in our sample
    // We match by identity using a simple index approach
    var filteredSet = {};
    filteredData.forEach(function(d) {
      // Use a composite key of rounded values as a proxy identity
      var key = d.genre + '|' + d.age + '|' + d.hoursPerDay + '|' + d.anxiety;
      filteredSet[key] = true;
    });

    // Animate line opacity (Filtering transition — consistent fade in/out)
    lines.transition().duration(T_DUR)
      .attr('opacity', function(d) {
        var hasFilter = filterState.selectedGenre ||
          Object.keys(filterState.brushExtents).length > 0;
        if (!hasFilter) return 0.35;   // no filter — default resting opacity

        // Check this sampled row against active filters directly
        var pass = true;
        if (filterState.selectedGenre && d.genre !== filterState.selectedGenre) pass = false;
        var extents = filterState.brushExtents;
        for (var k in extents) {
          if (!extents.hasOwnProperty(k)) continue;
          var ext = extents[k];
          if (ext && (d[k] < ext[0] || d[k] > ext[1])) { pass = false; break; }
        }
        return pass ? 0.82 : 0.04;   // active lines bright, inactive nearly invisible
      })
      .attr('stroke-width', function(d) {
        var hasFilter = filterState.selectedGenre ||
          Object.keys(filterState.brushExtents).length > 0;
        if (!hasFilter) return 1.2;
        var pass = true;
        if (filterState.selectedGenre && d.genre !== filterState.selectedGenre) pass = false;
        return pass ? 1.8 : 0.8;
      });
  };

  pcpUpdate(allData);
}