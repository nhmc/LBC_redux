#!/usr/bin/env python2.7
import os, argparse
from glob import glob
from commands import getoutput
from subprocess import call
import pyfits
from math import pi, cos, sin

def tweak_wcs(hd, pixscale=0.3):
    """ Change the header astrometry to a given pixel scale. Use
    IRAF-style CD?_? keyword pixscale units are arcsec/pix."""

    # HACK: all images get same pixscale
    #pixscale = sqrt(hd['CD1_1']^2 + hd['CD1_2']^2) # [deg/pixel]
    pixscale = pixscale / 3600.
    orientation = -(hd['CROTA1'] % 360.)

    theta = orientation * pi / 180.
    costheta = cos(theta)
    sintheta = sin(theta)
    #print -pixscale * costheta, -pixscale * sintheta, -pixscale * sintheta, pixscale * costheta
    hd.update('CD1_1', -pixscale * costheta, after='CTYPE2')
    hd.update('CD1_2', -pixscale * sintheta, after='CD1_1')
    hd.update('CD2_1', -pixscale * sintheta, after='CD1_2')
    hd.update('CD2_2',  pixscale * costheta, after='CD2_1')
    del hd['CDELT1']
    del hd['CDELT2']

def mask_bad_columns(d):
    d[:, 702:705] = 0
    d[:, 1050:1053] = 0
    d[:, 1067:1070] = 0
    d[:, 1383:1387] = 0
    return d

parser = argparse.ArgumentParser()
parser.add_argument(
    'filename_list', help='File containing list of input images, one per line.')
parser.add_argument(
    'extensions', default='1,2,3,4', help= 'Split input files into the '
    'requested extensions and do astrometry separately for each extension. '
    ' e.g.: 1,2')

# actions
parser.add_argument(
    '-copy', action='store_true', help='Copy images to the data directory '
    'and tweak header astrometry keywords.')
parser.add_argument(
    '-cat',  action='store_true', help='Use SExtractor to make catalogues '
    'from each image that are later used to correct astrometry.')
parser.add_argument(
    '-astrom', action='store_true', help=
    'Correct the astrometry with scamp by comparing to a reference catalogue. '
    'The updated astrometry transformation is saved in *.head files.')
parser.add_argument(
    '-mosaic', help='Combine the images using the correct astrometry '
    'with swarp. The argument is the name of the output mosaic file.')


############################
# Parameters
############################

##### used for all steps

# data directory is where we copy the data to and modify the headers, etc
# trailing slash required!
datapath = 'data/'
nthreads = 3
pixscale = 0.224

##### scamp 

parser.add_argument('-astref_catalog', default='SDSS-R7')
parser.add_argument('-astref_band', default='i')
parser.add_argument('-checkplot_dev', choices=('NULL','PNG','PSC'),
                    default='PSC')
parser.add_argument('-astrom_doall', action='store_true')
parser.add_argument('-crossid_radius', default='1')
parser.add_argument('-aheader_suffix', default='.ahead')
parser.add_argument('-astrefmag_key', default='MAG_AUTO')
#astref_catalog = 'FILE'
#astref_band = 'DEFAULT'
photinstru_key = 'FILTER'
magzero_key = 'PHOT_C'
extinct_key = 'PHOT_K'
photomflag_key = 'PHOTFLAG'
astrinstru_key = 'FILTER'
# or 'FIX_FOCALPLANE'
parser.add_argument('-mosaic_type', default='LOOSE')
# also INSTRUMENT
parser.add_argument('-stability_type', default='EXPOSURE')
parser.add_argument('-distort_degrees', default='3')

position_maxerr = '2.0'            # arcmin
posangle_maxerr = '3.0'            # degrees
# if your astrometry solution is bad, play with these:
parser.add_argument('-sn_thresholds', default='10.0,100.0')      
parser.add_argument('-fwhm_thresholds', default='3.0,50.0')            # pixels

##### swarp

