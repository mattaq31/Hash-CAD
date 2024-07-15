const resizer = document.getElementById('resizer');
const right3DPanel = document.getElementById('right-3D-panel');
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
    }
});

document.addEventListener('pointerup', () => {
    isResizing = false;
    document.body.style.cursor = 'default';
});