[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI GH actions](https://github.com/MyPyDavid/raman-fitting/actions/workflows/build-test-codecov.yml/badge.svg)](https://github.com/MyPyDavid/raman-fitting/actions/workflows/build-test-codecov.yml)
[![codecov](https://codecov.io/gh/MyPyDavid/raman-fitting/branch/main/graph/badge.svg?token=II9JZAODJY)](https://codecov.io/gh/MyPyDavid/raman-fitting)
[![Test & Upload to TestPyPI](https://github.com/MyPyDavid/raman-fitting/actions/workflows/upload-to-testpypi.yml/badge.svg)](https://github.com/MyPyDavid/raman-fitting/actions/workflows/upload-to-testpypi.yml)

<p align="center" width="100%">
  <img src="https://user-images.githubusercontent.com/13996213/140090631-ed7c9f51-7630-49b6-9081-fb0675a5a4c9.png" alt="raman_cover_img"  width="200px" height="100px"/>
</p>


# raman-fitting
 A Python framework that performs a deconvolution on typical parts of interest on the spectrum of carbonaceous materials.
 The deconvolutions are done with models which are composed of collections of lineshapes or peaks that are typically assigned to these spectra in scientific literature.

In batch processing mode this package will index the raman data files in a chosen folder.
First, it will try to extract a sample ID and position number from the filenames and create an index of the files in a dataframe. Over this index a preprocessing, fitting and exporting loop will start.
There are several models, each with a different combination of typical peaks, used for fitting. Each individual typical peak is defined as a class in the deconvolution/default_models folder with some added literature reference in the docstring. Here, the individual peak parameter settings can also be easily adjusted for initial values, limits, shape (eg. Lorentzian, Gaussian and Voigt) or be fixed at certain initial values.
Export is done with plots and excel files for the spectral data and fitting parameters for further analysis.


### Example plots

https://github.com/MyPyDavid/raman-fitting/wiki


### Set up virtual environment and install the package

A release is now available on PyPI, installation can be done with these commands in a terminal.
``` bash
# Setting up and activating a virtual environment
python -m venv env # python 3.12 is recommended
source env/bin/activate

# Installation from PyPI
python -m pip install raman_fitting
```

#### From source installation

The following shows how to install the package from this source repository.
Download or clone this repository in a certain folder.
``` bash
git clone https://github.com/MyPyDavid/raman-fitting.git

# set up and activate venv ...

# regular install
python -m pip install raman-fitting/

# editable/develop mode
python -m pip install -e raman-fitting/
```

### Usage

#### Post installation test run

In order to test the package after installation, please try the following command in a terminal CLI.
``` bash
raman_fitting run examples
```
or these commands in the Python interpreter or in a Jupyter Notebook.
``` python
import raman_fitting
raman_fitting.make_examples()
```
This test run should yield the resulting plots and files in the following folder. Where home means the local user home directory depending on the OS.
``` bash
# Linux
home/.raman_fitting/example_results

# For Other OSs, log messages will show:
# Results saved in ...

```

#### Fitting your own datafiles
Place your data files in the default location or change this default setting in the config.
``` bash
home/.raman_fitting/datafiles
```
The following command will attempt the indexing, preprocessing, fitting and plotting on all the files found in this folder.
``` bash
# default run mode is "normal" means over all the files found in the index
raman_fitting

# If you add a lot of files, try to check if the index is properly constructed
# before fitting them.
raman_fitting make index

# Location of index
home/.raman_fitting/datafiles/results/raman_fitting_index.csv
```

#### Datafiles

The raman data files should be .txt files with two columns of data values.
The first column should contain the Raman shift values and the second one the measured intensity.
Filenames will be parsed into a sampleID and position, in order to take the mean of the measured intensity
of several positions on the same sample.

An example of filename formatting and parsing result:
``` python
samplename1_pos1.txt => sampleID = 'samplename1', position = 1
sample2-100_3.txt => sampleID = 'sample2-100', position = 3
```
### Version

The current version is v0.8.0

### Dependencies

- python >= 3.12
- lmfit >= 1.2.0
- pandas >= 2.0.0
- scipy >= 1.10.1
- matplotlib >= 3.7.2
- numpy >= 1.24.2
