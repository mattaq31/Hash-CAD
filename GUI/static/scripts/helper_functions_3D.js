import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';


import {findSlatStartOrientation} from './helper_functions_io.js'

const right3DPanel = document.getElementById('right-3D-panel');
const scene = new THREE.Scene();
scene.background =  new THREE.Color(0xaaaaaa);
const renderer = new THREE.WebGLRenderer();
const camera = new THREE.PerspectiveCamera( 75, right3DPanel.clientWidth / right3DPanel.clientHeight, 0.1, 1000 );
camera.up.set(0, 0, 1);

// Add orbit controls to make the scene interactive
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; // for an improved experience
controls.dampingFactor = 0.25;
controls.screenSpacePanning = false; // if you want to pan in screen space (2D)




export function renderMegastructure(slatDict, bottomCargoDict, topCargoDict){
    scene.remove.apply(scene, scene.children);
    let slatGeometry = drawSlatGeometry(slatDict)
    let topCargoGeometry = drawCargoGeometry(topCargoDict, true)
    let bottomCargoGeometry = drawCargoGeometry(bottomCargoDict, false)
    populateScene(slatGeometry)
    populateScene(topCargoGeometry)
    populateScene(bottomCargoGeometry)
    renderScene()
}


export function updateCamera(){
    renderer.setSize( right3DPanel.clientWidth, right3DPanel.clientHeight );
    camera.aspect = right3DPanel.clientWidth / right3DPanel.clientHeight;
    camera.updateProjectionMatrix();
    
}

export function renderScene(){
    renderer.setSize( right3DPanel.clientWidth, right3DPanel.clientHeight );
    right3DPanel.innerHTML = ''
    right3DPanel.appendChild( renderer.domElement );

    

    // Compute scene center
    const center = computeSceneCenter();

    console.log("Center is: ", center)

    // Initial camera positioning
    //camera.position.set( center.x, center.y, center.z + 50 );
    //controls.update();

    controls.target.copy(center); // Ensure controls are also looking at the center
    controls.update();

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(center.x, center.y, center.z + 50).normalize();
    scene.add(directionalLight);

    console.log("Scene during render: ", scene)

    // Animation
    function animate() {
        controls.update();
        renderer.render( scene, camera );
    }
    renderer.setAnimationLoop( animate );
}




export function drawSlatGeometry(slatDict){

    const cylinderMeshes = [];

    //Get unique slat numbers
    let slatNums = Object.values(slatDict)
    const uniqueSlatNums = new Set(slatNums);

    const cylinderGeometry = new THREE.CylinderGeometry(0.5, 0.5, 32, 32);
    const cylinderMaterial = new THREE.MeshStandardMaterial({ color: 0xff0000 });

    for (const slatNum of uniqueSlatNums) {
        let orientation = findSlatStartOrientation(slatDict, slatNum)

        let dictX = orientation[0]
        let dictY = orientation[1]
        let layerId = orientation[2]
        let horizontal = orientation[3]

        const cylinder = new THREE.Mesh(cylinderGeometry, cylinderMaterial);

        if(horizontal){
            cylinder.rotation.z = Math.PI / 2; // Rotate 90 degrees around the z-axis to align along the x-axis
            cylinder.position.set(dictX + 16, dictY, layerId);
        }
        else{
            cylinder.position.set(dictX, dictY + 16, layerId);
        }

        
        cylinderMeshes.push(cylinder);
    }

    return cylinderMeshes
}




export function drawCargoGeometry(cargoDict, top=true){

    const cargoMeshes = [];

    const sphereGeometry = new THREE.SphereGeometry(0.5)
    const sphereMaterial = new THREE.MeshStandardMaterial({ color: 0x000000 });

    const cubeGeometry = new THREE.BoxGeometry(1,1,1)
    const cubeMaterial = new THREE.MeshStandardMaterial({ color: 0x000000 });
    
    // Iterate through the dictionary
    for (const [key, value] of Object.entries(cargoDict)) {
        
        let keyArray = key.split(',')

        let dictX   = Number(keyArray[0])
        let dictY   = Number(keyArray[1])
        let layerId = keyArray[2]

        let cargoId = value
        
        if(top == true){
            const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
            sphere.position.set(dictX, dictY + 0.5, layerId + 0.25)

            cargoMeshes.push(sphere)
        }
        else{
            const cube = new THREE.Mesh(cubeGeometry, cubeMaterial);
            cube.position.set(dictX, dictY + 0.5, layerId - 0.5)

            cargoMeshes.push(cube)
        }
    }

    return cargoMeshes
}




export function populateScene(geometryArray){
    for (const slat of geometryArray) {
        scene.add(slat)
    }

    // Add lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
}



// Function to compute the center of the bounding box of the scene geometry
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