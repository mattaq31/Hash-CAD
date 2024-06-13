
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



SVG.on(document, 'DOMContentLoaded', function() {
    
    

    //Configure Grid
    var minorGridSize = 10; // size of the grid squares
    var majorGridSize = 5*minorGridSize;
    var gridStyle = 2; //0 for off, 1 for grid, 2 for dots
    var width = document.getElementById('svg-container').getBoundingClientRect().width
    var height = document.getElementById('svg-container').getBoundingClientRect().height
    
    var fullDrawing = SVG().addTo('#svg-container').size(width, height)
    
    var drawGridLayer = fullDrawing.group();
    var draw = fullDrawing.group();

    
    //Calibration Figures to Mark Locations
    draw.rect(100,100).attr({fill: '#f00'}).move(0.25*width,0.25*height)
    draw.rect(100,100).attr({fill: '#ff0'}).move(0.5*width,0.5*height)


    var radios = document.querySelectorAll('input[name="graphMode');

    //Add a change event listener to each radio button:
    radios.forEach(function(radio) {
        radio.addEventListener('change', function() {
            gridStyle = this.value;
            drawGrid(drawGridLayer, width, height, gridStyle, majorGridSize, minorGridSize)

        })
    })

    //drawGrid(drawGridLayer, width, height, gridStyle, majorGridSize, minorGridSize)

    
/*
    //Drawing the grid itself:
    if(gridStyle != 0){
        // Draw vertical lines
        //Minor
        for (var x = 0; x < width; x += minorGridSize) {
            let tmpLine = drawGridLayer.line(x, 0, x, height).stroke({ width: 0.5, color:'#000'})
            if(gridStyle==2){
                tmpLine.stroke({dasharray:`${minorGridSize*0.1},${minorGridSize*0.9}`, dashoffset:`${minorGridSize*0.05}`})
            }
        }

        //Major
        for (var x = 0; x < width; x += majorGridSize) {
            let tmpLine = drawGridLayer.line(x, 0, x, height).stroke({ width: 1, color:'#000' })
            if(gridStyle==2){
                tmpLine.stroke({dasharray:`${majorGridSize*0.05},${majorGridSize*0.95}`, dashoffset:`${majorGridSize*0.025}`})
            }
        }

        // Draw horizontal lines
        //Minor
        for (var y = 0; y < height; y += minorGridSize) {
            let tmpLine = drawGridLayer.line(0, y, width, y).stroke({ width: 0.5, color:'#000'})
            if(gridStyle==2){
                tmpLine.stroke({dasharray:`${minorGridSize*0.1},${minorGridSize*0.9}`, dashoffset:`${minorGridSize*0.05}`})
            }
        }

        //Major
        for (var y = 0; y < height; y += majorGridSize) {
            let tmpLine = drawGridLayer.line(0, y, width, y).stroke({ width: 1, color:'#000' })
            if(gridStyle==2){
                tmpLine.stroke({dasharray:`${majorGridSize*0.05},${majorGridSize*0.95}`, dashoffset:`${majorGridSize*0.025}`})
            }
        }
    }
*/


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
    let mouseX = 0;
    let mouseY = 0;

    let roundedX = 0;
    let roundedY = 0;

    let scaling = 0;    
    

    // Event listener to track mouse movement over the target element
    targetElement.addEventListener('mousemove', (event) => {
        // Get the bounding rectangle of the element
        const rect = targetElement.getBoundingClientRect();
        // Calculate mouse position relative to the element
        mouseX = event.clientX - rect.left;
        mouseY = event.clientY - rect.top;

        scaling = panzoom.getScale();


        roundedX = Math.round(mouseX/(minorGridSize*scaling))*minorGridSize ;
        roundedY = Math.round(mouseY/(minorGridSize*scaling))*minorGridSize ;
    });

    //ID counter for slat IDs
    let slatCounter = 0;

    // Event listener to print slat when mouse is pressed
    targetElement.addEventListener('pointerdown', (event) => {
        if(disablePanStatus == true){
            console.log(`Rounded mouse position - X: ${roundedX}, Y: ${roundedY}`);
            let tmpLine = draw.line(roundedX, roundedY, roundedX, roundedY + 32 * minorGridSize).stroke({ width: 3, color:'#076900' });
            tmpLine.attr('id','ID-L'+'-N' + slatCounter)
            slatCounter += 1;

        }        
    });


})
    










    
    /*
    

*/

    





    //var rect = draw.rect(300, 300).fill(pattern1).move(100,100);
    //rect.fill(pattern)


    /* 

    // Create a group for the grid and other elements
    var gridGroup = draw.group();

    // Function to create the grid
    function createGrid() {
        var gridSize = 50; // size of the grid squares
        var width = draw.width();
        var height = draw.height();

        // Draw vertical lines
        for (var x = 0; x < width; x += gridSize) {
            gridGroup.line(x, 0, x, height).stroke({ width: 5, color:'#000000' });
        }

        // Draw horizontal lines
        for (var y = 0; y < height; y += gridSize) {
            gridGroup.line(0, y, width, y).stroke({ width: 5, color: '#000000' });
        }
    }

    // Create the grid
    createGrid();

    // Add other SVG elements if needed
    var rect = gridGroup.rect(100, 100).move(200, 200).fill('#f06');

    // Initialize Panzoom
    var panZoom = Panzoom(draw.node, {
        contain: 'outside',
        minScale: 0.5,
        maxScale: 4
    });

    // Make the SVG container zoomable and pannable
    draw.on('wheel', function(event) {
        if (event.ctrlKey) {
            event.preventDefault();
            panZoom.zoomWithWheel(event);
        }
    });

    // Prevent the default behavior of the mouse down event
    draw.on('mousedown', function(event) {
        event.preventDefault();
    });

    // Enable panning on mouse drag
    draw.on('mousemove', function(event) {
        if (event.buttons === 1) { // If left mouse button is held down
            panZoom.pan(event.movementX, event.movementY);
        }
    });

*/
