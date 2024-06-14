///////////////////////////////
//     Global Variables!     //
///////////////////////////////

//Configure grid
var minorGridSize = 10;                 //Size of minor grid squares
var majorGridSize = 5*minorGridSize;    //Size of major grid squares
var gridStyle = 1;                      //0 for off, 1 for grid, 2 for dots

//For dragging
let dragSelectedElement = null;         //Item selected to drag
let dragOffset = { x: 0, y: 0 };        //Offset between mouse position and item position

//For adding elements
let placeRoundedX = 0;                  //Snapped position of mouse (X)
let placeRoundedY = 0;                  //Snapped posiiton of mouse (Y)


///////////////////////////////
//     Helper Functions!     //
///////////////////////////////

//Draw grid:
function drawGrid(gridGroup, width, height, style, majorSize, minorSize) {
    //Grid style: 
        //0 corresponds to no grid
        //1 corresponds to normal grid
        //2 corresponds to dot grid
    
    //First reset grid:
    gridGroup.clear()

    //Now draw the grid itself:
    if(style != 0){
        // Draw vertical lines
        //Minor
        for (var x = 0; x < width; x += minorSize) {
            let tmpLine = gridGroup.line(x, 0, x, height).stroke({ width: 0.5, color:'#000'})
            if(style==2){
                tmpLine.stroke({dasharray:`${minorSize*0.1},${minorSize*0.9}`, dashoffset:`${minorSize*0.05}`})
            }
        }

        //Major
        for (var x = 0; x < width; x += majorSize) {
            let tmpLine = gridGroup.line(x, 0, x, height).stroke({ width: 1, color:'#000' })
            if(style==2){
                tmpLine.stroke({dasharray:`${majorSize*0.05},${majorSize*0.95}`, dashoffset:`${majorSize*0.025}`})
            }
        }

        // Draw horizontal lines
        //Minor
        for (var y = 0; y < height; y += minorSize) {
            let tmpLine = gridGroup.line(0, y, width, y).stroke({ width: 0.5, color:'#000'})
            if(style==2){
                tmpLine.stroke({dasharray:`${minorSize*0.1},${minorSize*0.9}`, dashoffset:`${minorSize*0.05}`})
            }
        }

        //Major
        for (var y = 0; y < height; y += majorSize) {
            let tmpLine = gridGroup.line(0, y, width, y).stroke({ width: 1, color:'#000' })
            if(style==2){
                tmpLine.stroke({dasharray:`${majorSize*0.05},${majorSize*0.95}`, dashoffset:`${majorSize*0.025}`})
            }
        }
    }
    
    
    return gridGroup;
  }


// Check if a point is on any existing line
function isPointOnLine(drawing, x, y) {
    const lines = drawing.find('.line');
    return lines.some(line => {
      const bbox = line.bbox();
      return (
        x >= bbox.x && x <= bbox.x2 && y >= bbox.y && y <= bbox.y2
      );
    });
  }



///////////////////////////////
//       Drag and Drop       //
///////////////////////////////


//Start dragging
function startDrag(event) {
        
    dragSelectedElement = event.target.instance;

    const point = dragSelectedElement.point(event.clientX, event.clientY);
    
    dragOffset.x = point.x - dragSelectedElement.x();
    dragOffset.y = point.y - dragSelectedElement.y();

    // Add event listeners for drag and end drag
    document.addEventListener('pointermove', drag)
    document.addEventListener('pointerup', endDrag);    
  }

//Actually drag the element
function drag(event) {
    if (dragSelectedElement) {
        let point = dragSelectedElement.point(event.clientX, event.clientY) 
        point.x = point.x - dragOffset.x
        point.y = point.y - dragOffset.y
        let roundedX = Math.round(point.x/(minorGridSize))*minorGridSize ;
        let roundedY = Math.round(point.y/(minorGridSize))*minorGridSize ;   

        dragSelectedElement.move(roundedX, roundedY);
        console.log("Im moving!")
    }
}


// Function to end dragging
function endDrag() {
    
    console.log("Dragging ended!")
    dragSelectedElement = null;
    dragOffset.x = 0
    dragOffset.y = 0

    // Remove event listeners for drag and end drag
    document.removeEventListener('pointermove', drag);
    document.removeEventListener('pointerup', endDrag);
  }



  
