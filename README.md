# Squad Mortar Toolkit
The Squad Mortar Toolkit is a collection of programs for calculating accurate mortar data for the video game [Squad](https://store.steampowered.com/app/393380/Squad/).
 
# Programs

* **Standalone Mortar Calculator (SMC)** - This is ideal if you're calculating data by yourself. You can control the gun data along with the target data.

* **Mortar Calculator Software (MC)** - This is much like SMC, except that it acts as a client to the FDC and will require a team to operate. Missions are calculated and received from the FDC. Each mortarman in a battery will need to operate this program.

* **Fire Direction Center (FDC)** - This program acts like the server to the MC. Has great control over missions, including multi-gun missions, sheaf distributions, and corrections. Only one person will need to operate this program, but will need each mortarman to connect via MC.

* **Browser Mortar Calculator (BMC)** - Almost identical to SMC, except that it is browser-based. This will allow the toolkit to be used on any device that has a web browser and it will require no download. A beta version can be accessed [here](https://raw.githack.com/I8087/Squad-Mortar-Toolkit/master/src/bmc.html).

# Releases
Currently, releases are built for win32 and can be found [here](https://github.com/I8087/Squad-Mortar-Toolkit/releases). A beta version of the browser implementation can be accessed [here](https://raw.githack.com/I8087/Squad-Mortar-Toolkit/master/src/bmc.html).

# Mortar Terminology
**NOTE: These are terms and definitions based on gunnery**

* **Altitude** - Often mixed up with elevation, this is the measurement of a vertical distance usually based on sea level. A desert will have a low altitude while a mountain will have a high altitude.
* **Azimuth** - This is the observer's direction based on North. Based on a sphere, azimuth can go left and right.
* **Degree** - A unit of measurement for angles denoted by °. There are 360° in a circle.
* **Elevation** - This is the mortar's tube angle based on a horizontal plane. Based on a sphere, elevation can go up and down.
* **Milliradian** - A thousandth of a radian (0.001 rad). Usually referred to as mil. There are 2000π (~6283) mils in a circle.
* **Radian** - A unit of measurement for angles denoted by rad. There are 2π (~6.283) rad in a circle.
* **Time of Flight** - The time it takes for a round to impact when fired. Usually abbreviated to TOF.

# Simple Mortar Guide
In Squad, using mortars can be a daunting task. The first step you need to get is your gun location followed by your target location. This is the most basic data needed for the calculator to compute firing data. Once computed, the two most important pieces of data are the azimuth and elevation. The azimuth is the direction between the gun and the target. The calculator gives the azimuth in degrees since the squad compass is in degrees. To lay on the target, simply move the mortar till it points at the given azimuth. The elevation is the angle that the tube needs to be at to range that target. The greater the elevation, the shorter the range. The smaller the elevation, the longer the range.
