function point(x, y) {
	this.x = arguments[0] ? arguments[0] : 0;
	this.y = arguments[1] ? arguments[1] : 0;
}
point.prototype.neg = function () {
	return new point(-this.x, -this.y);
}
point.prototype.offset = function (pt) {
	return new point(this.x + pt.x, this.y + pt.y);
}

function rect() {
	this.x = arguments[0] ? arguments[0] : 0;
	this.y = arguments[1] ? arguments[1] : 0;
	this.w = arguments[2] ? arguments[2] : 0;
	this.h = arguments[3] ? arguments[3] : 0;
}
rect.prototype.right = function () {
	return this.x + this.w;
}
rect.prototype.bottom = function () {
	return this.y + this.h;
}

function translate_by_ends(s1, l1, s2, l2, v) {
	return l2 * (v - s1) / l1 + s2;
}
function translate_by_rects(r1, r2, p) {
	return new point(
		translate_by_ends(r1.x, r1.w, r2.x, r2.w, p.x),
		translate_by_ends(r1.y, r1.h, r2.y, r2.h, p.y)
	);
}

function tick() {
	this.value = 0;
	this.text = '';
}
tick.prototype.set_date = function (date) {
	this.value = date.getTime();
	this.text = date.getFullYear().toString() + '/' + (date.getMonth() + 1).toString();
}
tick.prototype.set_num = function (v) {
	this.value = v;
	this.text = v.toString();
}

function inc_month(date) {
	if (date.getMonth() == 11) {
		return new Date(date.getFullYear() + 1, 0, 1);
	}
	return new Date(date.getFullYear(), date.getMonth() + 1, 1);
}

function get_numerical_ticks(begin, end) {
	var result = [];
	var diff = (end - begin) / 5.0, power = 1;
	if (diff < 1e-6) {
		return [];
	}
	while (diff > 10.0) {
		diff /= 10.0;
		power *= 10.0;
	}
	while (diff < 1.0) {
		diff *= 10.0;
		power /= 10.0;
	}
	diff = Math.round(diff) * power;
	for (var current = diff * Math.ceil(begin / diff); current < end; current += diff) {
		var tck = new tick();
		tck.set_num(current);
		result.push(tck);
	}
	return result;
}
function get_date_ticks(begin, end) {
	var result = [];
	console.log(begin.toString());
	console.log(end.toString());
	var resdate = new Date(begin.getFullYear(), begin.getMonth(), 1);
	console.log(begin.getFullYear());
	if (begin.getDate() > 1) {
		resdate = inc_month(resdate);
	}
	while (resdate.getTime() < end.getTime()) {
		console.log(resdate.toString());
		var tck = new tick();
		tck.set_date(resdate);
		result.push(tck);
		resdate = inc_month(resdate);
	}
	while (result.length > 8) {
		var newres = [];
		for (var i = 0; i < result.length; i += 2) {
			newres.push(result[i]);
		}
		result = newres;
	}
	return result;
}

function line() {
	this.point1 = arguments[0] ? arguments[0] : new point();
	this.point2 = arguments[1] ? arguments[1] : new point();
}

