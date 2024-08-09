import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { getInventoryItemById } from './functions_inventory.js';
import { generateSeedPoints3D } from './functions_seed_path.js'

const right3DPanel = document.getElementById('right-3D-panel');

//Configure scene
const scene = new THREE.Scene();
scene.scale.y = -1;
scene.background =  new THREE.Color(0xffffff);
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);

//Set up renderer & camera
const renderer = new THREE.WebGLRenderer();
const camera = new THREE.PerspectiveCamera( 75, right3DPanel.clientWidth / right3DPanel.clientHeight, 0.1, 1000 );
camera.up.set(0, 0, 1);

//Make scene interactive
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.25;
controls.screenSpacePanning = false;

//Start render
renderScene()


/**
 * Function to update renderer and camera to resized 3D viewer window
 */
export function updateCamera(){
    renderer.setSize( right3DPanel.clientWidth, right3DPanel.clientHeight );
    camera.aspect = right3DPanel.clientWidth / right3DPanel.clientHeight;
    camera.updateProjectionMatrix();
    
}

/**
 * Function to render the scene.
 */
export function renderScene(){
    renderer.setSize( right3DPanel.clientWidth, right3DPanel.clientHeight );
    right3DPanel.innerHTML = ''
    right3DPanel.appendChild( renderer.domElement );

    //Set up positioning
    const center = computeSceneCenter(); // Compute scene center
    controls.target.copy(center); // Ensure controls are also looking at the center
    controls.update();

    // Set up lighting
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(center.x, center.y, center.z + 50).normalize();
    scene.add(directionalLight);

    // Set up animation loop
    function animate() {
        controls.update();
        renderer.render( scene, camera );
    }
    renderer.setAnimationLoop( animate );
}

/**
 * Function to comput the center of the bounding box of the scene geometry
 * @returns {THREE.Vector3} Center of scene
 */
function computeSceneCenter() {
    const box = new THREE.Box3();
    scene.traverse(object => {
        if (object.isMesh) {
            box.expandByObject(object);
        }
    });
    const center = new THREE.Vector3();
    box.getCenter(center);
    return center;
}




/**
 * Function to place a 3D slat into the THREE.js scene
 * @param {Number} x X coordinate to place the slat. Top LH coordinate
 * @param {Number} y Y coordinate to place the slat. Top LH coordinate
 * @param {Number} layerNum Layer number to place the slat. Corresponds to Z
 * @param {Number} id Unique identifier number for the slat. Corresponds to slat ID
 * @param {String} layerColor Color of the active layer. Corresponds to slat color
 * @param {Boolean} horizontal True if slat should be placed horizontally. False if should be placed vertically
 * @param {Number} radius Radius of slat to be placed. Max 0.5
 * @param {Number} length Length of slat to be placed. Corresponds to number of handles
 */
export function place3DSlat(x, y, layerNum, id, layerColor,  horizontal, radius = 0.25, length = 32) {

    const cylinderGeometry = new THREE.CylinderGeometry(radius, radius, 32, length);
    const cylinderMaterial = new THREE.MeshStandardMaterial({ color: layerColor });

    const cylinder = new THREE.Mesh(cylinderGeometry, cylinderMaterial);

    if(horizontal){
        cylinder.rotation.z = Math.PI / 2;  // Rotate 90 degrees around the z-axis to align along the x-axis
        cylinder.position.set(x + length*(31/64), y + length*(1/64), layerNum); //Then set position, translate as necessary
    }
    else{
        cylinder.position.set(x, y + length/2, layerNum);
    }

    cylinder.name = 'slat-3d:' + id
    scene.add(cylinder)

    //If scene has not been rendered yet, render it!
    if(id < 2){
        renderScene()
    }
}

/**
 * Function to place a 3D cargo into the THREE.js scene
 * @param {Number} x X coordinate to place the cargo
 * @param {Number} y Y coordinate to place the cargo
 * @param {Number} layerNum Layer number to place the cargo. Corresponds to Z
 * @param {String} id Identifier for the cargo type. 
 * @param {Number} cargoCounter Unique identifier for the cargo placed. 
 * @param {Boolean} top True if cargo should be placed at the top. False if should be placed at the bottom
 * @param {Number} radius Radius of cargo to be placed. Max 0.5
 */
