# Note that Barak (https://pypi.python.org/pypi/Barak) must be
# installed for this pipeline to work.

# Make a directory corresponding to a single nights observations of,
# and a sub-directory called raw/

mkdir 2011oct20
cd 2011oct20
mkdir raw

# copy all the raw files lbcb*fits and lbcr*fits from this night into raw/

# Then make a file summarizing all the info about the raw files. Note
# that fhdr is a scritp included with the Barak package.
fhdr -f raw/*.fits.gz INSTRUME OBJECT LBCOBNAM FILTER EXPTIME OBSRA OBSDEC > info

# Now make a directory above 2011oct20 called code/ and copy
# the LBC redux files into it.

# Run sort_LBC.py to identify and sort all of the raw exposures
python ../code/sort_LBC.py

# this will create an series of directories and sub-directories,
# separating exposures into type (bias/flat/object), chip (blue or
# red) and filter. Soft links to the relevant raw files are placed in
# individual raw/ directories under the different
# sub-directories. Above each of these raw/ directories is a list with
# all of the raw files listed. These lists are passed as input to the
# subsequent pipeline reduction scripts.

# The next step is to maked a combined bias image. One is needed for
# each chip (blue and red). Start with the red chip

cd bias/r/

# Copy the raw files we want to reduce (they will be overwritten by the pipeline)
cp raw/* .
# if they are gzipped, inflate them.
gunzip *.gz

# next we need to run iraf

###############
# Set up IRAF
###############

# open an iraf session          (can be inside a screen instance, cd ~/iraf then ecl)


# We're now inside IRAF. Load these packages:

mscred
stsdas
playpen

# tell iraf where to find the pipeline iraf scripts
task lacos_im="/data/LBC/nhmc_reduction_code/lacos_im.cl"
task do_lbc_red="/data/LBC/nhmc_reduction_code/do_lbc_red.cl"
#task lacos_im="/home/nhmc/code/python/LBC_redux/lacos_im.cl"
#task do_lbc_red="/home/nhmc/code/python/LBC_redux/do_lbc_red.cl"

# set some variables
mscred.backup="none"

do_lbc_red.trimnover=no
do_lbc_red.trimlist="List.alltrim"
do_lbc_red.bias=no
do_lbc_red.biaslist="List.bias"
do_lbc_red.biassub=no
do_lbc_red.twiflat=no
do_lbc_red.fringeframe=no
do_lbc_red.twilist="List.twiflat.edit"
do_lbc_red.fringelist="List.science"
do_lbc_red.flatdo=no
do_lbc_red.flatdolist="List.allobject"
do_lbc_red.fringedo=no
do_lbc_red.fringedolist="List.allobject"
do_lbc_red.saturcorr=no
do_lbc_red.bpmlist="List.bpmaskdirs"
do_lbc_red.crrays=no
do_lbc_red.addmasks=no
do_lbc_red.dowcs=no
do_lbc_red.catfile=""
do_lbc_red.mkweight=no
do_lbc_red.dobackup=no
do_lbc_red.weightfile="Flat.fits"
do_lbc_red.database="test_new.db"

# And run do_lbc_red to trim the overscan regions and produce a combined bias file

do_lbc_red trimlis=list biaslist=list trimnover+ biassub- bias+ twiflat- saturcorr- flatdo- fringeframe- fringedo- crrays- addmasks- dowcs- mkweight-

# repeat this process for the blue chip if necessary.

#
# trim overscan
# ccdproc(images="@list", output="",bpmasks="",noproc=no, merge=no,xtalkco=no,oversca=yes,trim=ye
# s,fixpix=no,zerocor=no,darkcor=no,flatcor=no,sflatco=no,biassec='!biassec',trimsec='!trimsec',intera
# c=no)

# # make master bias
# zerocombine(input="@list",output="Finalbias",combine="average",reject="avsigclip",ccdtype="",\
# process=yes,delete=no,scale="none",statsec="*",nlow=1,nhigh=1,nkeep=2)

##########################################
# Next create Flat fields
##########################################

# now we use the combined bias to process the flat fields. This must
# be done for each filter.

# Again copy the raw files we want to reduce.

cd flat/rr/
cp raw/* .
gunzip *.gz

# link the relevant master bias to this directory, e.g.
ln -s ../../bias/r/Finalbias.fits .

# check that all the flat exposures in the list are good - you don't
# want to include any saturated twilifht flats, for example. 

# in iraf,  mscred

# trim overscan
ccdproc(images="@list", output="",bpmasks="",noproc=no, merge=no,xtalkco=no,oversca=yes,trim
=yes,fixpix=no,zerocor=no,darkcor=no,flatcor=no,sflatco=no,biassec='!biassec',trimsec='!trimsec',int
erac=no)

# subtract bias
ccdproc(images="@list", zerocor=yes,merge=no,zero="Finalbias.fits")

# make master flat - this creates 'Flat.fits'
flatcombine(input="@list", output="Flat", combine="median",reject="avsigclip",ccdtype="",pro
cess=no,delete=no,scale="mode",lsigma=3,hsigma=3,nlow=1,nhigh=1,nkeep=2)



#####################################
# Reduce science exposures
#####################################

# Now you can reduce the science exposures. Go to one of the object
# directories, copy the raw files again, and then make soft links to
# the relevant combiend bias and flat files.

cd object/rr/
cp raw/* .
gunzip *.gz
ln -s ../../flats/rr/Flat.fits .
ln -s ../../bias/r/Finalbias.fits .

# to do this for many filters there is an example helper script,
# prepare.py, that you can edit.

# This script copies over lbc.py that's used for subsquent steps. you
# may need to edit some paths in cp_reduction_files.sh
sh ../../cp_reduction_files.sh

# make a list of pixel mask filenames
sed s/\.fits/_bpm/ < list > list.bpmaskdirs

# this step should trim the overscan region, subtract the bias, doa
# flat field correction, a cosmic ray correction and make a weight
# image.  The cosmic ray rejection can take a long time (several
# minutes per image).

do_lbc_red trimnover+ biassub+ bias- twiflat- saturcorr+ flatdo+ fringeframe- fringedo- crrays- addmasks+ dowcs- mkweight+ trimlis=list flatdol=list bpmlist=list.bpmaskdirs
#do_lbc_red trimnover+ biassub+ bias- twiflat- saturcorr+ flatdo+ fringeframe- fringedo- crrays+ addmasks+ dowcs- mkweight+

# Now use cp_weights.py to make weight images that the astromatic
# programs (sextractor, scamp and swarp) understand
#python ../../cp_weights.py lbc*fits

# you can remove the temporary files (which take up a lot of space)
# with clean_crrays.sh.

# Now you're ready to run lbc.py. Take a look at run.sh for an example of how to use this.
 


#fhdr lbc?.????????.??????.fits LBCOBNAM EXPTIME


