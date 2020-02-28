var canvas;
var ctx;
var mouseDown = false;

const DRAW_RADIUS = 8;

function init() {
  canvas = document.getElementById("canvas");
  ctx = canvas.getContext("2d");

  canvas.addEventListener("mousemove", move);
  canvas.addEventListener("mousedown", down);
  window.addEventListener("mouseup", up);

  var submitButton = document.getElementById("submit");

  var clearButton = document.getElementById("clear");
  clearButton.addEventListener("click", clear);
}

function move(e) {
  var rect = canvas.getBoundingClientRect();
  var x = e.clientX - rect.left;
  var y = e.clientY - rect.top;

  if (mouseDown) {
    draw(x, y);
  }
}

function draw(x, y) {
  ctx.beginPath();
  ctx.arc(x, y, DRAW_RADIUS, 0, 2 * Math.PI, true);
  ctx.closePath();
  ctx.fill();
}

function down(e) {
  mouseDown = true;
}

function up(e) {
  mouseDown = false;
}

function clear(e) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

init();
