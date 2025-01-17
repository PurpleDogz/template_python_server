
////////////////////////////////////
// Metrics

function draw_metrics_chart(chart_id, chart_data, titles, chart_height, sub_chart_height) {
	
	const margin_top = {
		top: 10,
		right: 10,
		bottom: 0,
		left: 10,
	};

	const margin_middle = {
		top: 10,
		right: 10,
		bottom: 0,
		left: 10,
	};

	const margin_bottom = {
		top: 0,
		right: 10,
		bottom: 30,
		left: 10,
	};

	var chart_width = parseInt(d3.select(chart_id).style('width'), 10);

	const svg_orig = d3.select(chart_id);
	svg_orig.selectAll("*").remove();

	const tooltip = svg_orig
		.append("div")
		.style("opacity", 0)
		.attr("class", "tooltip")
		.style("position", "absolute")
		.style("background-color", "var(--bs-body-bg)")
		.style("border", "solid")
		.style("border-width", "1px")
		.style("border-radius", "5px")
		.style("padding", "10px")

	var dTypes = new Map([
		["cpu_pct", "CPU"],
		["network_in", "Network IN"],
		["network_out", "Network OUT"]
	]);

	const dt = new Set()
	dTypes.forEach((value, key) => {
		for (var i = 0; i < chart_data.length; i++) {
			if (chart_data[i][key] != null) {
				dt.add(key)
				break;
			}
		}
	});

	//console.log(dt);

	sub_chart_height = chart_height / dt.size;

	if (dt.has("cpu_pct")) {
		addchart(chart_data, dTypes, "cpu_pct", titles["cpu_pct"], chart_width, sub_chart_height, false, "steelblue", margin_top, true, 100);
	}

	if (dt.has("network_in")) {
		addchart(chart_data, dTypes, "network_in", titles["network_in"], chart_width, sub_chart_height, false, "#A569BD", margin_middle);
	}

	if (dt.has("network_out")) {
		addchart(chart_data, dTypes, "network_out", titles["network_out"], chart_width, sub_chart_height, true, "orange", margin_bottom);
	}

	function addchart(g_data, data_types, data_type, title, width, height, enable_x_axis, line_color, margin, gradient_color=false, max_y_value=null) {

		const graphWidth = width - margin.left - margin.right
		const graphHeight = height - margin.top - margin.bottom
		const svg = d3.select(chart_id)
			.append('svg')
			.attr('width', graphWidth + margin.left + margin.right)
			.attr('height', graphHeight + margin.top + margin.bottom);

		const graph = svg.append('g')
			.attr('width', graphWidth)
			.attr('height', graphHeight)
			.attr('transform', `translate(${margin.left},${margin.top})`);

		//console.log(d3.extent(g_data, function(d) { return new Date(d.timestamp); }))

		var x = d3.scaleTime()
			.domain(d3.extent(g_data, function(d) {
				return new Date(d.timestamp);
			}))
			.range([0, graphWidth]);

		var xaxis = d3.axisBottom(x).ticks(5);
		if (enable_x_axis == false) {
			xaxis.tickSizeOuter(0).tickSizeInner(0).ticks(0);
		}

		var xaxis_g = svg.append("g")
			.attr("transform", "translate(0," + graphHeight + ")")
			.call(xaxis);

		if (enable_x_axis == false) {
			xaxis_g.select(".domain")
				.attr("stroke-width", "0")
				.attr("opacity", "1");
		}

		// Add Y axis
		var y = d3.scaleLinear()
			.domain([0, max_y_value ? max_y_value : d3.max(g_data, function(d) {
				return +d[data_type];
			})])
			.range([graphHeight, 0]);

		svg.append("g")
			.call(d3.axisLeft(y))
			.append("text")
			.attr("class", "axis-title")
			.attr("transform", "rotate(-90)")
			.attr("y", 6)
			//.attr("dx", ".5em")
			.attr("dy", ".71em")
			.style("text-anchor", "end")
			.attr("fill", "#5D6971")
			.text(data_types.get(data_type));

		if ( gradient_color )
		{
			svg.append("linearGradient")
				.attr("id", "svgGradientPower")
				.attr("gradientUnits", "userSpaceOnUse")
				.attr("x1", 0)
				.attr("x2", graphWidth)
				.selectAll("stop")
				.data(g_data)
				.join("stop")
				.attr("offset", function(d) {
					return x(new Date(d.timestamp)) / graphWidth
				})
				.attr("stop-color", function(d) {
					return get_intensity_color(d[data_type]); 
				});
			line_color = "url(#svgGradientPower)";
		}

		// Add the line
		svg.append("path")
			.datum(g_data)
			.attr("fill", "none")
			.attr("stroke", line_color)
			.attr("stroke-width", 1)
			.attr("d", d3.line()
				.x(function(d) {
					return x(new Date(d.timestamp))
				})
				.y(function(d) {
					return y(d[data_type])
				})
				.defined(function(d) {
					return d[data_type] || d[data_type] == 0
				}).curve(d3.curveBasis));


			if ( title ) {
				const annotations = [
					{
					note: {
						title: title,
						wrap: 200
					},
					align: "middle",
					x: (graphWidth/2)-parseInt(title.length*3),
					y: -2,
					dy: 0,
					dx: 0,
					disable: ['connector', 'subject'],
					}
				]
				
				const makeAnnotations = d3.annotation().annotations(annotations)
				svg.append("g").call(makeAnnotations)
			}

		var hoverLineGroup = svg.append("g").attr("class", "hover-line");

		var hoverLine = hoverLineGroup
			.append("line")
			.attr("stroke", "lightgreen")
			.attr("x1", 10).attr("x2", 10)
			.attr("y1", 0).attr("y2", graphHeight);

		hoverLineGroup.style("opacity", 1e-6);

		var bisectDate = d3.bisector(function(d) {
			//console.log(new Date(d.timestamp));
			return new Date(d.timestamp);
		}).left;

		function hoverMouseOn(d) {

			var graph_y = y.invert(d.offsetY);
			var graph_x = x.invert(d.offsetX);

			var mouseDate = graph_x;

			var i = bisectDate(g_data, mouseDate);

			var d0 = g_data[i - 1]
			var d1 = g_data[i];

			var dTarget = resolveMousePoint(d0, d1, mouseDate);

			if (dTarget == null) {
				return;
			}

			var fontSize = get_tt_font_size();
			var fontSize_title = get_tt_font_title_size();
			var tableClass = get_tt_table_class();

			var tt = "<center>" + formatTime(dTarget.timestamp) + "</center>";

			tt += "<table cellpadding=\"0\" cellspacing=\"0\" class=\""+ tableClass + "\" style=\"border-spacing:0px;padding:0;margin:0;font-size:" + fontSize + "\">";

			data_types.forEach((value, key) => {

				if (dTarget[key]) {
					row_c = "table-dark";
					if (key == data_type) {
						row_c = "table-primary";
					}

					nVal =  dTarget[key] //Math.round(dTarget[key], 0)
					if ( key == "cpu_pct" )
					{
						nVal = nVal + "%";
					}
					if ( key == "network_in" || key == "network_out" )
					{
						nVal = nVal +  " MB/s";
					}

					tt += "<tr class=\"" + row_c + "\"><td>" + value + "</td><td>" + nVal + "</td></tr>";
				}
			});
			tt += "</table";

			tooltip
				.html(tt)
				.style("opacity", 1)
				.style("left", d.offsetX + calcMouseOffset(chart_id, d, 70, -160))
				.style("top", d.offsetY - 100)
				.style("visibility", "visible");

			hoverLine.attr("x1", d.offsetX + 3).attr("x2", d.offsetX + 3)
			hoverLineGroup.style("opacity", 1);
		}

		function hoverMouseOff() {
			tooltip.style("opacity", 0).style("visibility", "hidden");
			hoverLineGroup.style("opacity", 1e-6);
		}

		svg
			.on("touchstart", hoverMouseOn)
			.on("pointermove", hoverMouseOn)
			.on("pointerup lostpointercapture mouseout", hoverMouseOff);

	}
}

