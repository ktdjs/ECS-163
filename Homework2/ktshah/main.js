// ─────────────────────────────────────────────────────────────────────────────
// CONSTANTS
// ─────────────────────────────────────────────────────────────────────────────

var GENRES = [
  'Classical','Country','EDM','Folk','Gospel','Hip-Hop',
  'Jazz','K-Pop','Latin','Lofi','Metal','Pop','R&B','Rap','Rock','Video game music'
];

var CONDITIONS = ['Anxiety','Depression','Insomnia','OCD'];

// One color per genre — ordinal scale
var colorScale = d3.scaleOrdinal()
  .domain(GENRES)
  .range([
    '#c084fc','#38bdf8','#fb7185','#34d399','#fbbf24','#a78bfa',
    '#f472b6','#60a5fa','#4ade80','#f87171','#e879f9','#86efac',
    '#fde68a','#67e8f9','#fdba74','#a5f3fc'
  ]);

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

function hideTip() {
  tooltip.style.display = 'none';
}

// ─────────────────────────────────────────────────────────────────────────────
// CHART 1: BAR CHART — Genre Popularity (Overview)
// ─────────────────────────────────────────────────────────────────────────────

function drawBarChart(rawData) {
  var container = document.getElementById('bar-chart');
  var W = container.clientWidth;
  var H = container.clientHeight;
  var margin = { top: 12, right: 12, bottom: 58, left: 40 };
  var w = W - margin.left - margin.right;
  var h = H - margin.top - margin.bottom;

  // Count respondents per genre, sort descending
  var counts = d3.nest()
    .key(function(d) { return d.genre; })
    .rollup(function(v) { return v.length; })
    .entries(rawData)
    .sort(function(a, b) { return b.value - a.value; });

  var svg = d3.select('#bar-chart').append('svg')
    .attr('width', W)
    .attr('height', H);

  var g = svg.append('g')
    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

  var x = d3.scaleBand()
    .domain(counts.map(function(d) { return d.key; }))
    .range([0, w])
    .padding(0.25);

  var y = d3.scaleLinear()
    .domain([0, d3.max(counts, function(d) { return d.value; }) * 1.12])
    .range([h, 0]);

  // Dashed grid lines
  g.append('g')
    .attr('class', 'grid')
    .call(
      d3.axisLeft(y)
        .ticks(5)
        .tickSize(-w)
        .tickFormat('')
    )
    .call(function(sel) { sel.select('.domain').remove(); })
    .selectAll('line')
      .attr('stroke', '#1e2235')
      .attr('stroke-dasharray', '3,3');

  // Bars
  g.selectAll('.bar')
    .data(counts)
    .enter().append('rect')
      .attr('class', 'bar')
      .attr('x', function(d) { return x(d.key); })
      .attr('y', function(d) { return y(d.value); })
      .attr('width', x.bandwidth())
      .attr('height', function(d) { return h - y(d.value); })
      .attr('fill', function(d) { return colorScale(d.key); })
      .attr('rx', 3)
      .on('mousemove', function(d) { showTip('<strong>' + d.key + '</strong><br/>' + d.value + ' respondents', d3.event); })
      .on('mouseleave', hideTip);

  // Count labels above bars
  g.selectAll('.bar-label')
    .data(counts)
    .enter().append('text')
      .attr('x', function(d) { return x(d.key) + x.bandwidth() / 2; })
      .attr('y', function(d) { return y(d.value) - 3; })
      .attr('text-anchor', 'middle')
      .attr('fill', 'var(--muted)')
      .attr('font-size', 9)
      .attr('font-family', 'DM Mono, monospace')
      .text(function(d) { return d.value; });

  // X axis
  var xAxis = g.append('g')
    .attr('class', 'axis')
    .attr('transform', 'translate(0,' + h + ')')
    .call(d3.axisBottom(x));

  xAxis.selectAll('text')
    .attr('transform', 'rotate(-38)')
    .attr('text-anchor', 'end')
    .attr('dx', '-4')
    .attr('dy', '4');

  // Y axis
  g.append('g')
    .attr('class', 'axis')
    .call(d3.axisLeft(y).ticks(5).tickFormat(d3.format('d')))
    .call(function(sel) { sel.select('.domain').remove(); });

  // Y axis label
  g.append('text')
    .attr('class', 'axis-label')
    .attr('transform', 'rotate(-90)')
    .attr('x', -h / 2)
    .attr('y', -30)
    .attr('text-anchor', 'middle')
    .text('# Respondents');
}

