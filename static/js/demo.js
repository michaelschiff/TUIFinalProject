//set up
var dim = 600;
var dotSize = 8;
var center = dim/2.0;
var paper = Raphael("paper", dim, dim);

//for drawing arrows
drawArrow = function (x1, y1, x2, y2, size) {
    var angle = Math.atan2(x1-x2,y2-y1);
    angle = (angle / (2 * Math.PI)) * 360;
    var arrowPath = paper.path("M" + x2 + " " + y2 + " L" + (x2 - size) + " " + (y2 - size) + " L" + (x2 - size) + " " + (y2 + size) + " L" + x2 + " " + y2 ).rotate((90+angle),x2,y2);
    var line = paper.path("M"+x1+","+y1+"L"+x2+","+y2);
    var s = paper.set();
    s.push(arrowPath);
    s.push(line);
    return s
}

//draw the map
var mapBackground = paper.image("static/img/campus_map.gif", 0, 0, dim, dim)

//objects for the arrow attributes
var dirArrowAttrs = {stroke: "#f00", fill:"#f00", "stroke-width":3};
var themArrowAttrs = {stroke: "#00f", fill:"#00f", "stroke-width":3};

//us, the red dot and our direction arrow
var us = paper.circle(center, center, dotSize);
us.attr("fill" ,"#f00");
us.attr("stroke", "#f00");
var dirArrow = drawArrow(center, center, center, center-50, 5);
dirArrow.attr(dirArrowAttrs);

//their dot, and the arrow pointing to them
var themX = Math.floor(Math.random() * (dim-10));
var themY = Math.floor(Math.random() * (dim-10));
var them = paper.circle(themX, themY, dotSize);
them.attr("fill", "#00f");
them.attr("stroke", "#00f");
var themArrow = drawArrow(center, center, (them.attr("cx")+center)/2.0, (them.attr("cy")+center)/2.0, 5);
themArrow.attr(themArrowAttrs);

function moveHandler(dx, dy, x, y) {
    if (them.ox+dx >= 0 && them.oy+dy >= 0 && them.ox+dx <= dim && them.oy+dy <= dim) {
        them.attr({cx: them.ox+dx, cy: them.oy+dy});
        themArrow.remove();
        themArrow = drawArrow(center, center, (them.attr("cx")+center)/2.0, (them.attr("cy")+center)/2.0, 5);
        themArrow.attr(themArrowAttrs);
        us.toFront();
        $.ajax({
          type: "POST",
          url: "",
          data: {x:them.attr("cx"),y:them.attr("cy")}
        });
    }
}
function startHandler() {
    them.ox = them.attr("cx");
    them.oy = them.attr("cy");
}
function endHandler() {}

them.drag(moveHandler, startHandler, endHandler);
us.toFront();
function getGesture() {
    $.ajax({
        url: '/longpoll/',
        dataType: 'text',
        type: 'get',
        success: function(line) {
            if ( line.charCodeAt(0) == 99 ) {
                us.animate({r:50, opacity:0.5}, 100, ">");
                setTimeout('us.animate({r:dotSize, opacity:1}, 100, ">");', 100);
            } else if ( line.charCodeAt(0) == 98 ) {
                us.animate({cx:center+20}, 100, ">");
                setTimeout('us.animate({cx:center-20}, 100, ">");', 100);
                setTimeout('us.animate({cx:center+20}, 100, ">");', 200);
                setTimeout('us.animate({cx:center}, 100, ">");', 300);
            } else if ( line.charCodeAt(0) == 97 ) {
                them.animate({r:50, opacity:0.5}, 100, ">");
                setTimeout('them.animate({r:dotSize, opacity:1}, 100, ">");', 100);
            }
            setTimeout('getGesture()', 500);
        }
    });
}
getGesture();