export function place3DCargo(x, y, layerNum, id, cargoCounter, top, radius=0.5) {

    const cargoItem = getInventoryItemById(id);

    const sphereGeometry = new THREE.SphereGeometry(radius)
    const sphereMaterial = new THREE.MeshStandardMaterial({ color: cargoItem.color });

    const cubeGeometry = new THREE.BoxGeometry(1.5*radius, 1.5*radius, 1.5*radius)
    const cubeMaterial = new THREE.MeshStandardMaterial({ color: cargoItem.color });
        
    if(top == true){
        const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
        sphere.position.set(x, y + radius, parseInt(layerNum) + radius)
        sphere.name = 'cargo-3d:' + cargoCounter
        scene.add(sphere)
    }
    else{
        const cube = new THREE.Mesh(cubeGeometry, cubeMaterial);
        cube.position.set(x, y + radius, parseInt(layerNum) - 0.75 * radius)
        cube.name = 'cargo-3d:' + cargoCounter
        scene.add(cube)
    }
}

/**
 * Function to place a 3D seed into the THREE.js scene
 * @param {Number} roundedX X coordinate to place the seed. Corresponds to upper LH corner
 * @param {Number} roundedY Y coordinate to place the seed. Corresponds to upper LH corner
 * @param {Number} layerNum Layer number to place the seed. Corresponds to Z coordinate
 * @param {String} layerColor Color of the active layer. Corresponds to the seed color
 * @param {Boolean} rotated True if seed should be rotated 90 degrees. False otherwise.
 */
export function place3DSeed(roundedX, roundedY, layerNum, layerColor, rotated){
    // Define parameters
    const step = 1; // Step size
    const rows = 5; // Number of rows
    const cols = 16; // Number of columns

    const width = cols; // Width of each section
    const height = rows; // Height of each section

    //Generate set of points corresponding to seed geometry
    const points = generateSeedPoints3D(step, rows, cols, width, height);

    // Connect points of seed geometry to define a seed curve
    const curveSegments = [];
    for (let i = 0; i < points.length - 1; i++) {
        const start = points[i];
        const end = points[i + 1];
        const mid = new THREE.Vector3((start.x + end.x) / 2, (start.y + end.y) / 2, (start.z + end.z) / 2);

        // Create a quadratic curve between segments
        const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
        curveSegments.push(curve);
    }

    // Combine the curves into one path
    const path = new THREE.CurvePath();
    curveSegments.forEach(curve => path.add(curve));

    // Create a mesh from the path
    const tubeGeometry = new THREE.TubeGeometry(path, 1000, 0.25, 4, false);
    const tubeMaterial = new THREE.MeshBasicMaterial({ color: layerColor, side: THREE.DoubleSide });
    const tubeMesh = new THREE.Mesh(tubeGeometry, tubeMaterial);

    if(rotated){
        tubeMesh.rotation.z = - Math.PI / 2; // Rotate 90 degrees around the z-axis to align along the x-axis
        tubeMesh.position.set(roundedX - step/2, roundedY + width - step/2, layerNum);
    }
    else{
        tubeMesh.position.set(roundedX, roundedY, layerNum);
    }

    tubeMesh.name = 'seed-3D'
    scene.add(tubeMesh);
}

/**
 * Function to remove slat with a particular ID from THREE.js scene
 * @param {Number} id ID number of slat to delete
 */
export function delete3DSlat(id){
    console.log("Slat ID to remove: ", id)

    let slatToRemove = scene.getObjectByName('slat-3d:' + id);
    
    if (slatToRemove) {
        console.log("we have the slat!")
        scene.remove(slatToRemove);
    
        // Dispose of the slat's geometry and material to free up memory
        if (slatToRemove.geometry) slatToRemove.geometry.dispose();
        if (slatToRemove.material) slatToRemove.material.dispose();
    }
}

/**
 * Function to remove cargo with a particular ID from THREE.js scene
 * @param {Number} id ID number of cargo to delete
 */
export function delete3DCargo(id){
    console.log("Cargo ID to remove: ", id)

    let cargoToRemove = scene.getObjectByName('cargo-3d:' + id);
    
    if (cargoToRemove) {
        console.log("we have the cargo!")
        scene.remove(cargoToRemove);
    
        // Dispose of the slat's geometry and material to free up memory
        if (cargoToRemove.geometry) cargoToRemove.geometry.dispose();
        if (cargoToRemove.material) cargoToRemove.material.dispose();
    }
}

/**
 * Function to remove the seed from THREE.js scene
 */
export function delete3DSeed(){
    let seedToRemove = scene.getObjectByName('seed-3D');
    
    if (seedToRemove) {
        console.log("we have the seed!")
        scene.remove(seedToRemove);
    
        // Dispose of the seed's geometry and material to free up memory
        if (seedToRemove.geometry) seedToRemove.geometry.dispose();
        if (seedToRemove.material) seedToRemove.material.dispose();
    }
}

/**
 * Deletes a 3D element corresponding to given SVG element
 * @param {SVG Element} element Element from SVG to delete 
 */
