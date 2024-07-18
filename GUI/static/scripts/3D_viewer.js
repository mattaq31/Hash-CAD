import * as THREE from 'three';

import {drawSlatGeometry, populateScene, renderScene, updateCamera} from './helper_functions_3D.js'

const right3DPanel = document.getElementById('right-3D-panel');


document.addEventListener('DOMContentLoaded', () => {


    //create a blue LineBasicMaterial
    const lineMaterial = new THREE.LineBasicMaterial( { color: 0x0000ff } );

    const points = [];
    points.push( new THREE.Vector3( - 10, 0, 0 ) );
    points.push( new THREE.Vector3( 0, 10, 0 ) );
    points.push( new THREE.Vector3( 10, 0, 0 ) );

    const cylinderGeometry = new THREE.CylinderGeometry(100, 100, 160, 32);
    const cylinderMaterial = new THREE.MeshStandardMaterial({ color: 0xff0000 });
    const cylinder = new THREE.Mesh(cylinderGeometry, cylinderMaterial);
    cylinder.position.set(1, 1, 1);

    const lineGeometry = new THREE.BufferGeometry().setFromPoints( points );
    const line = new THREE.Line( lineGeometry, lineMaterial );

    //populateScene([cylinder])
    //renderScene()

});






const resizer = document.getElementById('resizer');
let isResizing = false;

resizer.addEventListener('pointerdown', (e) => {
    isResizing = true;
    document.body.style.cursor = 'ew-resize';
    console.log("resizing has begun")
});

document.addEventListener('mousemove', (e) => {
    if (isResizing) {
        const containerWidth = document.querySelector('.central-window').offsetWidth;
        const newWidth = containerWidth - e.clientX - resizer.offsetWidth;
        right3DPanel.style.minWidth = `${newWidth}px`;
        updateCamera()
    }
});

document.addEventListener('pointerup', () => {
    isResizing = false;
    document.body.style.cursor = 'default';
});


