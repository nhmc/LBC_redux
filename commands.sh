# do once per directory

cd /home/nhmc/data/LBC/2011oct

mkdir raw
# copy all files from this night to raw/
# make a file with all the info about the raw files.
fhdr -f raw/*.fits.gz INSTRUME OBJECT LBCOBNAM FILTER EXPTIME OBSRA OBSDEC > info

# run sort_LBC.py

cd object/bUs/
cp raw/* .
gunzip *.gz
ln -s ../../flats/bUs/Flat.fits .
ln -s ../../bias/b/Finalbias.fits .
sh ../../cp_reductionfiles.sh

# open an iraf session (inside a screen instance, cd ~/iraf then ecl)
# packages stsdas playpen and mscred should be loaded
task lacos_im="/home/crighton/data/LBC/20090920/bBias/lacos_im.cl"
task do_lbc_red="/home/crighton/data/LBC/20090920/bBias/do_lbc_red.cl"

# mscred.backup="none"

# epar do_lbc_red

# do_lbc_red.trimnover=no
# do_lbc_red.trimlist="List.alltrim"
# do_lbc_red.bias=no
# do_lbc_red.biaslist="List.bias"
# do_lbc_red.biassub=no
# do_lbc_red.twiflat=no
# do_lbc_red.fringeframe=no
# do_lbc_red.twilist="List.twiflat.edit"
# do_lbc_red.fringelist="List.science"
# do_lbc_red.flatdo=no
# do_lbc_red.flatdolist="List.allobject"
# do_lbc_red.fringedo=no
# do_lbc_red.fringedolist="List.allobject"
# do_lbc_red.saturcorr=no
# do_lbc_red.bpmlist="List.bpmaskdirs"
# do_lbc_red.crrays=no
# do_lbc_red.addmasks=no
# do_lbc_red.dowcs=no
# do_lbc_red.catfile=""
# do_lbc_red.mkweight=no
# do_lbc_red.dobackup=no
# do_lbc_red.weightfile="Flat.fits"
# do_lbc_red.database="test_new.db"

sed s/\.fits/_bpm/ < list > list.bpmaskdirs
do_lbc_red trimnover+ biassub+ bias- twiflat- saturcorr+ flatdo+ fringeframe- fringedo- crrays+ addmasks+ dowcs- mkweight+

python ../../cp_weights.py lbc*fits

fhdr lbc?.????????.??????.fits LBCOBNAM EXPTIME
# make lists of the files you want to combine. e.g. list.deep

# cd to reduce directory

# unlearn do_lbc_red

# # do_lbc_red sets the lacos_im parameters, so you don't really need this
# lacos_im.gain=1.6
# lacos_im.readn=8.0
# lacos_im.sigclip=4.5
# lacos_im.sigfrac=0.3
# lacos_im.objlim=1.0
# lacos_im.niter=2

# # Get rid of any old backups
# imdel trim/*.fits,bias/*.fits,flat/*.fits,satur/*.fits,fringe/*.fits,crrays/*.fits

# # Copy original images if you want a backup - skip this step if you
# # have them nearby on disk
# # mscred will do this if you have mscred.backup="once"
# # changed do_lbc_red.cl so it does not override your setting of backup
# ## cp lbcr.*.fits Raw

# # Do processing, first up to the flat field

# do_lbc_red.mkweight=no
# do_lbc_red.trimnover=yes
# #do_lbc_red.trimlist="List.alltrim"
# do_lbc_red.bias=yes
# #do_lbc_red.biaslist="List.bias"
# do_lbc_red.biassub=yes
# do_lbc_red.twiflat=yes
# do_lbc_red.fringeframe=no
# #do_lbc_red.twilist="List.twiflat.edit"
# #do_lbc_red.fringedolist="List.allobject"
# do_lbc_red.flatdo=yes
# #do_lbc_red.flatdolist="List.allobject"
# do_lbc_red.fringedo=no
# do_lbc_red.saturcorr=yes
# do_lbc_red.crrays=no

# do_lbc_red trimnover+ biassub+ bias+ twiflat+ saturcorr+ flatdo+ fringeframe- fringedo- crrays- addmasks- dowcs- mkweight-

# # This will try to match up subsets of the data based on the 
# # filter, e.g. it matches the R images to the R flat.  If any
# # filter header fields are missing or inconsistent it will balk,
# # and you have to edit the image header filter field to be
# # correct and try again.

# # I was only processing images all taken in one filter so 
# # Flat.fits is just for that filter

# # Make weights after Flat.fits exists

# do_lbc_red.bias=no
# do_lbc_red.biassub=no
# do_lbc_red.twiflat=no
# do_lbc_red.flatdo=no
# do_lbc_red.saturcorr=no
# do_lbc_red.mkweight=yes

# do_lbc_red trimnover- biassub- bias- twiflat- saturcorr- flatdo- fringeframe- fringedo- crrays- addmasks- dowcs- mkweight+

# # Make fringe frame and do subtraction.  The fringe frame is a
# # stack of scaled images, so you need enough dithers or different
# # pointings that all the objects get clipped out and it's just
# # making a supersky.  This is then scaled to the sky in each of
# # your images and subtracted (not divided).
# # If you have images with something big and # bright (like an 
# # NGC galaxy) you may want to exclude them from the fringelist,
# # although you still want them in the fringedolist, which is the
# # list of images to correct.

# do_lbc_red.bias=no
# do_lbc_red.twiflat=no
# do_lbc_red.fringeframe=yes
# #do_lbc_red.fringelist="List.egsregular"
# #do_lbc_red.fringedolist="List.allobject"
# do_lbc_red.fringedo=yes
# do_lbc_red.mkweight=no

# # This first does the combine, then a median which takes a while, then you
# # have to hit return when rmfringe prompts for list of bad data masks

# do_lbc_red trimnover- biassub- bias- twiflat- saturcorr- flatdo- fringeframe+ fringedo+ crrays- addmasks- dowcs- mkweight-

# # Do crrays the list to do is same as fringedolist
# # This will take a long time - about 8-9 minutes per image, on my desktop

# # Make sure you have a bunch of free disk space because the tasks are
# # splitting up multi extension images and will put them back together
# # after addmasks, so if it dies part way through the data will be
# # in a confused state and you may want to start over (since everything
# # but crrays is fairly fast)

# do_lbc_red.fringeframe=no
# do_lbc_red.fringedo=no
# #do_lbc_red.fringedolist="List.allobject"
# do_lbc_red.crrays=yes
# do_lbc_red.addmasks=yes

# do_lbc_red trimnover- biassub- bias- twiflat- saturcorr- flatdo- fringeframe- fringedo- crrays+ addmasks+ dowcs- mkweight-

# # This leaves a lot of clutter files like bpmlbcr.20080601.053248_final_2.pl
# # in both the parent and the _bpm directory unfortunately.

# ----------

# Now we have a bunch of reduced images - flattened, defringed, and 
# cosmic ray cleaned - and need to astrometrically calibrate and
# stack them.  I did not have much luck with the mscred task that
# supposedly can do this, msccmatch.  scamp and swarp worked well
# although they may require some tuning of parameters.

# Make some lists of images to combine, for example I made

# List.egspointing1
# List.egspointing2
# List.egspointing4
# List.egspointing5

# put this list of pointings in list.list-of-pointings
# and make some names for output files.  Again you want to do
# this one filter at a time.

# sed s/List.// < list.list-of-pointings | awk '{print $1".mos.fits"}' \
#   > list.list-of-mosaics

# Run bjw_egs_scampswarp.pro on each of these lists:

# csh
# idl
# .com bjw_egs_scampswarp.pro

# do one as a test
# bjw_egs_scampswarp, 'List.egspointing4',preproc=1,sextractor=1,scamp=1, $
#     swarp=1,psf_find=1,finfile='egspointing4.mos.fits',nofluxscale=1, $
#     astref_band='r'

# As written this is trying to match to SDSS R-band, so if your
# images are something else or not in the SDSS footprint you should
# adjust the arguments astref_band, astref_catalog, etc.

# I set nofluxscale=1 to avoid using the scaling computed by
# SCAMP to normalize images when combining

# The output of this is an astrometrically calibrated and
# combined stack image, which includes an extension that gives
# pixel weights.  Currently it's telling swarp to do a median
# combine - see "combinetype" in the scampswarp.pro file for
# where this is set.

# It also tries to report something about the PSF of the 
# combined image, but this is kind of hokey.

# How to do a list of pointings:

# readcol,'list.list-of-pointings',ptgfilenames,format='A'
# readcol,'list.list-of-mosaics',mosfilenames,format='A'
# numfiles = n_elements(ptgfilenames)

# for i = 0, numfiles-1 do $
#   bjw_egs_scampswarp, ptgfilenames[i],preproc=1,sextractor=1,scamp=1, $
#     swarp=1,psf_find=1,finfile=mosfilenames[i],nofluxscale=1, $
#     astref_band='r'

# Be sure to look at the scamp output to verify that it's finding
# decent solutions for all the chips in all the images.  Sometimes
# one goes bad and you may have to adjust scamp parameters.  This
# also depends on how far off the initial guess of RA, Dec, 
# orientation in the original headers is.

