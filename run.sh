name=deep
band=DEFAULT    # USNO-B1:  Bj Rf In

# one extension to check everything works

#./lbc.py List.$name 1 -copy -cat  -astrom -astref_catalog USNO-B1 -astref_band $band
#./lbc.py List.$name 1 -astrom -astref_catalog USNO-B1 -astref_band $band
#./lbc.py List.$name 1 -copy -cat -astrom -astref_catalog SDSS-R7 -astref_band u

# split into extensions and generate SExtractor catalogues

#./lbc.py list.$name 1,2,3,4 -copy -cat

#./lbc.py list.$name 1,2,3,4 -cat

# remove SExtractor detections along bad columns in chip 1
#./clean_chip1_cat.py data/lbcb.*_1.cat
# correct astrometry by comparison to SDSS catalogues. After this step
# check the scamp*.log files to see that the internal astrometry is
# reasonable. It should be ~0.1" or less, for all and high S/N sample.

# ./lbc.py list.$name 3 -astrom -astref_catalog FILE \
# -astref_band $band -astrefmag_key MAG \    #-sn_thresholds 2,500 \


#./lbc.py list.$name 1,2,3,4 -astrom -astref_catalog SDSS-R7 \
#-crossid_radius 1

# -astref_band $band -aheader_suffix .head \
#  -stability_type INSTRUMENT \
#  -mosaic_type FIX_FOCALPLANE
#-sn_thresholds 30,100
# -astrom_doall \
#-distort_degrees 4\

# combine the images using the corrected astrometry into a file called
# mosaic.fits.

./lbc.py list.$name 1,2,3,4 -mosaic mos_$name\_med.fits
