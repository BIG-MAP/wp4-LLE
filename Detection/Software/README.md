# LLE API

This is the source code of the LLE API

## Cloning
To download the source code install git on your computer. It can be downloaded [here](https://git-scm.com/download/win). Open a terminal in Linux or the GIT CMD program in Windows, navigate to an appropriate folder, and run the following command:

`git clone {url-of-this-github-repository}`

## Installation

To install the API, open a terminal in Linux or a command line in Windows and navigate to the folder containing this README file (use the `cd` command).

1. Python:

Install the latest version of the Python interpreter in your system (currently 3.11). It can be downloaded [here](https://www.python.org/downloads/).
In Windows: If not added automatically remember to add the Python executable folder to the Windows PATH library, both locally and systemwide if possible.

3. Poetry:

Install the latest version of Poetry in your system. It can be downloaded [here](https://python-poetry.org/docs/).
In Windows: If not added automatically remember to add the Poetry executable folder to the Windows PATH library, both locally and systemwide if possible.

4. Install dependencies:

From the Software folder run the following command to install all dependency libraries:

`poetry install`

## Running
To run the API after installing it, open a terminal in Linux or a command line in Windows and navigate to the folder containing this README file (use the `cd` command). Run the following command:

`poetry run lle-fastapi`

The API will check if all devices are connected, initialize them and fail otherwise. After a successful initialization the API will be running attached to the IP address of the computer it is running on on port 8000.

To stop the API press CTRL-C in the command line window the API is running on. The API will automatically shut down.

## Updating

To update the API, stop it, open a terminal in Linux or the GIT CMD program in Windows, navigate to the folder containing this README file (use the `cd` command), and run the following command:

`git pull`