function draw_account_metrics_chart(chart_id, chart_data, titles, chart_height, sub_chart_height) {
	
	const margin_top = {
		top: 10,
		right: 10,
		bottom: 0,
		left: 10,
	};

	const margin_middle = {
		top: 10,
		right: 10,
		bottom: 0,
		left: 10,
	};

	const margin_bottom = {
		top: 0,
		right: 10,
		bottom: 30,
		left: 10,
	};

	var chart_width = parseInt(d3.select(chart_id).style('width'), 10);

	const svg_orig = d3.select(chart_id);
	svg_orig.selectAll("*").remove();

	const tooltip = svg_orig
		.append("div")
		.style("opacity", 0)
		.attr("class", "tooltip")
		.style("position", "absolute")
		.style("background-color", "var(--bs-body-bg)")
		.style("border", "solid")
		.style("border-width", "1px")
		.style("border-radius", "5px")
		.style("padding", "10px")

	var dTypes = new Map([
		["user_total", "Users"],
		["user_subscriber", "Subscribers"],
		["user_non_subscriber", "Non-Subscribers"],
		["user_lifetime", "Liftetime Users"],
		["user_mobile_ios", "Mobile IOS"],
		["user_mobile_android", "Mobile Android"],
		["user_browser", "Browser"]
	]);

	const dt = new Set()
	dTypes.forEach((value, key) => {
		for (var i = 0; i < chart_data.length; i++) {
			if (chart_data[i][key] != null) {
				dt.add(key)
				break;
			}
		}
	});

	//console.log(dt);

	sub_chart_height = chart_height / dt.size;

	if (dt.has("user_total")) {
		addchart(chart_data, dTypes, "user_total", "Users", chart_width, sub_chart_height, false, "steelblue", margin_top, false);
	}
	if (dt.has("user_subscriber")) {
		addchart(chart_data, dTypes, "user_subscriber", "Subscribers", chart_width, sub_chart_height, false, "green", margin_top, false);
	}
	if (dt.has("user_non_subscriber")) {
		addchart(chart_data, dTypes, "user_non_subscriber", "Non-Subscribers", chart_width, sub_chart_height, false, "orange", margin_top, false);
	}
	if (dt.has("user_lifetime")) {
		addchart(chart_data, dTypes, "user_lifetime", "Liftime Users", chart_width, sub_chart_height, false, "purple", margin_top, false);
	}
	if (dt.has("user_mobile_ios")) {
		addchart(chart_data, dTypes, "user_mobile_ios", "IOS Mobile", chart_width, sub_chart_height, false, "yellow", margin_top, false);
	}
	if (dt.has("user_mobile_android")) {
		addchart(chart_data, dTypes, "user_mobile_android", "Android Mobile", chart_width, sub_chart_height, false, "grey", margin_top, false);
	}	
	if (dt.has("user_browser")) {
		addchart(chart_data, dTypes, "user_browser", "Browser", chart_width, sub_chart_height, false, "pink", margin_top, false);
	}

	function addchart(g_data, data_types, data_type, title, width, height, enable_x_axis, line_color, margin, gradient_color=false, max_y_value=null) {

		const graphWidth = width - margin.left - margin.right
		const graphHeight = height - margin.top - margin.bottom
		const svg = d3.select(chart_id)
			.append('svg')
			.attr('width', graphWidth + margin.left + margin.right)
			.attr('height', graphHeight + margin.top + margin.bottom);

		const graph = svg.append('g')
			.attr('width', graphWidth)
			.attr('height', graphHeight)
			.attr('transform', `translate(${margin.left},${margin.top})`);

		//console.log(d3.extent(g_data, function(d) { return new Date(d.timestamp); }))

		var x = d3.scaleTime()
			.domain(d3.extent(g_data, function(d) {
				return new Date(d.timestamp);
			}))
			.range([0, graphWidth]);

		var xaxis = d3.axisBottom(x).ticks(5);
		if (enable_x_axis == false) {
			xaxis.tickSizeOuter(0).tickSizeInner(0).ticks(0);
		}

		var xaxis_g = svg.append("g")
			.attr("transform", "translate(0," + graphHeight + ")")
			.call(xaxis);

		if (enable_x_axis == false) {
			xaxis_g.select(".domain")
				.attr("stroke-width", "0")
				.attr("opacity", "1");
		}

		// Add Y axis
		var y = d3.scaleLinear()
			.domain([0, max_y_value ? max_y_value : d3.max(g_data, function(d) {
				return +d[data_type];
			})])
			.range([graphHeight, 0]);

		svg.append("g")
			.call(d3.axisLeft(y))
			.append("text")
			.attr("class", "axis-title")
			.attr("transform", "rotate(-90)")
			.attr("y", 6)
			//.attr("dx", ".5em")
			.attr("dy", ".71em")
			.style("text-anchor", "end")
			.attr("fill", "white")
			.text(data_types.get(data_type));

		if ( gradient_color )
		{
			svg.append("linearGradient")
				.attr("id", "svgGradientPower")
				.attr("gradientUnits", "userSpaceOnUse")
				.attr("x1", 0)
				.attr("x2", graphWidth)
				.selectAll("stop")
				.data(g_data)
				.join("stop")
				.attr("offset", function(d) {
					return x(new Date(d.timestamp)) / graphWidth
				})
				.attr("stop-color", function(d) {
					return get_intensity_color(d[data_type]); 
				});
			line_color = "url(#svgGradientPower)";
		}

		// Add the line
		svg.append("path")
			.datum(g_data)
			.attr("fill", "none")
			.attr("stroke", line_color)
			.attr("stroke-width", 1)
			.attr("d", d3.line()
				.x(function(d) {
					return x(new Date(d.timestamp))
				})
				.y(function(d) {
					return y(d[data_type])
				})
				.defined(function(d) {
					return d[data_type] || d[data_type] == 0
				}).curve(d3.curveBasis));


			if ( title ) {
				const annotations = [
					{
					note: {
						title: title,
						wrap: 200
					},
					align: "middle",
					x: (graphWidth/2)-parseInt(title.length*3),
					y: -2,
					dy: 0,
					dx: 0,
					disable: ['connector', 'subject'],
					}
				]
				
				const makeAnnotations = d3.annotation().annotations(annotations)
				svg.append("g").call(makeAnnotations)
			}

		var hoverLineGroup = svg.append("g").attr("class", "hover-line");

		var hoverLine = hoverLineGroup
			.append("line")
			.attr("stroke", "lightgreen")
			.attr("x1", 10).attr("x2", 10)
			.attr("y1", 0).attr("y2", graphHeight);

		hoverLineGroup.style("opacity", 1e-6);

		var bisectDate = d3.bisector(function(d) {
			//console.log(new Date(d.timestamp));
			return new Date(d.timestamp);
		}).left;

		function hoverMouseOn(d) {

			var graph_y = y.invert(d.offsetY);
			var graph_x = x.invert(d.offsetX);

			var mouseDate = graph_x;

			var i = bisectDate(g_data, mouseDate);

			var d0 = g_data[i - 1]
			var d1 = g_data[i];

			var dTarget = resolveMousePoint(d0, d1, mouseDate);

			if (dTarget == null) {
				return;
			}

			var fontSize = get_tt_font_size();
			var fontSize_title = get_tt_font_title_size();
			var tableClass = get_tt_table_class();

			var tt = "<center>" + formatDate(dTarget.timestamp) + "</center>";

			tt += "<table cellpadding=\"0\" cellspacing=\"0\" class=\""+ tableClass + "\" style=\"border-spacing:0px;padding:0;margin:0;font-size:" + fontSize + "\">";

			data_types.forEach((value, key) => {

				//if (dTarget[key]) {
					row_c = "table-dark";
					if (key == data_type) {
						row_c = "table-primary";
					}

					nVal =  dTarget[key] //Math.round(dTarget[key], 0)
					if ( nVal ) {
						tt += "<tr class=\"" + row_c + "\"><td>" + value + "</td><td>" + nVal + "</td></tr>";
					}
				//}
			});
			tt += "</table";

			tooltip
				.html(tt)
				.style("opacity", 1)
				.style("left", d.offsetX + calcMouseOffset(chart_id, d, 70, -160))
				.style("top", d.offsetY - 100)
				.style("visibility", "visible");

			hoverLine.attr("x1", d.offsetX + 3).attr("x2", d.offsetX + 3)
			hoverLineGroup.style("opacity", 1);
		}

		function hoverMouseOff() {
			tooltip.style("opacity", 0).style("visibility", "hidden");
			hoverLineGroup.style("opacity", 1e-6);
		}

		svg
			.on("touchstart", hoverMouseOn)
			.on("pointermove", hoverMouseOn)
			.on("pointerup lostpointercapture mouseout", hoverMouseOff);

	}
}