///////////////////////////////
//         Main Code!        //
///////////////////////////////

SVG.on(document, 'DOMContentLoaded', function() {
    
    //Configure Grid
    
    var width = document.getElementById('svg-container').getBoundingClientRect().width
    var height = document.getElementById('svg-container').getBoundingClientRect().height
    var fullDrawing = SVG().addTo('#svg-container').size(width, height)
    
    //Layers
    var drawGridLayer = fullDrawing.group();
    var draw = fullDrawing.group();

    //Initialize Grid
    drawGrid(drawGridLayer, width, height, gridStyle, majorGridSize, minorGridSize)

    
    //Calibration Figures to Mark Locations
    draw.rect(100,100).attr({fill: '#f00'}).move(0.25*width,0.25*height).draggable()
    draw.rect(100,100).attr({fill: '#ff0'}).move(0.5*width,0.5*height).draggable().onClick = function() { console.log("clicked!"); };


    //Change grid configuration by radio buttons
        //Get radio buttons
        var radios = document.querySelectorAll('input[name="graphMode');

        //Add a change event listener to each radio button:
        radios.forEach(function(radio) {
            radio.addEventListener('change', function() {
                gridStyle = this.value;
                drawGrid(drawGridLayer, width, height, gridStyle, majorGridSize, minorGridSize)

            })
        })


    const svgcontainer = document.getElementById('svg-container')
    
    
    const panzoom = Panzoom(svgcontainer, {
        maxScale: 5,
        minScale: 0.25,
        contain: "outside",
      })
    
    //Turn of pan by default
    let disablePanStatus = true; 

    //Initial setup: Zoom & Pan
    setTimeout(() => {
        panzoom.pan(-width/4,-height/4);
        panzoom.setOptions({ disablePan: disablePanStatus });
        panzoom.zoom(2)
    });
    

    //Allow zoom with touchpad
    svgcontainer.parentElement.addEventListener('wheel', panzoom.zoomWithWheel)

    // Event listener to enable pan only when shift is down
    document.addEventListener('keydown', (event) => {
        if( event.key === 'Shift') {
            disablePanStatus = false;
            panzoom.setOptions({ disablePan: disablePanStatus })
        }
    });

    // Turn off pan when shift key is lifted
    document.addEventListener('keyup', (event) => {
        if( event.key === 'Shift') {
            disablePanStatus = true;
            panzoom.setOptions({ disablePan: disablePanStatus })
        }
    });
    




    const targetElement = document.getElementById('svg-container');
    
    // Event listener to track mouse movement over the target element
    targetElement.addEventListener('mousemove', (event) => {
        // Calculate mouse position relative to the element
        let selectedElement = event.target.instance;
        let mousePoints = selectedElement.point(event.clientX, event.clientY);
        
        placeRoundedX = Math.round(mousePoints.x/(minorGridSize))*minorGridSize ;
        placeRoundedY = Math.round(mousePoints.y/(minorGridSize))*minorGridSize ;
    });




    //ID counter for slat IDs
    let slatCounter = 0;

    // Event listener to print slat when mouse is pressed
    targetElement.addEventListener('pointerdown', (event) => {
        if(disablePanStatus == true){
            console.log(`Rounded mouse position - X: ${placeRoundedX}, Y: ${placeRoundedY}`);

            if(!isPointOnLine(draw, placeRoundedX, placeRoundedY)   && !isPointOnLine(draw, placeRoundedX, placeRoundedY + 32 * minorGridSize)){
                let tmpLine = draw.line(placeRoundedX, placeRoundedY, placeRoundedX, placeRoundedY + 32 * minorGridSize).stroke({ width: 3, color:'#076900' });
                tmpLine.attr('id','ID-L'+'-N' + slatCounter)
                tmpLine.attr('class',"line")
                tmpLine.attr({ 'pointer-events': 'stroke' })
                slatCounter += 1;


                //Experimental: dragging

                // Attach event listener using SVG.js method
                tmpLine.on('pointerdown', startDrag)
                
                
                

            }
            

        }        
    });







})
    

