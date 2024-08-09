import { createGridArray, importHandles, importDesign } from './functions_design_dicts.js';
import { getHandleLayerDict, clearHandles } from './functions_handles.js';
import { updateInventoryItems} from './functions_inventory.js';
import { showNotification } from './functions_socket.js';
import { getLayerList } from './functions_layers.js'
import { downloadFile } from './functions_misc.js';
import { getFullDrawing } from './functions_drawing.js';

import { writeVariable } from './variables.js';
import {minorGridSize, shownOpacity, shownCargoOpacity } from './constants.js'

var socket = io();

document.addEventListener('DOMContentLoaded', () => {
    let layerList = getLayerList()

    //Design import via file upload
    let uploadForm = document.getElementById('upload-form')
    uploadForm.addEventListener('submit', function(event){
        console.log("Upload form submitted!")

        // Prevent the default form submission
        event.preventDefault(); 
        
        //Get file input
        var fileInput = document.getElementById('file-input');
        if (fileInput.files.length == 0) {
            console.log("No file selected.")
            return
        }

        //Get file
        var file = fileInput.files[0];

        //Setup file reader
        var reader = new FileReader();
        reader.onload = function(event) {
            var data = {
                'file': {
                    'filename': file.name,
                    'data': new Uint8Array(event.target.result)
                }
            };
            console.log("reader.onload executed!")
            socket.emit('upload_file', data);
        };

        //Read file and emit signal on socket
        reader.readAsArrayBuffer(file)
    })

    //Respond to design file upload
    socket.on('upload_response', function(data) {
        console.log(data.message)
    });

    //Import design after file upload
    socket.on('design_imported', function(data) {
        console.log("Imported design!", data)

        let offset = getFullDrawing().point(0,0);

        let offsetX = Math.round(offset.x/(minorGridSize))*minorGridSize ;
        let offsetY = Math.round(offset.y/(minorGridSize))*minorGridSize ;

        
        


        console.log(getFullDrawing(), offset, offset.x, offset.y)

        let seedDict = data[0]
        let slatDict = data[1]
        let cargoDict = data[2]
        let handleDict = data[3]
        let slatCounter, cargoCounter = importDesign(seedDict, slatDict, 
                                                     cargoDict, handleDict, 
                                                     layerList, minorGridSize, 
                                                     shownOpacity, shownCargoOpacity,
                                                     offsetX, offsetY)
        writeVariable("slatCounter", slatCounter)
        writeVariable("cargoCounter", cargoCounter)
    });




    //Plate file uploading
    let plateUploadForm = document.getElementById('plate-upload-form')
    plateUploadForm.addEventListener('submit', function(event) {
        console.log("Plate upload form submitted!")

        //Prevent the default form submission
        event.preventDefault(); 

        //Get file inpus
        var fileInput = document.getElementById('plate-file-input');
        if (fileInput.files.length == 0) {
            console.log("No file selected.")
            return
        }

        //Iterate through files
        Array.from(fileInput.files).forEach(file => {

            //Setup file reader
            var reader = new FileReader();
            reader.onload = function(event) {
                var data = {
                    'file': {
                        'filename': file.name,
                        'data': new Uint8Array(event.target.result)
                    }
                };
                console.log("reader.onload executed!")
                socket.emit('upload_plates', data);
            };

            //Read file and emit signal on socket
            reader.readAsArrayBuffer(file)
        });
    })

    //Respond to plate file upload
    socket.on('plate_upload_response', function(data) {
        console.log(data.message)
        updateInventoryItems();
    });




    //Design saving & exporting
    //document.getElementById('save-design').addEventListener('click', function(event) {
    //    console.log("design to be saved now!")
    //    let gridArray = createGridArray(layerList, minorGridSize)
    //    socket.emit('design_to_backend_for_download', gridArray);
    //});

    //Download saved design
    //socket.on('saved_design_ready_to_download', function(){
    //    downloadFile('/download/crisscross_design.npz', 'crisscross_design.npz')
    //})




    //Megastructure generation
    document.getElementById('generate-megastructure-button').addEventListener('click',function(event){
        let gridArray = createGridArray(layerList, minorGridSize)
        let handleConfigs = getHandleLayerDict(layerList)

        let checkboxOldHandles = document.getElementById('checkbox-old-handles').checked;
        let checkboxGraphics = document.getElementById('checkbox-graphics').checked;
        let checkboxEcho = document.getElementById('checkbox-echo').checked;

        let generalConfigs = [checkboxOldHandles, checkboxGraphics, checkboxEcho]

        socket.emit('generate_megastructures', [gridArray, handleConfigs, generalConfigs])
    })

    //Download generated megastructure
    socket.on('megastructure_output_ready_to_download', function(){
        downloadFile('/download/outputs.zip', 'outputs.zip')
    })


    

    //Handle generation
    document.getElementById('generate-handles-button').addEventListener('click',function(event){
        let gridArray = createGridArray(layerList, minorGridSize)
        let handleConfigs = getHandleLayerDict(layerList)
        let handleIterations = document.getElementById('handle-iteration-number').value
        console.log('generating handles now...')
        socket.emit('generate_handles', [gridArray, handleConfigs, handleIterations])
    })

    //Import newly generated handles
    socket.on('handles_sent', function(handleDict){
        console.log('handles have been generated and recieved:', handleDict)
        importHandles(handleDict, layerList, minorGridSize)
    })

    //Clear old handles
    document.getElementById('clear-handles-button').addEventListener('click', function(event){
        clearHandles(layerList)
    })





    //Read in console messages from python backend
    socket.on('console', function(msg) {
        showNotification(msg.data)
    });
})