mosaicpath = 'swarp/'
header_only = 'N'
coordtype = 'EQUATORIAL'    
gain_keyword = 'GAIN'
# keywords to copy to the final mosaic'd image
keywords = 'OBJECT,FILTER,SATURATE,RDNOISE,GAIN,EXPTIME,AIRMASS,TIME-OBS'

# here it might have been nice to add a keyword that was 1/exptime
# that we could use to scale the flux by.
scaleflux = 'NONE'   # otherwise FLXSCALE

# Choice of combinetype is less than ideal.  WEIGHTED uses the weight
# maps but may not eliminate outliers.  AVERAGE is not robust to left
# over cosmic ray residuals etc.  MEDIAN is robust and ought to work
# well if combining a reasonable number of images taken in roughly
# the same photometric conditions, but I worry about small numbers
# of images or other problems.  It would be nice to have the option
# of trimming outliers and then doing a weighted mean or average.
#    combinetype = 'WEIGHTED'
#    combinetype = 'CHI2' 
#    combinetype = 'AVERAGE' 
combinetype = 'MEDIAN' 

#################################################
# End of parameters
#################################################

#args = parser.parse_args('-make_mosaic foo'.split())
args = parser.parse_args()
args.extensions = map(int, args.extensions.split(','))

# the input file list
fh = open(args.filename_list)
infilenames = [r.strip() for r in fh if r.lstrip() and not r.lstrip().startswith('#')]
fh.close()
print len(infilenames), 'files found in', args.filename_list

# make a list of images
imagenames = []
for n in infilenames:
    for iext in args.extensions:
        imagenames.append(n.replace('.fits', '_%i.fits' % iext))

if args.copy:
    # copy (or link) the required images to the datapath directory
    if not os.path.lexists(datapath):
        print 'Creating', datapath
        call('mkdir -p ' + datapath, shell=1)

    CDkeys = set(['CD1_2', 'CD1_2','CD2_1', 'CD2_2'])
    print ('Splitting extensions %s and copying to %s' % (
        args.extensions, datapath))
    for n in infilenames:
        fh = pyfits.open(n)
        fw = pyfits.open(n.replace('.fits', '.weight.fits'))
        hd = fh[0].header
        for iext in args.extensions:
           # copy the image
            fhout = pyfits.HDUList([fh[0], fh[iext]])

            # if old data, force the pixel scale to be that in the
            # primary header
            if CDkeys.difference(fhout[1].header.keys()):
                print '  Tweaking wcs'
                tweak_wcs(fhout[1].header, pixscale)
            fhout[0].header['NEXTEND'] = 1
            n1 = n.replace('.fits', '_%i.fits' % iext)
            print 'Writing', datapath + n1
            fhout.writeto(datapath + n1, clobber=True)
            # and the corresponding weight image
            fwout = pyfits.HDUList([fw[0], fw[iext]])
            fwout[0].header['NEXTEND'] = 1
            n1 = n.replace('.fits', '_%i.weight.fits' % iext)
            if iext == 1 and 'lbcb' in n1:
                print '  Masking bad columns'
                fwout[1].data = mask_bad_columns(fwout[1].data)
            print 'Writing', datapath + n1
            fwout.writeto(datapath + n1, clobber=True)
        fh.close()
        fw.close()

if args.cat:
    # generate SExtractor catalogs to be used by scamp for astrometric
    # matching
    template = ('sex %s -c conf/lbc.sex -CATALOG_NAME %s '
                ' -PARAMETERS_NAME conf/lbc.param '
                ' -FILTER_NAME conf/default.conv '
                ' -DETECT_THRESH 2.0 -ANALYSIS_THRESH 2.0 '
                ' -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_IMAGE %s -WEIGHT_THRESH 0')
    
    for imagename in imagenames:
        n = datapath + imagename
        catname = n.replace('.fits', '.cat')
        weightname = n.replace('.fits', '.weight.fits')
        s = template % (n, catname, weightname)
        print s
        call(s, shell=1)


