/// User action and display settings state management.

import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';

/// State management for action mode and display settings
class ActionState extends ChangeNotifier {
  String slatMode;
  String cargoMode;
  String assemblyMode;
  String assemblyHandleValue;
  String assemblyAttachMode;
  bool displayAssemblyHandles;
  bool displayCargoHandles;
  bool displaySlatIDs;
  bool extendSlatTips;
  bool displaySeeds;
  bool displayGrid;
  bool drawingAids;
  bool slatNumbering;
  bool displayBorder;
  bool viewPhantoms;
  bool isolateSlatLayerView;
  bool evolveMode;
  bool slatLinkerActive;
  bool isSideBarCollapsed;
  int panelMode;
  String cargoAttachMode;
  bool plateValidation;
  double splitScreenDividerWidth = 0.5; // 50% split by default
  bool threeJSViewerActive =  true; // default to true, can be toggled by the user
  bool assemblyRandomMode; // When true, each click places random handle value
  bool assemblyEnforceMode; // When true, placed handles are marked as enforced

  Map<int, String> panelMap = {
    0: 'slats',
    1: 'assembly',
    2: 'cargo',
    3: 'settings',
  };

  Map<String, dynamic> echoExportSettings =  {
    'Reference Volume' : 75,
    'Reference Concentration' : 500,
  };

  ActionState({
    this.slatMode = 'Add',
    this.cargoMode = 'Add',
    this.assemblyMode = 'Add',
    this.assemblyHandleValue = '1',
    this.assemblyAttachMode = 'top',
    this.displayAssemblyHandles = false,
    this.displayCargoHandles = true,
    this.displaySlatIDs = false,
    this.isolateSlatLayerView = false,
    this.evolveMode = false,
    this.slatLinkerActive = false,
    this.isSideBarCollapsed = false,
    this.displaySeeds = true,
    this.displayBorder = true,
    this.displayGrid = true,
    this.drawingAids = false,
    this.slatNumbering = false,
    this.plateValidation=false,
    this.extendSlatTips = true,
    this.viewPhantoms = true,
    this.panelMode = 0,
    this.cargoAttachMode = 'top',
    this.assemblyRandomMode = false,
    this.assemblyEnforceMode = false,
  });

  void updateEchoSetting(String setting, dynamic value){
    echoExportSettings[setting] = value;
    notifyListeners();
  }

  void updateSlatMode(String value) {
    slatMode = value;
    notifyListeners();
  }

  void updateCargoMode(String value) {
    cargoMode = value;
    notifyListeners();
  }

  void updateAssemblyMode(String value) {
    assemblyMode = value;
    notifyListeners();
  }

  void updateAssemblyHandleValue(String value) {
    assemblyHandleValue = value;
    notifyListeners();
  }

  void updateAssemblyAttachMode(String value) {
    assemblyAttachMode = value;
    notifyListeners();
  }

  void setPanelMode(int value) {
    panelMode = value;
    notifyListeners();
  }

  void setSideBarStatus(bool status){
    isSideBarCollapsed = status;
    notifyListeners();
  }

  void setSplitScreenDividerWidth(double value){
    splitScreenDividerWidth = value;
    notifyListeners();
  }

  void setAssemblyHandleDisplay(bool value){
    displayAssemblyHandles = value;
    notifyListeners();
  }

  void setSlatIDDisplay(bool value){
    displaySlatIDs = value;
    notifyListeners();
  }

  void setSeedDisplay(bool value){
    displaySeeds = value;
    notifyListeners();
  }

  void setPhantomVisibility(bool value){
    viewPhantoms = value;
    notifyListeners();
  }

  void setGridDisplay(bool value){
    displayGrid = value;
    notifyListeners();
  }
  void setBorderDisplay(bool value){
    displayBorder = value;
    notifyListeners();
  }

  void setThreeJSViewerActive(bool value){
    threeJSViewerActive = value;
    notifyListeners();
  }

  void setDrawingAidsDisplay(bool value){
    drawingAids = value;
    notifyListeners();
  }

  void setExtendSlatTips(bool value){
    extendSlatTips = value;
    notifyListeners();
  }

  void setSlatNumberingDisplay(bool value){
    slatNumbering = value;
    notifyListeners();
  }

  void setCargoHandleDisplay(bool value){
    displayCargoHandles = value;
    notifyListeners();
  }

  void setPlateValidation(bool value){
    plateValidation = value;
    notifyListeners();
  }

  void setIsolateSlatLayerView(bool value){
    isolateSlatLayerView = value;
    notifyListeners();
  }

  void activateEvolveMode(){
    evolveMode = true;
    notifyListeners();
  }

  void deactivateEvolveMode(){
    evolveMode = false;
    notifyListeners();
  }

  void activateSlatLinker(){
    slatLinkerActive = true;
    notifyListeners();
  }

  void deactivateSlatLinker(){
    slatLinkerActive = false;
    notifyListeners();
  }

  void updateCargoAttachMode(String value){
    cargoAttachMode = value;
    notifyListeners();
  }

  void setAssemblyRandomMode(bool value) {
    assemblyRandomMode = value;
    notifyListeners();
  }

  void setAssemblyEnforceMode(bool value) {
    assemblyEnforceMode = value;
    notifyListeners();
  }
}
