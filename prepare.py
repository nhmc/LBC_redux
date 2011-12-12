from glob import glob
from subprocess import call

dirs = 'bg bUs ri rr'.split()

for d in dirs:
    names = sorted(glob(d + '/raw/*gz'))
    for n in names:
        n1 = n.split('/')[-1].replace('.gz','.fz')
        s = 'ln -s ../../../raw/' + n1 + ' ' + d + '/raw/' + n1
        print s
        call(s,shell=1)

    s = 'funpack '+ d + '/raw/*.fz'
    print s
    call(s, shell=1)
    s = 'mv '+ d + '/raw/*.fits ' + d 
    print s
    call(s, shell=1)

call('ln -s ../../bias/b/Finalbias.fits bg/', shell=1)
call('ln -s ../../bias/b/Finalbias.fits bUs/', shell=1)
call('ln -s ../../bias/r/Finalbias.fits rr/', shell=1)
call('ln -s ../../bias/r/Finalbias.fits ri/', shell=1)

call('ln -s ../../old_flats/bg/Flat.fits bg/', shell=1)
call('ln -s ../../old_flats/bUs/Flat.fits bUs/', shell=1)
call('ln -s ../../old_flats/rr/Flat.fits rr/', shell=1)
call('ln -s ../../old_flats/ri/Flat.fits ri/', shell=1)

D = "/home/crighton/data/LBC/nhmc_reduction_code/"
for d in dirs:
    call('cp -r ' + D + '/conf ' + d, shell=1)
    call('cp -r ' + D + '/run.sh ' + d, shell=1)
    call('cp -r ' + D + '/lbc.py ' + d , shell=1)

for d in dirs:
    s = r'sed s/\.fits/_bpm/ < '+d+'/list > '+d+'/list.bpmaskdirs'
    print s
    call(s,shell=1)
