#!/bin/bash


function min () {
    /home/xeowhyx/projet/l3l1/l3l1/bin/python /home/xeowhyx/projet/l3l1/code/pycoingecko/min.py
}


source ~/projet/l3l1/l3l1/bin/activate

while ((1))
      do
            echo "tps : $cpt"
            sleep 1
               ((cpt+=1))
            if (((cpt%60)==0));then
               min& #arriere plan
            fi
      done
      