function draw_data_metrics_chart(chart_id, chart_data, titles, chart_height, sub_chart_height) {
	
	const margin_top = {
		top: 10,
		right: 10,
		bottom: 0,
		left: 10,
	};

	const margin_middle = {
		top: 10,
		right: 10,
		bottom: 0,
		left: 10,
	};

	const margin_bottom = {
		top: 0,
		right: 10,
		bottom: 30,
		left: 10,
	};

	var chart_width = parseInt(d3.select(chart_id).style('width'), 10);

	const svg_orig = d3.select(chart_id);
	svg_orig.selectAll("*").remove();

	const tooltip = svg_orig
		.append("div")
		.style("opacity", 0)
		.attr("class", "tooltip")
		.style("position", "absolute")
		.style("background-color", "var(--bs-body-bg)")
		.style("border", "solid")
		.style("border-width", "1px")
		.style("border-radius", "5px")
		.style("padding", "10px")

	var dTypes = new Map([
		["activity_count", "Activities"],
		["db_size_mb_evandus", "Evander DB Size"],
		["db_size_mb_evandus_cache", "Cache DB Size"],
		["db_size_mb_evandus_datastore", "Datastore DB Size"]
	]);

	const dt = new Set()
	dTypes.forEach((value, key) => {
		for (var i = 0; i < chart_data.length; i++) {
			if (chart_data[i][key] != null) {
				dt.add(key)
				break;
			}
		}
	});

	//console.log(dt);

	sub_chart_height = chart_height / dt.size;

	if (dt.has("activity_count")) {
		addchart(chart_data, dTypes, "activity_count", "Activities", chart_width, sub_chart_height, false, "steelblue", margin_top, false);
	}
	if (dt.has("db_size_mb_evandus")) {
		addchart(chart_data, dTypes, "db_size_mb_evandus", "Evander DB Size", chart_width, sub_chart_height, false, "green", margin_top, false);
	}
	if (dt.has("db_size_mb_evandus_cache")) {
		addchart(chart_data, dTypes, "db_size_mb_evandus_cache", "Cache DB Size", chart_width, sub_chart_height, false, "orange", margin_top, false);
	}
	if (dt.has("db_size_mb_evandus_datastore")) {
		addchart(chart_data, dTypes, "db_size_mb_evandus_datastore", "Datastore DB Size", chart_width, sub_chart_height, false, "purple", margin_top, false);
	}

	function addchart(g_data, data_types, data_type, title, width, height, enable_x_axis, line_color, margin, gradient_color=false, max_y_value=null) {

		const graphWidth = width - margin.left - margin.right
		const graphHeight = height - margin.top - margin.bottom
		const svg = d3.select(chart_id)
			.append('svg')
			.attr('width', graphWidth + margin.left + margin.right)
			.attr('height', graphHeight + margin.top + margin.bottom);

		const graph = svg.append('g')
			.attr('width', graphWidth)
			.attr('height', graphHeight)
			.attr('transform', `translate(${margin.left},${margin.top})`);

		//console.log(d3.extent(g_data, function(d) { return new Date(d.timestamp); }))

		var x = d3.scaleTime()
			.domain(d3.extent(g_data, function(d) {
				return new Date(d.timestamp);
			}))
			.range([0, graphWidth]);

		var xaxis = d3.axisBottom(x).ticks(5);
		if (enable_x_axis == false) {
			xaxis.tickSizeOuter(0).tickSizeInner(0).ticks(0);
		}

		var xaxis_g = svg.append("g")
			.attr("transform", "translate(0," + graphHeight + ")")
			.call(xaxis);

		if (enable_x_axis == false) {
			xaxis_g.select(".domain")
				.attr("stroke-width", "0")
				.attr("opacity", "1");
		}

		// Add Y axis
		var y = d3.scaleLinear()
			.domain([0, max_y_value ? max_y_value : d3.max(g_data, function(d) {
				return +d[data_type];
			})])
			.range([graphHeight, 0]);

		svg.append("g")
			.call(d3.axisLeft(y))
			.append("text")
			.attr("class", "axis-title")
			.attr("transform", "rotate(-90)")
			.attr("y", 6)
			//.attr("dx", ".5em")
			.attr("dy", ".71em")
			.style("text-anchor", "end")
			.attr("fill", "white")
			.text(data_types.get(data_type));

		if ( gradient_color )
		{
			svg.append("linearGradient")
				.attr("id", "svgGradientPower")
				.attr("gradientUnits", "userSpaceOnUse")
				.attr("x1", 0)
				.attr("x2", graphWidth)
				.selectAll("stop")
				.data(g_data)
				.join("stop")
				.attr("offset", function(d) {
					return x(new Date(d.timestamp)) / graphWidth
				})
				.attr("stop-color", function(d) {
					return get_intensity_color(d[data_type]); 
				});
			line_color = "url(#svgGradientPower)";
		}

		// Add the line
		svg.append("path")
			.datum(g_data)
			.attr("fill", "none")
			.attr("stroke", line_color)
			.attr("stroke-width", 1)
			.attr("d", d3.line()
				.x(function(d) {
					return x(new Date(d.timestamp))
				})
				.y(function(d) {
					return y(d[data_type])
				})
				.defined(function(d) {
					return d[data_type] || d[data_type] == 0
				}).curve(d3.curveBasis));


			if ( title ) {
				const annotations = [
					{
					note: {
						title: title,
						wrap: 200
					},
					align: "middle",
					x: (graphWidth/2)-parseInt(title.length*3),
					y: -2,
					dy: 0,
					dx: 0,
					disable: ['connector', 'subject'],
					}
				]
				
				const makeAnnotations = d3.annotation().annotations(annotations)
				svg.append("g").call(makeAnnotations)
			}

		var hoverLineGroup = svg.append("g").attr("class", "hover-line");

		var hoverLine = hoverLineGroup
			.append("line")
			.attr("stroke", "lightgreen")
			.attr("x1", 10).attr("x2", 10)
			.attr("y1", 0).attr("y2", graphHeight);

		hoverLineGroup.style("opacity", 1e-6);

		var bisectDate = d3.bisector(function(d) {
			//console.log(new Date(d.timestamp));
			return new Date(d.timestamp);
		}).left;

		function hoverMouseOn(d) {

			var graph_y = y.invert(d.offsetY);
			var graph_x = x.invert(d.offsetX);

			var mouseDate = graph_x;

			var i = bisectDate(g_data, mouseDate);

			var d0 = g_data[i - 1]
			var d1 = g_data[i];

			var dTarget = resolveMousePoint(d0, d1, mouseDate);

			if (dTarget == null) {
				return;
			}

			var fontSize = get_tt_font_size();
			var fontSize_title = get_tt_font_title_size();
			var tableClass = get_tt_table_class();

			var tt = "<center>" + formatDate(dTarget.timestamp) + "</center>";

			tt += "<table cellpadding=\"0\" cellspacing=\"0\" class=\""+ tableClass + "\" style=\"border-spacing:0px;padding:0;margin:0;font-size:" + fontSize + "\">";

			data_types.forEach((value, key) => {

				//if (dTarget[key]) {
					row_c = "table-dark";
					if (key == data_type) {
						row_c = "table-primary";
					}

					nVal =  dTarget[key] //Math.round(dTarget[key], 0)
					if ( nVal ) {
						tt += "<tr class=\"" + row_c + "\"><td>" + value + "</td><td>" + nVal + "</td></tr>";
					}
				//}
			});
			tt += "</table";

			tooltip
				.html(tt)
				.style("opacity", 1)
				.style("left", d.offsetX + calcMouseOffset(chart_id, d, 70, -160))
				.style("top", d.offsetY - 100)
				.style("visibility", "visible");

			hoverLine.attr("x1", d.offsetX + 3).attr("x2", d.offsetX + 3)
			hoverLineGroup.style("opacity", 1);
		}

		function hoverMouseOff() {
			tooltip.style("opacity", 0).style("visibility", "hidden");
			hoverLineGroup.style("opacity", 1e-6);
		}

		svg
			.on("touchstart", hoverMouseOn)
			.on("pointermove", hoverMouseOn)
			.on("pointerup lostpointercapture mouseout", hoverMouseOff);

	}
}

