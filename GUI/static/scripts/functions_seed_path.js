import * as THREE from 'three';

/**
 * Function to create an SVG.path for seed
 * @param {Number} x Starting X position
 * @param {Number} y Starting Y position
 * @param {Number} step Distance between each row and between each column
 * @param {Number} rows Number of rows in seed
 * @param {Number} cols Number of columns in seed
 * @returns {String} Path string for SVG.path 
 */
export function drawDefaultSeed(x, y, step, rows = 5, cols = 16){
    const width = step * cols;
    const height = step * rows;

    let pathString = `M ${x - step/2} ${y} `;
    
    //Start with horizontal lines
    for (let i = 0; i < rows; i++) {
        if (i === rows-1){ //Last line
            if (i % 2 === 0) {
                // Forward direction
                pathString += `l ${width-step/2} 0`;
                } else {
                // Backward direction
                pathString += `l ${-width+step/2} 0`;
                }
        }
        else{ //All other horizontal lines
            if (i % 2 === 0) {
                // Forward direction
                pathString += `l ${width} 0  l 0 ${step}`;
                } else {
                // Backward direction
                pathString += `l ${-width} 0 l 0 ${step}`;
                }
        }
    }

    // Now start vertical snaking
    for (let j = 0; j < cols; j++) {
        if (j === 0){
            pathString += ` l 0 ${-height + step/2} l ${-step} 0`;
        }
        else if(j === cols - 1){
            if (j % 2 === 0) {
                // Up direction
                pathString += ` l 0 ${-height} l ${-step} ${step}`;
                } else {
                // Down direction
                pathString += ` l 0 ${height} l ${-step} ${step}`;
                }
        }
        else if (j % 2 === 0) {
        // Up direction
        pathString += ` l 0 ${-height} l ${-step} 0`;
        } else {
        // Down direction
        pathString += ` l 0 ${height} l ${-step} 0`;
        }
    }

    return pathString
}

/**
 * Function to create an SVG.path for rotated seed
 * @param {Number} x Starting X position
 * @param {Number} y Starting Y position
 * @param {Number} step Distance between each row and between each column
 * @param {Number} rows Number of rows in seed
 * @param {Number} cols Number of columns in seed
 * @returns {String} Path string for SVG.path 
 */
export function drawRotatedSeed(x, y, step, rows = 5, cols = 16){
    const width = step * cols;
    const height = step * rows;

    let pathString = `M ${x} ${y + width - step/2}`;

    //Start with horizontal lines
    for (let i = 0; i < rows; i++) {
        if (i === rows-1){ //Last line
            if (i % 2 === 0) {
                // Forward direction
                pathString += `l 0 ${-width+step/2}`;
                } else {
                // Backward direction
                pathString += `l 0 ${width-step/2}`;
                }
        }
        else{ //All other horizontal lines
            if (i % 2 === 0) {
                // Forward direction
                pathString += `l 0 ${-width}  l ${step} 0`;
                } else {
                // Backward direction
                pathString += `l 0 ${width} l ${step} 0`;
                }
        }
    }

    // Now start vertical snaking
    for (let j = 0; j < cols; j++) {
        if (j === 0){
            pathString += ` l ${-height + step/2} 0 l 0 ${step} `;
        }
        else if(j === cols - 1){
            if (j % 2 === 0) {
                // Up direction
                pathString += ` l ${height} 0 l ${step} ${step}`;
                } else {
                // Down direction
                pathString += ` l ${height} 0 l ${step} ${step}`;
                }
        }
        else if (j % 2 === 0) {
        // Up direction
        pathString += ` l ${-height} 0 l 0 ${step}`;
        } else {
        // Down direction
        pathString += ` l ${height} 0 l 0 ${step}`;
        }
    }

    return pathString
}

/**
 * Function to generate points for a 3D seed
 * @param {Number} step Distance between each row and between each column
 * @param {Number} rows Number of rows in seed
 * @param {Number} cols Number of columns in seed
 * @param {Number} width Width of seed
 * @param {Number} height Height of seed
 * @returns {Array} Array of THREE.Vector3 points
 */
export function generateSeedPoints3D(step, rows, cols, width, height) {
    const points = [];
    let x = 0 - step / 2
    let y = 0 + step / 2
    let z = 0 - 0.375
    points.push(new THREE.Vector3(x, y, z))

    for (let i = 0; i < rows; i++) {
        if (i === rows - 1) { // Last line
            if (i % 2 === 0) {
            // Forward direction
            x += (width - step / 2)
            points.push(new THREE.Vector3(x, y, z))
            } 
            else {
            // Backward direction
            x += (- width + step / 2)
            points.push(new THREE.Vector3(x, y, z))
            }
        }
        else{
            if (i % 2 === 0) {
                // Forward direction
                x += width
                points.push(new THREE.Vector3(x, y, z))
                y += step 
                points.push(new THREE.Vector3(x, y, z))
                } else {
                // Backward direction
                x -= width
                points.push(new THREE.Vector3(x, y, z))
                y += step
                points.push(new THREE.Vector3(x, y, z))
                }
        }
    }

    for (let j = 0; j < cols; j++) {
        if (j === 0) {
            y += (- height + step / 2)
            points.push(new THREE.Vector3(x, y, z))
            x -= step
            points.push(new THREE.Vector3(x, y, z))
        } else if (j === cols - 1) {
            if (j % 2 === 0) {
            // Up direction
            y -= height
            points.push(new THREE.Vector3(x, y, z))
            x -= step
            points.push(new THREE.Vector3(x, y, z))
            } else {
            // Down direction
            y += height
            points.push(new THREE.Vector3(x, y, z))
            x -= step
            y += step
            points.push(new THREE.Vector3(x, y, z))
            }
        } else if (j % 2 === 0) {
            // Up direction
            y -= height
            points.push(new THREE.Vector3(x, y, z))
            x -= step
            points.push(new THREE.Vector3(x, y, z))
        } else {
            // Down direction
            y += height
            points.push(new THREE.Vector3(x, y, z))
            x -= step
            points.push(new THREE.Vector3(x, y, z))
        }
    }

    return points;
}