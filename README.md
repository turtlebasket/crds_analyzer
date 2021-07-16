# CRDS Scan Analyzer

### Basics

- Designed for usage with **Mid-IR laser comb** scan output (time scale, not frequency)

- Expected data column format: `[time, signal voltage in, piezo crystal voltage out]`

### Building

1. `pip3 <or python3 -m pip> install -r requirements.txt`

2. `build.cmd -compileUI -build`

3. Find build output in `/dist/`

### Usage

1. Import data (CSV format preferred, delimiter customization coming later, maybe even [LabView binary](https://pypi.org/project/npTDMS/))

2. Cut out & overlay peak groups using either piezo-voltage-threshold or group-spacing algorithm 

3. Set peak isolation parameters + guesses for ringdown function coefficients 

4. Admire glorious tau distributions for each comb tooth 