export function delete3DElement(element){
    if(element.attr('class').split(' ').includes('line')){
        delete3DSlat(element.attr('id'))
    }
    else if(element.attr('class').split(' ').includes('cargo')){
        delete3DCargo(element.attr('id'))
    }
    else if(element.attr('class').split(' ').includes('seed')){
        delete3DSeed()
    }
}
    

/**
 * Function to move a slat within THREE.js scene
 * @param {Number} id Unique ID corresponding to slat that should be moved
 * @param {Number} x X coordinate to move slat to. Corresponds to top LH corner
 * @param {Number} y Y coordinate to move slat to. Corresponds to top LH corner
 * @param {Number} layerNum Layer on which slat to be moved resides
 * @param {Boolean} horizontal True if slat is horizontal. False if vertical 
 * @param {Number} length Length of slat. Corresponds to number of handles
 */
export function move3DSlat(id, x, y, layerNum, horizontal = false, length=32){
    let slatToMove = scene.getObjectByName('slat-3d:' + id);
    if (slatToMove) {
        if(horizontal){
            slatToMove.position.set(x + length/2, y + length*(1/64), layerNum)
        }
        else{
            slatToMove.position.set(x, y + length*(33/64), layerNum);
        }
    }
}

/**
 * Function to move a cargo within THREE.js scene
 * @param {Number} id Unique ID corresponding to cargo that should be moved
 * @param {Number} x X coordinate to move cargo to.
 * @param {Number} y Y coordinate to move cargo to
 * @param {Number} layerNum Lyer on which cargo to be moved resides
 * @param {Boolean} top True if cargo is on top of slats. False if below slats
 * @param {Number} radius Radius of cargo. Max is 0.5
 */
export function move3DCargo(id, x, y, layerNum, top = true, radius=0.5){
    let cargoToMove = scene.getObjectByName('cargo-3d:' + id);
    if (cargoToMove) {
        if(cargoToMove.geometry instanceof THREE.SphereGeometry){
            cargoToMove.position.set(x, y + radius, parseInt(layerNum) + radius)
        }
        else{
            cargoToMove.position.set(x, y + radius, parseInt(layerNum) - 0.75 * radius)
        }
    }
}

/**
 * Function to move the seed within THREE.js scene
 * @param {Number} x X coordinate to move seed to
 * @param {Number} y Y coordinate to move seed to
 * @param {Number} layerNum Layer on which seed to be moved resides
 */
export function move3DSeed(x, y, layerNum){
    let seedToMove = scene.getObjectByName('seed-3D');
    if (seedToMove) {
        seedToMove.position.set( x, y, layerNum);        
    }
}

/**
 * Function to remove an entire layer of slats from THREE.js scene
 * @param {Number} slatLayer Layer number corresponding to layer that should be removed
 */
export function delete3DSlatLayer(slatLayer){
    slatLayer.children().forEach(child => {
        if(child.attr('class').split(' ').includes('line')){
            delete3DSlat(child.attr('id'))
        }
    });
}





/**
 * Function to change the color of a particular slat
 * @param {Number} id ID number of slat to recolor
 * @param {String} newColor Color to recolor slat to
 */
function recolor3DSlat(id, newColor){
    console.log("Slat ID to recolor: ", id)

    let slatToRecolor = scene.getObjectByName('slat-3d:' + id);
    
    if (slatToRecolor) {
        console.log("we have the slat!")
        slatToRecolor.material.color.set(newColor);
    }
}

/**
 * Function to change the color of a particular cargo
 * @param {Number} id ID number of cargo to recolor
 * @param {String} newColor Color to recolor cargo to
 */
function recolor3DCargo(id, newColor){
    console.log("Cargo ID to recolor: ", id)

    let cargoToRecolor = scene.getObjectByName('cargo-3d:' + id);
    
    if (cargoToRecolor) {
        console.log("we have the cargo!")
        cargoToRecolor.material.color.set(newColor);
    }
}

/**
 * Function to change the color of a seed
 * @param {String} newColor Color to recolor seed to
 */
function recolor3DSeed(newColor){
    let seedToRecolor = scene.getObjectByName('seed-3D');
    
    if (seedToRecolor) {
        console.log("we have the seed!")
        seedToRecolor.material.color.set(newColor);
    }
}

/**
 * Function to change the color of a particular element in 3D
 * @param {SVG Element} element Element from SVG to recolor
 * @param {String} newColor Color to recolor element to
 */
export function recolor3DElement(element, newColor){
    if(element.attr('class').split(' ').includes('line')){
        recolor3DSlat(element.attr('id'), newColor)
    }
    else if(element.attr('class').split(' ').includes('cargo')){
        recolor3DCargo(element.attr('id'), newColor)
    }
    else if(element.attr('class').split(' ').includes('seed')){
        recolor3DSeed(newColor)
    }
}