// ─────────────────────────────────────────────────────────────────────────────
// CHART 2: HEATMAP — Genre × Mental Health Condition (Context)
// ─────────────────────────────────────────────────────────────────────────────

function drawHeatmap(rawData) {
  var container = document.getElementById('heatmap');
  var W = container.clientWidth;
  var H = container.clientHeight;
  var margin = { top: 12, right: 95, bottom: 60, left: 95 };
  var w = W - margin.left - margin.right;
  var h = H - margin.top - margin.bottom;

  // Get unique genres present in data (preserving GENRES order)
  var presentGenres = GENRES.filter(function(g) {
    return rawData.some(function(d) { return d.genre === g; });
  });

  // Compute average score per genre × condition
  var heatData = [];
  presentGenres.forEach(function(genre) {
    var rows = rawData.filter(function(d) { return d.genre === genre; });
    CONDITIONS.forEach(function(cond) {
      var key = cond.toLowerCase();
      var avg = d3.mean(rows, function(d) { return d[key]; });
      heatData.push({ genre: genre, cond: cond, value: avg });
    });
  });

  var svg = d3.select('#heatmap').append('svg')
    .attr('width', W)
    .attr('height', H);

  var g = svg.append('g')
    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

  var xScale = d3.scaleBand().domain(CONDITIONS).range([0, w]).padding(0.08);
  var yScale = d3.scaleBand().domain(presentGenres).range([0, h]).padding(0.06);

  var colorMap = d3.scaleSequential(
    d3.interpolateRgbBasis(['#0d0f14','#1e1040','#7c3aed','#c084fc','#fb7185'])
  ).domain([2, 9]);

  // Cells
  g.selectAll('.heatmap-cell')
    .data(heatData)
    .enter().append('rect')
      .attr('class', 'heatmap-cell')
      .attr('x', function(d) { return xScale(d.cond); })
      .attr('y', function(d) { return yScale(d.genre); })
      .attr('width', xScale.bandwidth())
      .attr('height', yScale.bandwidth())
      .attr('fill', function(d) { return colorMap(d.value); })
      .attr('rx', 3)
      .on('mousemove', function(d) {
        showTip('<strong>' + d.genre + '</strong><br/>' + d.cond + ': ' + d.value.toFixed(2) + ' avg', d3.event);
      })
      .on('mouseleave', hideTip);

  // Value labels inside cells
  g.selectAll('.cell-text')
    .data(heatData)
    .enter().append('text')
      .attr('x', function(d) { return xScale(d.cond) + xScale.bandwidth() / 2; })
      .attr('y', function(d) { return yScale(d.genre) + yScale.bandwidth() / 2 + 3; })
      .attr('text-anchor', 'middle')
      .attr('font-size', 8)
      .attr('font-family', 'DM Mono, monospace')
      .attr('fill', function(d) { return d.value > 6 ? '#fff' : 'var(--muted)'; })
      .text(function(d) { return d.value.toFixed(1); });

  // X axis (conditions)
  g.append('g')
    .attr('class', 'axis')
    .attr('transform', 'translate(0,' + h + ')')
    .call(d3.axisBottom(xScale))
    .call(function(sel) {
      sel.select('.domain').remove();
      sel.selectAll('line').remove();
    });

  // Y axis (genres)
  g.append('g')
    .attr('class', 'axis')
    .call(d3.axisLeft(yScale))
    .call(function(sel) {
      sel.select('.domain').remove();
      sel.selectAll('line').remove();
    });

  // Color legend — gradient bar on the right
  var legendH = h * 0.6;
  var legendW = 12;
  var legendX = w + 18;
  var legendY = (h - legendH) / 2;

  var defs = svg.append('defs');
  var grad = defs.append('linearGradient')
    .attr('id', 'hm-grad')
    .attr('x1', '0').attr('x2', '0')
    .attr('y1', '1').attr('y2', '0');

  [2, 4, 5.5, 7, 9].forEach(function(val, i, arr) {
    grad.append('stop')
      .attr('offset', (i / (arr.length - 1) * 100) + '%')
      .attr('stop-color', colorMap(val));
  });

  var lg = g.append('g').attr('transform', 'translate(' + legendX + ',' + legendY + ')');

  lg.append('rect')
    .attr('width', legendW)
    .attr('height', legendH)
    .attr('fill', 'url(#hm-grad)')
    .attr('rx', 3);

  var legendScale = d3.scaleLinear().domain([2, 9]).range([legendH, 0]);

  lg.append('g')
    .attr('class', 'axis')
    .attr('transform', 'translate(' + legendW + ',0)')
    .call(d3.axisRight(legendScale).ticks(4).tickFormat(function(d) { return d.toFixed(0); }))
    .call(function(sel) {
      sel.select('.domain').remove();
      sel.selectAll('line').attr('stroke', 'var(--border)');
    });

  lg.append('text')
    .attr('x', legendW / 2)
    .attr('y', -6)
    .attr('text-anchor', 'middle')
    .attr('font-size', 9)
    .attr('font-family', 'DM Mono, monospace')
    .attr('fill', 'var(--muted)')
    .text('Score');
}

