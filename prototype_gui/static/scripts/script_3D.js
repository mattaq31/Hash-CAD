import {updateCamera} from './functions_3D.js'

const right3DPanel = document.getElementById('right-3D-panel');
const resizer = document.getElementById('resizer');

document.addEventListener('DOMContentLoaded', () => {
    let isResizing = false;

    //Start resizing when you click the resizing bar
    resizer.addEventListener('pointerdown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'ew-resize';
        console.log("resizing has begun")
    });

    //Resize the 3D panel when dragging the resizing bar
    document.addEventListener('mousemove', (e) => {
        if (isResizing) {
            const containerWidth = document.querySelector('.central-window').offsetWidth;
            const newWidth = containerWidth - e.clientX - resizer.offsetWidth;
            right3DPanel.style.minWidth = `${newWidth}px`;
            updateCamera()
        }
    });

    //End resizing when you release the resizing bar
    document.addEventListener('pointerup', () => {
        isResizing = false;
        document.body.style.cursor = 'default';
    });      
});