function toFormat(v) {
	return moment(v).format("YYYY-MM-DDT00:00:00");
}

Date.prototype.addDays = function(days) {
    var date = new Date(this.valueOf());
    date.setDate(date.getDate() + days);
    return date;
}

function fillInDayBasedGaps(dates, start, end) {
	// Initialize the result array.
	//result = [];
  
	// Iterate over the dates in the range.
	for (let date = start; date <= end; date = date.addDays(1)) {
	  // Check if the date is already in the array.
	  let index = dates.findIndex((item) => new Date(item.timestamp).getTime() === date.getTime());
  
	  // If the date is not in the array, add it.
	  if (index === -1) {
		dates.push({ "timestamp" : toFormat(date), "count" : 0 });
	  }
	}

	//result = dates + result;

	function compareDates(date1, date2) {
		return new Date(date1.timestamp).getTime() - new Date(date2.timestamp).getTime();
	  }

	  dates.sort(compareDates);
  
	// Return the result array.
	return dates;
}

function draw_activity_chart(chart_id, chart_data, chart_height) {
	
	const margin_top = {
		top: 10,
		right: 10,
		bottom: 0,
		left: 10,
	};

	const margin_middle = {
		top: 10,
		right: 10,
		bottom: 0,
		left: 10,
	};

	const margin_bottom = {
		top: 0,
		right: 10,
		bottom: 30,
		left: 10,
	};

	var chart_width = parseInt(d3.select(chart_id).style('width'), 10);

	const svg_orig = d3.select(chart_id);
	svg_orig.selectAll("*").remove();

	const tooltip = svg_orig
		.append("div")
		.style("opacity", 0)
		.attr("class", "tooltip")
		.style("position", "absolute")
		.style("background-color", "var(--bs-body-bg)")
		.style("border", "solid")
		.style("border-width", "1px")
		.style("border-radius", "5px")
		.style("padding", "10px")

	var dTypes = new Map([
		["cpu_pct", "CPU"],
		["network_in", "Network IN"],
		["network_out", "Network OUT"]
	]);

	const dt = new Set()
	dt.add("count")

	sub_chart_height = chart_height / dt.size;

	addchart(chart_data, dTypes, "count", null, chart_width, sub_chart_height, false, "steelblue", margin_top, true);

	function addchart(g_data, data_types, data_type, title, width, height, enable_x_axis, line_color, margin, gradient_color=false, max_y_value=null) {

		const graphWidth = width - margin.left - margin.right
		const graphHeight = height - margin.top - margin.bottom
		const svg = d3.select(chart_id)
			.append('svg')
			.attr('width', graphWidth + margin.left + margin.right)
			.attr('height', graphHeight + margin.top + margin.bottom);

		const graph = svg.append('g')
			.attr('width', graphWidth)
			.attr('height', graphHeight)
			.attr('transform', `translate(${margin.left},${margin.top})`);

		//console.log(d3.extent(g_data, function(d) { return new Date(d.timestamp); }))

		/*
		var x = d3.scaleTime()
			.domain(d3.extent(g_data, function(d) {
				return new Date(d.timestamp);
			}))
			.range([0, graphWidth]);

		var xaxis = d3.axisBottom(x).ticks(5);
		if (enable_x_axis == false) {
			xaxis.tickSizeOuter(0).tickSizeInner(0).ticks(0);
		}

		var xaxis_g = svg.append("g")
			.attr("transform", "translate(0," + graphHeight + ")")
			.call(xaxis);

		if (enable_x_axis == false) {
			xaxis_g.select(".domain")
				.attr("stroke-width", "0")
				.attr("opacity", "1");
		}
		*/

		//console.log(g_data)

		var extent = d3.extent(g_data, function(d) { return new Date(d.timestamp);});
		//console.log(g_data)

		fillInDayBasedGaps(g_data, extent[0], extent[1]);

		//console.log(g_data)

		const groups = g_data.map(d => d.timestamp)

		const x = d3.scaleBand()
		.domain(groups)
		.range([0, graphWidth])
		.padding([0.2])

		// const xAxis = svg.append("g")
		// .attr("transform", `translate(0,${graphHeight})`).attr("class", "axisWhite")
		// .call(d3.axisBottom(x));


		// Add Y axis
		var y = d3.scaleLinear()
			.domain([0, max_y_value ? max_y_value : d3.max(g_data, function(d) {
				return +d[data_type];
			})])
			.range([graphHeight+0.5, 0]);

		// svg.append("g")
		// 	.call(d3.axisLeft(y))
		// 	.append("text")
		// 	.attr("class", "axis-title")
		// 	.attr("transform", "rotate(-90)")
		// 	.attr("y", 6)
		// 	//.attr("dx", ".5em")
		// 	.attr("dy", ".71em")
		// 	.style("text-anchor", "end")
		// 	.attr("fill", "#5D6971")
		// 	.text(data_types.get(data_type));

		const u = svg.selectAll("rect").data(g_data)

			/*
		if ( gradient_color )
		{
			svg.append("linearGradient")
				.attr("id", "svgGradientPower")
				.attr("gradientUnits", "userSpaceOnUse")
				.attr("x1", 0)
				.attr("x2", graphWidth)
				.selectAll("stop")
				.data(g_data)
				.join("stop")
				.attr("offset", function(d) {
					return x(new Date(d.timestamp)) / graphWidth
				})
				.attr("stop-color", function(d) {
					return get_intensity_color(d[data_type]); 
				});
			line_color = "url(#svgGradientPower)";
		}

		// Add the line
		svg.append("path")
			.datum(g_data)
			.attr("fill", "none")
			.attr("stroke", line_color)
			.attr("stroke-width", 1)
			.attr("d", d3.line()
				.x(function(d) {
					return x(new Date(d.timestamp))
				})
				.y(function(d) {
					return y(d[data_type])
				})
				.defined(function(d) {
					return d[data_type] || d[data_type] == 0
				}).curve(d3.curveBasis));

			*/


		if ( title ) {
			const annotations = [
				{
				note: {
					title: title,
					wrap: 200
				},
				align: "middle",
				x: (graphWidth/2)-parseInt(title.length*3),
				y: -2,
				dy: 0,
				dx: 0,
				disable: ['connector', 'subject'],
				}
			]
			
			const makeAnnotations = d3.annotation().annotations(annotations)
			svg.append("g").call(makeAnnotations)
		}

		function mapXLocation(event, rect) {
			var xoffset = 80;

			//console.log(event.offsetX)
			//console.log(rect.width / 2)


			if (event.offsetX > (rect.width / 2)) {
				xoffset = -220;
			}
			return event.offsetX + xoffset;
		}

		function mapYLocation(event, rect) {
			var yoffset = -60;
			return event.offsetY + yoffset;
		}

		const mouseover = function(event, d) {

			var fontSize = get_tt_font_size();
			var fontSize_title = get_tt_font_title_size();
			var tableClass = get_tt_table_class();

			var tt = "<center>" + formatDate(d.timestamp) + "</center>";
			tt += "<center>" + d.count + "</center>";

			// tt += "<table cellpadding=\"0\" cellspacing=\"0\" class=\""+ tableClass + "\" style=\"border-spacing:0px;padding:0;margin:0;font-size:" + fontSize + "\">";

			// data_types.forEach((value, key) => {

			// 	if (dTarget[key]) {
			// 		row_c = "table-dark";
			// 		if (key == data_type) {
			// 			row_c = "table-primary";
			// 		}

			// 		nVal =  dTarget[key] //Math.round(dTarget[key], 0)
			// 		if ( key == "cpu_pct" )
			// 		{
			// 			nVal = nVal + "%";
			// 		}
			// 		if ( key == "network_in" || key == "network_out" )
			// 		{
			// 			nVal = nVal +  " MB/s";
			// 		}

			// 		tt += "<tr class=\"" + row_c + "\"><td>" + value + "</td><td>" + nVal + "</td></tr>";
			// 	}
			// });
			// tt += "</table";

			let rect = svg.node().getBBox();
			var xoffset = mapXLocation(event, rect);
			var yoffset = mapYLocation(event, rect);
			tooltip
				.html(tt)
				.style("left", xoffset)
				.style("top", yoffset)
				.style("opacity", 1)
				.style("visibility", "visible");
		}

		const mousemove = function(event, d) {

			let rect = svg.node().getBBox();
			
			var xoffset = mapXLocation(event, rect);
			var yoffset = mapYLocation(event, rect);

			tooltip
				.style("left", xoffset)
				.style("top", yoffset)
				.style("opacity", 1)
			    .style("visibility", "visible");
		}
		const mouseleave = function(event, d) {

			tooltip
			.style("opacity", 0)
			.style("visibility", "hidden");
		}

		
		u.join("rect")
			.attr("x", d => x(d.timestamp))
			.attr("y", d => y(d.count))
			.attr("width", x.bandwidth())
			.attr("height", d => (height - y(d.count)))
			//.style("opacity", 0.75)
			//.attr("fill", "url(#lightstripe)")
			.attr("fill", function(d) { 
				return line_color;
			})
			.on("mouseover", mouseover)
			.on("mousemove", mousemove)
			.on("mouseleave", mouseleave);
	}
}

