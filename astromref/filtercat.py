import pyfits
import pylab as pl

fh = pyfits.open('astrefcat.cat')
d = fh[2].data
c0 = (d.FWHM_IMAGE < 50) & (d.FWHM_IMAGE > 3) & \
     (d.FLUX_AUTO / d.FLUXERR_AUTO > 10) & (d.FLAGS==0) & \
     (d.ELONGATION < 1.5)
fh[2].data = d[c0]
pl.plot(d.X_WORLD, d.Y_WORLD, 'b.')
pl.plot(d.X_WORLD[c0], d.Y_WORLD[c0], 'r.')
pl.axis('equal')

fh.writeto('astrefcat.cat', clobber=1)

pl.show()
