#quick look
fhdr lbc?.????????.??????.fits LBCOBNAM EXPTIME
# make lists
filterfits LBCOBNAM_notcontains_wid EXPTIME_gt_150 lbc?.????????.??????.fits > List.deep
#filterfits EXPTIME_lt_150 lbc?.????????.??????.fits > List.short100
filterfits EXPTIME_gt_150 lbc?.????????.??????.fits > List.deep
filterfits EXPTIME_lt_150 lbc?.????????.??????.fits > List.short
#filterfits LBCOBNAM_contains_sho lbc?.????????.??????.fits > List.short10
#filterfits LBCOBNAM_contains_wid lbc?.????????.??????.fits > List.wide