///////////////////////////////////
// Metrics

function draw_api_metrics_chart(chart_id, chart_data, titles, chart_height, sub_chart_height) {
	
	const margin_top = {
		top: 10,
		right: 10,
		bottom: 0,
		left: 10,
	};

	const margin_middle = {
		top: 10,
		right: 10,
		bottom: 0,
		left: 10,
	};

	const margin_bottom = {
		top: 0,
		right: 10,
		bottom: 30,
		left: 10,
	};

	var chart_width = parseInt(d3.select(chart_id).style('width'), 10);

	const svg_orig = d3.select(chart_id);
	svg_orig.selectAll("*").remove();

	const tooltip = svg_orig
		.append("div")
		.style("opacity", 0)
		.attr("class", "tooltip")
		.style("position", "absolute")
		.style("background-color", "var(--bs-body-bg)")
		.style("border", "solid")
		.style("border-width", "1px")
		.style("border-radius", "5px")
		.style("padding", "10px")

	var dTypes = new Map([
		["short_usage", "Short Usage"],
		["long_usage", "Long Usage"]
	]);

	const dt = new Set()
	dTypes.forEach((value, key) => {
		for (var i = 0; i < chart_data.length; i++) {
			if (chart_data[i][key] != null) {
				dt.add(key)
				break;
			}
		}
	});

	if (!chart_data[0])
	{
		return;
	}

	short_limit = chart_data[0].short_limit;
	long_limit = chart_data[0].long_limit;

	//console.log(dt);

	sub_chart_height = chart_height / dt.size;

	if (dt.has("short_usage")) {
		addchart(chart_data, dTypes, "short_usage", "Short Usage [Limit=" + short_limit +"]", chart_width, sub_chart_height, false, "steelblue", margin_top, true, short_limit);
	}

	if (dt.has("long_usage")) {
		addchart(chart_data, dTypes, "long_usage", "Long Usage [Limit=" + long_limit +"]", chart_width, sub_chart_height, false, "#A569BD", margin_bottom, true, long_limit);
	}

	function addchart(g_data, data_types, data_type, title, width, height, enable_x_axis, line_color, margin, gradient_color=false, max_y_value=null) {

		const graphWidth = width - margin.left - margin.right
		const graphHeight = height - margin.top - margin.bottom
		const svg = d3.select(chart_id)
			.append('svg')
			.attr('width', graphWidth + margin.left + margin.right)
			.attr('height', graphHeight + margin.top + margin.bottom);

		const graph = svg.append('g')
			.attr('width', graphWidth)
			.attr('height', graphHeight)
			.attr('transform', `translate(${margin.left},${margin.top})`);

		console.log(d3.extent(g_data, function(d) { return new Date(d.timestamp); }))

		var x = d3.scaleTime()
			.domain(d3.extent(g_data, function(d) {
				return new Date(d.timestamp);
			}))
			.range([0, graphWidth]);

		var xaxis = d3.axisBottom(x).ticks(5);
		if (enable_x_axis == false) {
			xaxis.tickSizeOuter(0).tickSizeInner(0).ticks(0);
		}

		var xaxis_g = svg.append("g")
			.attr("transform", "translate(0," + graphHeight + ")")
			.call(xaxis);

		if (enable_x_axis == false) {
			xaxis_g.select(".domain")
				.attr("stroke-width", "0")
				.attr("opacity", "1");
		}

		// Add Y axis
		var y = d3.scaleLinear()
			.domain([0, max_y_value ? max_y_value : d3.max(g_data, function(d) {
				return +d[data_type];
			})])
			.range([graphHeight, 0]);

		svg.append("g")
			.call(d3.axisLeft(y))
			.append("text")
			.attr("class", "axis-title")
			.attr("transform", "rotate(-90)")
			.attr("y", 6)
			//.attr("dx", ".5em")
			.attr("dy", ".71em")
			.style("text-anchor", "end")
			.attr("fill", "#5D6971")
			.text(data_types.get(data_type));

		if ( gradient_color )
		{
			svg.append("linearGradient")
				.attr("id", "svgGradientPower")
				.attr("gradientUnits", "userSpaceOnUse")
				.attr("x1", 0)
				.attr("x2", graphWidth)
				.selectAll("stop")
				.data(g_data)
				.join("stop")
				.attr("offset", function(d) {
					return x(new Date(d.timestamp)) / graphWidth
				})
				.attr("stop-color", function(d) {
					return get_intensity_color(d[data_type], max_y_value == null ? 1 : max_y_value ); 
				});
			line_color = "url(#svgGradientPower)";
		}

		// Add the line
		svg.append("path")
			.datum(g_data)
			.attr("fill", "none")
			.attr("stroke", line_color)
			.attr("stroke-width", 1)
			.attr("d", d3.line()
				.x(function(d) {
					return x(new Date(d.timestamp))
				})
				.y(function(d) {
					return y(d[data_type])
				})
				.defined(function(d) {
					return d[data_type] || d[data_type] == 0
				}).curve(d3.curveBasis));


			if ( title ) {
				const annotations = [
					{
					note: {
						title: title,
						wrap: 200
					},
					align: "middle",
					x: (graphWidth/2)-parseInt(title.length*3),
					y: -2,
					dy: 0,
					dx: 0,
					disable: ['connector', 'subject'],
					}
				]
				
				const makeAnnotations = d3.annotation().annotations(annotations)
				svg.append("g").call(makeAnnotations)
			}

		var hoverLineGroup = svg.append("g").attr("class", "hover-line");

		var hoverLine = hoverLineGroup
			.append("line")
			.attr("stroke", "lightgreen")
			.attr("x1", 10).attr("x2", 10)
			.attr("y1", 0).attr("y2", graphHeight);

		hoverLineGroup.style("opacity", 1e-6);

		var bisectDate = d3.bisector(function(d) {
			//console.log(new Date(d.timestamp));
			return new Date(d.timestamp);
		}).left;

		function hoverMouseOn(d) {

			var graph_y = y.invert(d.offsetY);
			var graph_x = x.invert(d.offsetX);

			var mouseDate = graph_x;

			var i = bisectDate(g_data, mouseDate);

			var d0 = g_data[i - 1]
			var d1 = g_data[i];

			var dTarget = resolveMousePoint(d0, d1, mouseDate);

			if (dTarget == null) {
				return;
			}

			var fontSize = get_tt_font_size();
			var fontSize_title = get_tt_font_title_size();
			var tableClass = get_tt_table_class();

			var tt = "<center>" + formatDatePlusTimeFromUTC(dTarget.timestamp) + "</center>";

			tt += "<table cellpadding=\"0\" cellspacing=\"0\" class=\""+ tableClass + "\" style=\"border-spacing:0px;padding:0;margin:0;font-size:" + fontSize + "\">";

			data_types.forEach((value, key) => {

				if (dTarget[key]) {
					row_c = "table-dark";
					if (key == data_type) {
						row_c = "table-primary";
					}

					nVal =  dTarget[key] //Math.round(dTarget[key], 0)
					if ( key == "cpu_pct" )
					{
						nVal = nVal + "%";
					}
					if ( key == "network_in" || key == "network_out" )
					{
						nVal = nVal +  " MB/s";
					}

					tt += "<tr class=\"" + row_c + "\"><td>" + value + "</td><td>" + nVal + "</td></tr>";
				}
			});
			tt += "</table";

			tooltip
				.html(tt)
				.style("opacity", 1)
				.style("left", d.offsetX + calcMouseOffset(chart_id, d, 70, -160))
				.style("top", d.offsetY - 100)
				.style("visibility", "visible");

			hoverLine.attr("x1", d.offsetX + 3).attr("x2", d.offsetX + 3)
			hoverLineGroup.style("opacity", 1);
		}

		function hoverMouseOff() {
			tooltip.style("opacity", 0).style("visibility", "hidden");
			hoverLineGroup.style("opacity", 1e-6);
		}

		svg
			.on("touchstart", hoverMouseOn)
			.on("pointermove", hoverMouseOn)
			.on("pointerup lostpointercapture mouseout", hoverMouseOff);

	}
}