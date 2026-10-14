@echo off
echo RESULTS > FAILURES.TXT
copy keyrus.com saved.com > NUL
base /fast=off > T01.TXT
if errorlevel 1 echo FAIL 01 unexpected high error >> FAILURES.TXT
probe > T02.TXT
if errorlevel 1 echo FAIL 02 unexpected high error >> FAILURES.TXT
base /release > T03.TXT
if errorlevel 1 echo FAIL 03 unexpected high error >> FAILURES.TXT
keyrus /8x8=off /8x14=off /8x16=off /fast=off > T04.TXT
if errorlevel 2 echo FAIL 04 unexpected high error >> FAILURES.TXT
if not errorlevel 1 echo FAIL 04 expected error >> FAILURES.TXT
keyrus @LONG.CFG > T05.TXT
if errorlevel 2 echo FAIL 05 unexpected high error >> FAILURES.TXT
if not errorlevel 1 echo FAIL 05 expected error >> FAILURES.TXT
keyrus @OVER.CFG > T06.TXT
if errorlevel 2 echo FAIL 06 unexpected high error >> FAILURES.TXT
if not errorlevel 1 echo FAIL 06 expected error >> FAILURES.TXT
keyrus /keys=BIG.KBD > T07.TXT
if errorlevel 2 echo FAIL 07 unexpected high error >> FAILURES.TXT
if not errorlevel 1 echo FAIL 07 expected error >> FAILURES.TXT
keyrus /files > T08.TXT
if errorlevel 1 echo FAIL 08 unexpected high error >> FAILURES.TXT
keyrus /fast=off /color=0,0 /beep=off /lamp=off > T09.TXT
if errorlevel 1 echo FAIL 09 unexpected high error >> FAILURES.TXT
probe > T10.TXT
if errorlevel 1 echo FAIL 10 unexpected high error >> FAILURES.TXT
keyrus /fast=off /scan=54 > T11.TXT
if errorlevel 1 echo FAIL 11 unexpected high error >> FAILURES.TXT
keyrus /fast=off /scan=29p > T12.TXT
if errorlevel 1 echo FAIL 12 unexpected high error >> FAILURES.TXT
probe scan > T13.TXT
if errorlevel 1 echo FAIL 13 unexpected high error >> FAILURES.TXT
keyrus /fast=off /lat=42 > T14.TXT
if errorlevel 1 echo FAIL 14 unexpected high error >> FAILURES.TXT
keyrus /fast=off /lat=off > T15.TXT
if errorlevel 1 echo FAIL 15 unexpected high error >> FAILURES.TXT
probe scan > T16.TXT
if errorlevel 1 echo FAIL 16 unexpected high error >> FAILURES.TXT
hook > T17.TXT
if errorlevel 1 echo FAIL 17 unexpected high error >> FAILURES.TXT
keyrus /release > T18.TXT
if errorlevel 2 echo FAIL 18 unexpected high error >> FAILURES.TXT
if not errorlevel 1 echo FAIL 18 expected error >> FAILURES.TXT
probe > T19.TXT
if errorlevel 1 echo FAIL 19 unexpected high error >> FAILURES.TXT
hook /u > T20.TXT
if errorlevel 1 echo FAIL 20 unexpected high error >> FAILURES.TXT
keyrus /release > T21.TXT
if errorlevel 1 echo FAIL 21 unexpected high error >> FAILURES.TXT
keyrus /fast=off /delay_init > T22.TXT
if errorlevel 1 echo FAIL 22 unexpected high error >> FAILURES.TXT
keyrus /fast=off /scan=29p /keys=GOOD.KBD > T23.TXT
if errorlevel 1 echo FAIL 23 unexpected high error >> FAILURES.TXT
probe scan > T24.TXT
if errorlevel 1 echo FAIL 24 unexpected high error >> FAILURES.TXT
keyrus /release > T25.TXT
if errorlevel 1 echo FAIL 25 unexpected high error >> FAILURES.TXT
keyrus /fast=off /all /keys=GOOD.KBD /font=_08x16.fnt > T26.TXT
if errorlevel 1 echo FAIL 26 unexpected high error >> FAILURES.TXT
probe > T27.TXT
if errorlevel 1 echo FAIL 27 unexpected high error >> FAILURES.TXT
keyrus /fast=off /font=_08x16.fnt > T28.TXT
if errorlevel 1 echo FAIL 28 unexpected high error >> FAILURES.TXT
keyrus /release > T29.TXT
if errorlevel 1 echo FAIL 29 unexpected high error >> FAILURES.TXT
saved /scan=54 /save > T30.TXT
if errorlevel 1 echo FAIL 30 unexpected high error >> FAILURES.TXT
saved /? > T31.TXT
if errorlevel 1 echo FAIL 31 unexpected high error >> FAILURES.TXT
saved /fast=off > T32.TXT
if errorlevel 1 echo FAIL 32 unexpected high error >> FAILURES.TXT
probe > T33.TXT
if errorlevel 1 echo FAIL 33 unexpected high error >> FAILURES.TXT
saved /release > T34.TXT
if errorlevel 1 echo FAIL 34 unexpected high error >> FAILURES.TXT
keyrus /fast=off /rom /8x8=off /8x14=off /8x16=off > T35.TXT
if errorlevel 1 echo FAIL 35 unexpected high error >> FAILURES.TXT
probe > T36.TXT
if errorlevel 1 echo FAIL 36 unexpected high error >> FAILURES.TXT
keyrus /release > T37.TXT
if errorlevel 1 echo FAIL 37 unexpected high error >> FAILURES.TXT
keyrus > T38.TXT
if errorlevel 1 echo FAIL 38 >> FAILURES.TXT
probe > T39.TXT
if errorlevel 1 echo FAIL 39 >> FAILURES.TXT
keyrus /release > T40.TXT
if errorlevel 1 echo FAIL 40 >> FAILURES.TXT
keyrus /fast=off /blank=on /color=0,0 > T41.TXT
if errorlevel 1 echo FAIL 41 >> FAILURES.TXT
probe > T42.TXT
if errorlevel 1 echo FAIL 42 >> FAILURES.TXT
keyrus /release > T43.TXT
if errorlevel 1 echo FAIL 43 >> FAILURES.TXT
keyrus /fast=off > T44.TXT
if errorlevel 1 echo FAIL 44 >> FAILURES.TXT
keyrus /alt=56 > T45.TXT
if errorlevel 1 echo FAIL 45 >> FAILURES.TXT
keyrus /release > T46.TXT
if errorlevel 1 echo FAIL 46 >> FAILURES.TXT
keyrus /fast=off /alt=56 > T47.TXT
if errorlevel 1 echo FAIL 47 >> FAILURES.TXT
keyrus /alt=29 > T48.TXT
if errorlevel 1 echo FAIL 48 >> FAILURES.TXT
keyrus /release > T49.TXT
if errorlevel 1 echo FAIL 49 >> FAILURES.TXT
echo DONE > DONE.TXT
exit
