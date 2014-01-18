var d3plot = {};

(function () {

    var margin = {top: 5, right: 5, bottom: 5, left: 5};

    d3plot = function (element, data) {

        var $el = $(element);

        var width = $el.width(),
            height = $el.height(),
            innerWidth = width - (margin.left + margin.right),
            innerHeight = height - (margin.top + margin.bottom);
        console.log(data);

        // ugh!
        var xmin = d3.min(data[0], function(d) { return d[0]; }),
            xmax = d3.max(data[0], function(d) { return d[0]; }),
            ymin = d3.min(data[0], function(d) { return d[1]; }),
            ymax = d3.max(data[0], function(d) { return d[1]; }),
            wlmax = d3.max(data[0], function(d) { return d[2]; }),
            wlmin = d3.max(data[0], function(d) { return d[2]; });
        for (var i in data) {
            xmin = Math.min(xmin, d3.min(data[i], function(d) { return d[0]; })),
            xmax = Math.max(xmax, d3.max(data[i], function(d) { return d[0]; })),
            ymin = Math.min(ymin, d3.min(data[i], function(d) { return d[1]; })),
            ymax = Math.max(ymax, d3.max(data[i], function(d) { return d[1]; }));
            wlmax = Math.max(wlmax, d3.max(data[i], function(d) { return d[2]; }));
            wlmin = Math.min(wlmax, d3.min(data[i], function(d) { return d[2]; }));
        }

        var xwidth = xmax - xmin, ywidth = ymax - ymin;
        if (xwidth === 0)
            xwidth = 1;
        if (ywidth === 0)
            ywidth = 1;

        var x = d3.scale.linear()
                .domain([xmin - 0.1 * xwidth, xmax + 0.1 * xwidth])
                .range([innerWidth*0.05, innerWidth*0.95]);

        var y = d3.scale.linear()
                .domain([ymin - 0.1 * ywidth, ymax + 0.1 * ywidth])
    	        .range([innerHeight*0.95, innerHeight*0.05]);

        var chart = d3.select(element)
	        .append('svg:svg')
	        .attr('width', width)
	        .attr('height', height )
	        .attr('class', 'chart');

        var main = chart.append('g')
	        .attr('transform',
                      'translate(' + margin.left + ',' + margin.top + ')')
	        .attr('width', innerWidth)
	        .attr('height', innerHeight)
	        .attr('class', 'plot');

        // draw the x axis
        var xAxis = d3.svg.axis()
	        .scale(x)
	        .orient('top')
                .ticks(5, "s");

        main.append('g')
	    .attr('transform', 'translate(0,' + innerHeight + ')')
	    .attr('class', 'plot axis')
	    .call(xAxis);

        // draw the y axis
        var yAxis = d3.svg.axis()
	        .scale(y)
	        .orient('right')
                .ticks(5, "s");

        main.append('g')
	    .attr('transform', 'translate(0,0)')
	    .attr('class', 'plot axis')
	    .call(yAxis);

        var g = main.append("svg:g");

        var colors = ["red", "violet", "blue"];
        var colorscale = d3.scale.linear()
                .domain([0, colors.length - 1])
                .range([wlmin, wlmax]);
        var color = d3.scale.linear()
                .domain(d3.range(colors.length).map(colorscale))
                .range(colors);

        for (i in data) {
            g.selectAll("scatter-dots-" + i)
                .data(data[i])
                .enter().append("svg:circle")
                .attr("cx", function (d,i) { return x(d[0]); } )
                .attr("cy", function (d) { return y(d[1]); } )
                .attr("r", 1)
                .attr("fill", function (d) {return color(d[2]);});
        }
    };

    var debounce = function(fn, timeout) {
        var timeoutID = -1;
        return function() {
            if (timeoutID > -1) {
                window.clearTimeout(timeoutID);
            }
            timeoutID = window.setTimeout(fn, timeout);
        };
    };

})();
