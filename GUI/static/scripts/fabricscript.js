

var panelwidth = document.getElementById('right-panel').getBoundingClientRect().width
var panelheight = document.getElementById('right-panel').getBoundingClientRect().height

const canvasItself = document.getElementById('main-canvas');
canvasItself.width = panelwidth - 10;
canvasItself.height = panelheight - 10;

// create a wrapper around native canvas element (with id="c")
var canvas = new fabric.Canvas('main-canvas');

// create a rectangle object
var rect = new fabric.Rect({
  left: 100,
  top: 100,
  fill: 'red',
  width: 20,
  height: 20
});

// "add" rectangle onto canvas
canvas.add(rect);





// Variables to keep track of panning
let isPanning = false;
let startX, startY;

// Event listener for panning
canvas.on('mouse:down', function(opt) {
    const evt = opt.e;
    if (evt.altKey) { // Use alt key to trigger panning
        isPanning = true;
        startX = evt.clientX;
        startY = evt.clientY;
    }
});

canvas.on('mouse:move', function(opt) {
    if (isPanning) {
        const e = opt.e;
        const deltaX = e.clientX - startX;
        const deltaY = e.clientY - startY;
        canvas.relativePan({ x: deltaX, y: deltaY });
        startX = e.clientX;
        startY = e.clientY;
    }
});

canvas.on('mouse:up', function(opt) {
    isPanning = false;
});

// Event listener for zooming
canvas.on('mouse:wheel', function(opt) {
    const delta = opt.e.deltaY;
    let zoom = canvas.getZoom();
    zoom *= 0.99 ** delta;
    if (zoom > 20) zoom = 20;
    if (zoom < 0.1) zoom = 0.1;
    canvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
    opt.e.preventDefault();
    opt.e.stopPropagation();
});

// Optional: Disable object selection during panning
canvas.on('mouse:down', function(opt) {
    if (opt.e.altKey) {
        canvas.selection = false;
    }
});

canvas.on('mouse:up', function(opt) {
    canvas.selection = true;
});