if args.astrom:

    # use the catalogues above and a reference catalogue
    # astref_catalog, to be downloaded, to do corrections to the
    # astrometry. The corrections are saved to *.head files

    s = ('scamp %s -c conf/lbc.scamp ' +
         ' -CHECKPLOT_DEV ' + args.checkplot_dev + 
         ' -POSANGLE_MAXERR ' + posangle_maxerr +
         ' -POSITION_MAXERR ' + position_maxerr +
         ' -ASTREF_CATALOG ' + args.astref_catalog +
         ' -ASTREF_BAND ' + args.astref_band +
         ' -AHEADER_SUFFIX ' + args.aheader_suffix + 
         ' -SN_THRESHOLDS ' + args.sn_thresholds +
         ' -FWHM_THRESHOLDS ' + args.fwhm_thresholds + 
         ' -SAVE_REFCATALOG Y -MOSAIC_TYPE ' + args.mosaic_type +
         ' -STABILITY_TYPE ' + args.stability_type +
         ' -CROSSID_RADIUS ' + args.crossid_radius +
         ' -DISTORT_DEGREES ' + args.distort_degrees +
         ' -ASTREFMAG_KEY ' + args.astrefmag_key + 
         ' -CDSCLIENT_EXEC aclient_cgi' +
         ' -ASTRINSTRU_KEY ' + astrinstru_key +
         ' -NTHREADS ' + str(nthreads) + ' -VERBOSE_TYPE LOG ')

    output = ['For more details see scamp_?.log files']
    if args.astrom_doall:
        print '##### Doing astrometry for all extensions at once! #####'
        outdir = 'scamp'
        if not os.path.lexists(outdir):
            print 'Creating', outdir
            call('mkdir -p ' + outdir, shell=1)

        catnames = []
        for iext in args.extensions:
            catnames.extend([datapath + n.replace('.fits','_%i.cat' % iext)
                             for n in infilenames])
        catnames = ' '.join(catnames)
        print s % catnames
        S = getoutput(s % catnames + '2>&1 | tee %s/scamp.log' % outdir)
        i = S.index('----- Astrometric stats (internal)')
        i = i + S[i:].index('           dAXIS1')
        j = i + S[i:].index('----- Astrometric stats (external):')
        output.append(
            '###                                   All | High S/N')
        output.extend([r for r in S[i:j].split('\n') if r.strip()])
        i = i + S[i:].index('----- Astrometric stats (external)')
        i = i + S[i:].index('Group')
        j = i + S[i:].index('----- Photometric clipping:')
        output.extend([r for r in S[i:j].split('\n') if r.strip()])
        if glob('*.png'):
            call('mv *.png ' + outdir, shell=1)
        if glob('*.ps'):
            call('mv *.ps ' + outdir, shell=1)
        
    else:
        for iext in args.extensions:
            outdir = 'scamp%i' % iext
            if not os.path.lexists(outdir):
                print 'Creating', outdir
                call('mkdir -p ' + outdir, shell=1)
    
            catnames = ' '.join([datapath + n.replace('.fits','_%i.cat' % iext)
                                 for n in infilenames])
            print s % catnames
            S = getoutput(s % catnames + '2>&1 | tee %s/scamp.log' % outdir)
            i = S.index('----- Astrometric stats (internal)')
            i = i + S[i:].index('           dAXIS1')
            j = i + S[i:].index('----- Astrometric stats (external):')
            output.append(
                '### Extension %i                      All | High S/N' % iext)
            output.extend([r.replace('Group  1', 'Internal')
                           for r in S[i:j].split('\n') if r.strip()])
            i = i + S[i:].index('----- Astrometric stats (external)')
            i = i + S[i:].index('Group')
            j = i + S[i:].index('----- Photometric clipping:')
            output.extend([r.replace('Group  1', 'External')
                           for r in S[i:j].split('\n') if r.strip()])
            if glob('*.png'):
                call('mv *.png ' + outdir, shell=1)
            if glob('*.ps'):
                call('mv *.ps ' + outdir, shell=1)
    
    fh = open('astrometry.log', 'w')
    fh.write('\n'.join(output))
    fh.close()


    # Note that if scamp fails to find a photometric solution, the 
    # FLXSCALE in the *.head files will be NAN.  This is a pain.
    # We could try to test for this and (a) issue warnings, (b)
    # set the FLXSCALE to something useful like 1/EXPTIME ?
    # in the meantime, you can combine those with scaleflux=True
    # in the command line options.


