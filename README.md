# defense-and-intel-analysis-toolbox

The ArcGIS Defense and Intelligence Analysis Toolbox is a set of models, scripts, and tools for use in ArcGIS Desktop. These tools provide specialized processing and workflows for defense and intelligence analysis.

![Image of Defense and Intel Analysis Toolbox](ScreenShot.jpg "defense-and-intel-analysis-toolbox")

## Features

* Specialized geoprocessing models and tools for defense and intelligence analysis including
* Tools for visibility and range analysis
* Tools for analyzing the battlefield  environment
* Tools for position analysis

## Instructions

### General Help
[New to Github? Get started here.](http://htmlpreview.github.com/?https://github.com/Esri/esri.github.com/blob/master/help/esri-getting-to-know-github.html)

### Getting Started with the toolbox
* Install and configure Apache Ant
    * Download from http://ant.apache.org and unzip to a location on your machine
    * Set environment variable ANT_HOME to Ant Install Location
    * Add Ant\bin to your path: %ANT_HOME%\bin
    * You may optionally install the PyDev Eclipse Plugin for Python
* To download the data dependencies 
    * Open Command Prompt>
    * cd defense-and-intel-analysis-toolbox\data
    * > ant
    * Verify “Build Succeeded”  
* To run unit tests
    * Open Command Prompt>
    * > cd defense-and-intel-analysis-toolbox\source\test
    * > ant
    * Verify “Build Succeeded”  

## Requirements

* ArcGIS Desktop 10.1 Standard 
* Apache Ant - used to download and extract dependent data and run test drivers
* Some tools require additional licenses (they will be disabled if not available):
* ArcGIS Desktop Advanced 
* ArcGIS Spatial Analyst Extension
* ArcGIS 3D Analyst Extension

## Resources

* Learn more about Esri's [ArcGIS for Defense maps and apps](http://resources.arcgis.com/en/communities/defense-and-intelligence/).

## Issues

* Find a bug or want to request a new feature?  Please let us know by submitting an issue.

## Contributing

* Anyone and everyone is welcome to contribute.

## Licensing

Copyright 2013 Esri

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the repository's
[license.txt](license.txt) file.

[](Esri Tags: ArcGIS Defense and Intelligence)
[](Esri Language: Python)
