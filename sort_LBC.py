#!/usr/bin/env python
import pyfits
import sys,os
from subprocess import call
import textwrap
from glob import glob
from barak.io import loadobj, saveobj, writetxt

def makedir(dirname, clean=False):
    """ Make a directory only if it doesn't exist.

    If clean is True, remove any files in the directory if it already
    exists."""
    if not os.path.lexists(dirname):
        print 'Creating %s/' % dirname
        os.makedirs(dirname)
    else:
        if clean:
            call('rm %s/*' % dirname, shell=1)

# make shorter versions of names for naming directories
arm_str = {'LBC-RED':'r', 'LBC_BLUE':'b'}
filter_str = {'SDT_Uspec':'Us',
              'g-SLOAN':'g',
              'r-SLOAN':'r',
              'i-SLOAN':'i',
              'z-SLOAN':'z',
              'V-BESSEL':'V',
              'V-BESSEL(?)':'V',
              'R-BESSEL':'R',
              'B-BESSEL':'B',
              'I-BESSEL':'I',
              'U-BESSEL':'U'}


usage = """\
./sort_LBC.py

Use the header information in the input files to sort imaging targets
into directories for reduction. Soft links are made to the raw files
necessary for reduction in each directory.

All the raw fits files must be in a directory called raw/ in the
current directory!"""


if 1:
    filenames = glob('raw/*.fits*')

    if len(filenames) == 0:
        print usage
        sys.exit()
    print 'Reading', len(filenames), 'raw input files...'

    # types

    #use keywords HIERARCH ESO INS TPL ID, OBJECT and OBS NAME to identify them

    if os.path.lexists('_sort_LBC.sav'):
        d = loadobj('_sort_LBC.sav')
        biases = d['biases']
        objects = d['objects']
        flats = d['flats']

    else:
        # IMAGETYP

        # object
        # zero
        # flat
        # FOCUS

        # OBJECT

        # BinoBias
        # Flat
        # SkyFlat

        # DETECTOR

        # EEV-RED
        # EEV-BLUE

        # INSTRUME

        # LBC_BLUE
        # LBC_RED

        # FILTER

        # SDT_Uspec
        # u-SLOAN
        # g-SLOAN
        # r-SLOAN
        # i-SLOAN
        # z-SLOAN

        # separate by detector and arm
        biases = {}
        # group science objects by name and filter and arm
        objects = {}
        # flats by filter and arm
        flats = {}

        unused = []
        unknown = []

        for i,n in enumerate(filenames):
            i += 1
            print i
            if not i % 20:
                print i, n
            #print 'reading', n
            hd = pyfits.getheader(n)
            # bias
            imtype = hd['IMAGETYP']
            obj = hd['object']
            filter = hd['FILTER']
            arm = hd['INSTRUME']
            if imtype == 'zero' and obj == 'BinoBias':
                if arm not in biases:
                    biases[arm] = [n]
                else:
                    biases[arm].append(n)
            elif imtype == 'flat' and hd['NEXTEND'] == 4:
                if arm not in flats:
                    flats[arm] = {filter: [n]}
                elif filter in flats[arm]:
                    flats[arm][filter].append(n)
                else:
                    flats[arm][filter] = [n]
            elif imtype == 'object':
                if obj not in objects:
                    objects[obj] = {arm : {filter: [n]}}
                elif arm not in objects[obj]:
                    objects[obj][arm] = {filter: [n]}
                elif filter not in objects[obj][arm]:
                    objects[obj][arm][filter] = [n]
                else:
                    objects[obj][arm][filter].append(n)
            elif imtype == 'FOCUS' or \
                     imtype == 'flat' and hd['NEXTEND'] == 1:
                unused.append(n)
            else:
                unknown.append(n)

        print len(biases), 'biases'
        print len(objects), 'imaging targets found:'
        print ' ', '\n  '.join(textwrap.wrap(' '.join(objects)))
        print len(flats), 'flats found:'
        print ' ', '\n  '.join(textwrap.wrap(' '.join(flats)))
        print len(unknown), 'unidentified exposures:'
        print ' ', '\n  '.join(textwrap.wrap(' '.join(unknown)))
        saveobj('_sort_LBC.sav', dict(biases=biases,objects=objects,flats=flats))
        # could be a bug writing out an empty file?
        
        writetxt('sort_LBC_unused', [unused], overwrite=1)

if 1:
    # make links to the biases
    if len(biases) > 0:
        makedir('bias')
    for arm in biases:
        biasdir = 'bias/' + arm_str[arm]
        makedir(biasdir)
        makedir(biasdir + '/raw', clean=True)
        names = []
        for filename in sorted(biases[arm]):
            n = filename.rsplit('/')[-1]
            s = 'ln -s ../../../raw/%s %s/raw/%s' % (n, biasdir, n)
            call(s, shell=1)
            names.append(n.replace('.fits.gz', '.fits'))
        writetxt(biasdir + '/list', [sorted(names)], overwrite=1)

    s = "fhdr -f -p bias/*/raw/*.fits* OBJECT LBCOBNAM FILTER EXPTIME OBSRA OBSDEC > bias/info"
    print s
    call(s, shell=1)

if 1:
    # make links to the flats
    if len(flats) > 0:
        makedir('flats')
    for arm in flats:
        for filter in flats[arm]:
            names = []
            filtdir = 'flats/' + arm_str[arm] + filter_str[filter]
            makedir(filtdir)
            makedir(filtdir + '/raw', clean=True)
            for filename in sorted(flats[arm][filter]):
                n = filename.rsplit('/')[-1]
                s = 'ln -s ../../../raw/%s %s/raw/%s' % (n, filtdir, n)
                call(s, shell=1)
                names.append(n.replace('.fits.gz', '.fits'))
            writetxt(filtdir + '/list', [sorted(names)], overwrite=1)
    s = "fhdr -f -p flats/*/raw/*.fits* OBJECT LBCOBNAM FILTER EXPTIME OBSRA OBSDEC > flats/info"
    print s
    call(s, shell=1)

if 1:
    # make links to the science objects
    for obj in objects:
        objdir = 'sci_' + obj
        objdir.replace('/', '_').replace('\\', '_')
        makedir(objdir)
        for arm in objects[obj]:
            for filter in sorted(objects[obj][arm]):
                filtdir = objdir + '/' + arm_str[arm] + filter_str[filter]
                makedir(filtdir)
                makedir(filtdir + '/raw', clean=True)
                names = []
                for filename in objects[obj][arm][filter]:
                    n = filename.rsplit('/')[-1]
                    s = 'ln -s ../../../raw/%s %s/raw/%s' % (n, filtdir, n)
                    call(s, shell=1)
                    names.append(n.replace('.fits.gz', '.fits'))
                writetxt(filtdir + '/list', [sorted(names)], overwrite=1)
        s = "fhdr -f -p %s/*/raw/*.fits* OBJECT LBCOBNAM FILTER EXPTIME OBSRA OBSDEC > %s/info"
        print s % (objdir, objdir)
        call(s % (objdir, objdir), shell=1)