// ─────────────────────────────────────────────────────────────────────────────
// CHART 3: PARALLEL COORDINATES PLOT — Multi-dim Explorer (Focus / Advanced)
// ─────────────────────────────────────────────────────────────────────────────

function drawPCP(rawData) {
  var container = document.getElementById('pcp-chart');
  var W = container.clientWidth;
  var H = container.clientHeight;
  var margin = { top: 32, right: 40, bottom: 16, left: 40 };
  var w = W - margin.left - margin.right;
  var h = H - margin.top - margin.bottom;

  var dimensions = [
    { key: 'age',         label: 'Age',        domain: [10, 90] },
    { key: 'hoursPerDay', label: 'Hours/Day',  domain: [0, 24]  },
    { key: 'anxiety',     label: 'Anxiety',    domain: [0, 10]  },
    { key: 'depression',  label: 'Depression', domain: [0, 10]  },
    { key: 'insomnia',    label: 'Insomnia',   domain: [0, 10]  },
    { key: 'ocd',         label: 'OCD',        domain: [0, 10]  }
  ];

  var svg = d3.select('#pcp-chart').append('svg')
    .attr('width', W)
    .attr('height', H);

  var g = svg.append('g')
    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

  // One y-scale per axis
  var yScales = {};
  dimensions.forEach(function(dim) {
    yScales[dim.key] = d3.scaleLinear()
      .domain(dim.domain)
      .range([h, 0])
      .clamp(true);
  });

  var xScale = d3.scalePoint()
    .domain(dimensions.map(function(d) { return d.key; }))
    .range([0, w]);

  // Dark background panel
  g.append('rect')
    .attr('x', 0).attr('y', 0)
    .attr('width', w).attr('height', h)
    .attr('fill', '#0d0f14')
    .attr('rx', 6)
    .attr('opacity', 0.45);

  // Sample up to 300 rows so the chart stays readable
  var sample = rawData.slice().sort(function() { return Math.random() - 0.5; }).slice(0, 300);

  // Draw one polyline per respondent
  g.selectAll('.pcp-line')
    .data(sample)
    .enter().append('path')
      .attr('class', 'pcp-line')
      .attr('d', function(d) {
        return d3.line()(
          dimensions.map(function(dim) {
            return [xScale(dim.key), yScales[dim.key](d[dim.key])];
          })
        );
      })
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

  // Draw each axis
  dimensions.forEach(function(dim) {
    var axisG = g.append('g')
      .attr('class', 'axis')
      .attr('transform', 'translate(' + xScale(dim.key) + ',0)');

    axisG.call(d3.axisLeft(yScales[dim.key]).ticks(5))
      .call(function(sel) {
        sel.select('.domain').attr('stroke', 'var(--border)');
        sel.selectAll('line').attr('stroke', 'var(--border)');
      });

    // Axis label above each axis
    axisG.append('text')
      .attr('class', 'pcp-axis-label')
      .attr('y', -16)
      .text(dim.label);
  });

  // Genre color legend below the PCP
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
}
