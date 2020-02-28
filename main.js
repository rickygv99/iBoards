var canvas;
var ctx;
var mouseDown = false;
var x = 0;
var y = 0;
var background;

const DRAW_RADIUS = 4;

function init() {
  canvas = document.getElementById("canvas");
  ctx = canvas.getContext("2d");

  canvas.addEventListener("mousemove", move);
  canvas.addEventListener("mousedown", down);
  window.addEventListener("mouseup", up);

  var submitButton = document.getElementById("submit");
  submitButton.addEventListener("click", submit);

  var saveButton = document.getElementById("save");
  saveButton.addEventListener("click", save);

  var clearButton = document.getElementById("clear");
  clearButton.addEventListener("click", clear);
}

function move(e) {
  var rect = canvas.getBoundingClientRect();

  var oldX = x;
  var oldY = y;
  x = e.clientX - rect.left;
  y = e.clientY - rect.top;

  if (mouseDown) {
    draw(oldX, oldY);
  }
}

function draw(oldX, oldY) {
  ctx.beginPath();
  ctx.moveTo(oldX, oldY);
  ctx.lineTo(x, y);
  ctx.lineWidth = DRAW_RADIUS;
  ctx.stroke();
  ctx.fill();
}

function down(e) {
  mouseDown = true;
}

function up(e) {
  mouseDown = false;
}

function submit(e) {

}

function save(e) {
  var saveButton = document.getElementById("save");
  saveButton.href = canvas.toDataURL();
  saveButton.download = "mypainting.png";
}

function clear(e) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(background, 0, 0, background.width, background.height,
                0, 0, canvas.width, canvas.height);
}

init();