if args.mosaic is not None:
    # use the astrometry corrects in the *.head files to warp all the
    # images and combine into a single mosaic image.
    if not os.path.lexists(mosaicpath):
        os.makedirs(mosaicpath)

    mosaic_file = mosaicpath + args.mosaic
    mosaic_weightfile = mosaic_file.replace('.fits','.weight.fits')
    inputnames = ','.join([datapath + n for n in imagenames])

    s = ('swarp ' + inputnames + ' -c conf/lbc.swarp ' + 
         ' -IMAGEOUT_NAME ' + mosaic_file + ' -RESAMPLE_DIR ' + mosaicpath +
         ' -WEIGHTOUT_NAME ' + mosaic_weightfile +
         ' -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_SUFFIX .weight.fits ' + 
         ' -WEIGHT_THRESH 0 -HEADER_SUFFIX .head' +
         ' -COMBINE_TYPE ' + combinetype +
         ' -BLANK_BADPIXELS Y -CELESTIAL_TYPE ' + coordtype +
         ' -GAIN_KEYWORD ' + gain_keyword +
         ' -FSCALE_KEYWORD ' + scaleflux + ' -FSCALE_DEFAULT 1.0' +
         ' -COMBINE_BUFSIZE 1024 -COPY_KEYWORDS ' + keywords +
         ' -VERBOSE_TYPE NORMAL -NTHREADS ' + str(nthreads))
    print s
    call(s, shell=True)

# Add a constant background back to the mosaic, based on the mean bg
# measured by swarp.  This currently assumes that swarp normalized to
# e-/sec and it should do something more intelligent like looking at
# flxscale?

    rnames = []
    for n in imagenames:
        n1 = n.replace('.fits', '.0001.resamp.fits')
        rnames.append(mosaicpath + n1)


    # find the mean background level in all the input resampled images
    bgvals = []
    for n in rnames:        
        #print pyfits.getval(n, 'BACKMEAN')
        bgvals.append(pyfits.getval(n, 'BACKMEAN'))
        # while we're here, delete the weight file
        wname = n.replace('.fits', '.weight.fits')
        call('rm ' + wname, shell=1)

    bgmean = sum(bgvals) / len(bgvals)

# this line from the idl program, no idea what it means.
# 
# if swarp normalizes the output into e-/sec, do the same with the 
# background we are adding back; divide by tottime*4 (because 4 chips)


    # add the measured mean bg to the mosaic image.
    fh = pyfits.open(mosaic_file)
    mosaicim = fh[0].data
    mosaicim_wght = pyfits.getdata(mosaic_weightfile)
    mosaicim += float(bgmean)

    # What to do where there is no good data?  If we set it to 0, then
    # it puts holes in saturated stars, which is annoying.  Perhaps
    # best to set it to 1e+5.     
    mosaicim[mosaicim_wght < 1e-5] = 1e5

    # total exposure time
    Next = len(args.extensions)
    exptot = sum([pyfits.getval(datapath + n, 'EXPTIME') for
                  n in imagenames[::Next]])
    print 'tottime, backmean = ', exptot, bgmean

    # add in the number of images and other info to the header
    hd = fh[0].header
    hd.update('NUMIMG', len(infilenames), comment='Number of input images')
    hd.update('TOTTIME',  exptot, comment='Total Exposure time')
    hd.update('AVGTIME',  exptot/len(infilenames), comment='Avg Exposure time')
    hd.update('BACKMEAN', bgmean, comment='Mean background')
    fh.writeto(mosaic_file, clobber=True)
    fh.close()
