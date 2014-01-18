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

        var xmin = d3.min(data, function(d) { return d[0]; }),
            xmax = d3.max(data, function(d) { return d[0]; }),
            ymin = d3.min(data, function(d) { return d[1]; }),
            ymax = d3.max(data, function(d) { return d[1]; }),
            xwidth = xmax - xmin, ywidth = ymax - ymin;
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

        g.selectAll("scatter-dots")
            .data(data)
            .enter().append("svg:circle")
            .attr("cx", function (d,i) { return x(d[0]); } )
            .attr("cy", function (d) { return y(d[1]); } )
            .attr("r", 1);
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
