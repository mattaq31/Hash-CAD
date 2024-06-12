

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