function Graph() {
	this.graphrgn = new rect();
	this.clientrgn = new rect();
	this.xtitle = '';
	this.ytitle = '';
	this.ticklength = 3;
	this.lines = [];
	this.xticks = [];
	this.yticks = [];
}
Graph.prototype.set_axes = function (axes) {
	this.graphrgn = axes;
}
Graph.prototype.set_ticks = function () {
	this.xticks = get_numerical_ticks(axes.x, axes.right());
	this.yticks = get_numerical_ticks(axes.y, axes.bottom());
}
Graph.prototype.set_client = function (crgn) {
	this.clientrgn = crgn;
}
Graph.prototype.w2c = function (pt) {
	return translate_by_rects(this.graphrgn, this.clientrgn, pt);
}
Graph.prototype.c2w = function (pt) {
	return translate_by_rects(this.clientrgn, this.graphrgn, pt);
}
Graph.prototype.render = function (canvasobj) {
	var ctx = canvasobj.getContext('2d');

	ctx.strokeStyle = 'rgb(0, 0, 0)';
	ctx.beginPath();
	ctx.moveTo(this.clientrgn.right(), this.clientrgn.y);
	ctx.lineTo(this.clientrgn.x, this.clientrgn.y);
	ctx.lineTo(this.clientrgn.x, this.clientrgn.bottom());
	for (var i = 0; i < this.xticks.length; ++i) {
		var xv = translate_by_ends(this.graphrgn.x, this.graphrgn.w, this.clientrgn.x, this.clientrgn.w, this.xticks[i].value);
		ctx.moveTo(xv, this.clientrgn.y);
		ctx.lineTo(xv, this.clientrgn.y + this.ticklength);
	}
	for (var i = 0; i < this.yticks.length; ++i) {
		var yv = translate_by_ends(this.graphrgn.y, this.graphrgn.h, this.clientrgn.y, this.clientrgn.h, this.yticks[i].value);
		ctx.moveTo(this.clientrgn.x, yv);
		ctx.lineTo(this.clientrgn.x - this.ticklength, yv);
	}
	ctx.stroke();

	ctx.fillStyle = 'rgb(0, 0, 0)';
	for (var i = 0; i < this.xticks.length; ++i) {
		var xv = translate_by_ends(this.graphrgn.x, this.graphrgn.w, this.clientrgn.x, this.clientrgn.w, this.xticks[i].value);
		xv -= ctx.measureText(this.xticks[i].text).width * 0.5;
		ctx.fillText(this.xticks[i].text, xv, this.clientrgn.y + this.ticklength + 15); // magic!
	}
	for (var i = 0; i < this.yticks.length; ++i) {
		var yv = translate_by_ends(this.graphrgn.y, this.graphrgn.h, this.clientrgn.y, this.clientrgn.h, this.yticks[i].value);
		var metrics = ctx.measureText(this.yticks[i].text);
		ctx.fillText(this.yticks[i].text, this.clientrgn.x - this.ticklength - 2 - metrics.width, yv);
	}

	ctx.strokeStyle = 'rgb(20, 50, 255)';
	ctx.beginPath();
	for (var i = 0; i < this.lines.length; ++i) {
		var curl = this.lines[i];
		var np1 = this.w2c(curl.point1), np2 = this.w2c(curl.point2);
		ctx.moveTo(np1.x, np1.y);
		ctx.lineTo(np2.x, np2.y);
	}
	ctx.stroke();
}

function int_to_date(ival) {
	return new Date(Math.floor(ival / 10000), Math.floor(ival / 100) % 100, ival % 100);
}

function get_likes_histogram(data) {
	var result = new Graph();
	result.set_axes(new rect(0, 0, data.length, data[0] * 1.2));
	result.yticks = get_numerical_ticks(result.graphrgn.y, result.graphrgn.bottom());
	for (var i = 0; i < data.length; ++i) {
		result.lines.push(new line(new point(i, 0), new point(i, data[i])));
	}
	return result;
}
function get_history_likes_graph(data) {
	var result = new Graph();
	if (data.length == 0) {
		return result;
	}
	var maxy = data[0].y;
	var lastpt = new point(int_to_date(data[0].x).getTime(), data[0].y);
	for (var i = 1; i < data.length; ++i) {
		var curpt = new point(int_to_date(data[i].x).getTime(), data[i].y);
		if (data[i].y > maxy) {
			maxy = data[i].y;
		}
		result.lines.push(new line(lastpt, curpt));
		lastpt = curpt;
	}
	var mintime = int_to_date(data[data.length - 1].x);
	var maxtime = int_to_date(data[0].x);
	result.set_axes(new rect(mintime.getTime(), 0, maxtime.getTime() - mintime.getTime(), maxy * 1.2));
	result.xticks = get_date_ticks(mintime, maxtime);
	result.yticks = get_numerical_ticks(result.graphrgn.y, result.graphrgn.bottom());
	return result;
}


var current_target = null;
function on_mouse_enter(obj) {
	current_target = obj;
	obj.hovertimer = window.setInterval(function () {
		clearInterval(obj.hovertimer);
		jQuery.ajax({
			url: '/stat',
			method: 'POST',
			data: {'data': JSON.stringify({
				'type': obj.getAttribute('data-type'),
				'index': obj.getAttribute('data-index')
			})},
			dataType: 'json',
			success: function (data) {
				if (obj == current_target) {
					var card = document.getElementById('total-suggest');
					card.style['display'] = 'block';
					var histogram = get_likes_histogram(data.histogram);
					var graph = get_history_likes_graph(data.graph);
					var canvas = document.getElementById('data');
					canvas.getContext('2d').clearRect(0, 0, 500, 1000);
					histogram.set_client(new rect(40, 350, data.histogram.length, -350));
					histogram.render(canvas);
					graph.set_client(new rect(40, 750, 250, -350));
					graph.render(canvas);
				}
			}
		});
	}, 1000, obj);
}
function on_mouse_leave(obj) {
	current_target = null;
	clearInterval(obj.hovertimer);
	delete obj.hovertimer;
}
