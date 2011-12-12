for d in sci_J021857+08172 sci_J045142-13203 sci_J074437+20590 sci_J081240+32080 sci_J212916+00375 sci_SDSSJ2346-001;
  do
  for d1 in bUs bg rr ri;
    do
    cp $HOME/data/LBC/nhmc_reduction_code/lbc.py $d/$d1/;
    cp -r $HOME/data/LBC/nhmc_reduction_code/conf $d/$d1/;
  done
done