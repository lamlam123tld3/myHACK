#!/usr/bin/python

#**************************************
#
# date: 20160918
#
#**************************************
#
# Usage: (1) python y.py input.flv       [detect discontinuousness in video tags and audio tags]
#        (2) python y.py input.flv -l    [log all tag's info into input.flv.txt]     
#
#**************************************

from struct import *
from sys import exit
import sys
import binascii

#
# Global Configuration
#
# 25fps
# Tag 8 : Audio tag
# Tag 9 : Video tag
# Tag 18: Metadata tag
valid_gap = {
                8: [0, 21, 22, 23, 24, 25],
                9: [0, 36, 37, 38, 39, 40, 41, 42, 43, 44]
            };
typeName = {8: 'A', 9: 'V', 18: 'S'};
OUTPUT_LOG = False;


def calTimeDiff(curr,start):
    dif = int((curr - start)/1000) if start >= 0 else 0;
    m, s = divmod(dif, 60);
    hr, m = divmod(m, 60);
    return "%2d:%02d:%02d" % (hr, m, s);
    
def intToHex(int):
    return format(int,'X');

def parseTags(f, outputlog = False):
    lasta, lastv, starta, startv, start = 0, 0, -50, -50, -50;
    lastapos = lastvpos = 0;
    startFlag8 = startFlag9 = False;
    
    while True:
        pos = f.tell();
        TagHeader = f.read(11);
        
        if len(TagHeader) < 11:
            break;
        
        if TagHeader[0:9] == 'FLV\x01\x05\x00\x00\x00\x09':
            f.read(2); 
            if lasta > 0 and lastv > 0:
                print "[%d, %s, %9s]" % (lasta,calTimeDiff(lasta,starta), intToHex(pos));
            print "T       Last       Curr       Diff      Time    LastPos    CurrPos";
            print "New FLV";
            lasta, lastv, starta, startv, start = 0, 0, -50, -50, -50;
            startFlag8 = startFlag9 = False;
            continue;
        
        tagType = unpack('B',TagHeader[0])[0];
        dataSize = unpack('>I','\x00' + TagHeader[1:4])[0];
        timeStamp = unpack('>I',TagHeader[7] + TagHeader[4:7])[0];
        payload = f.read(dataSize);
        preTagSize = f.read(4);
        
        if outputlog == True:
            add = (('1' if payload[0] == '\x17' else '2') if tagType == 9 else ' ') if len(payload) > 0 else ' ';
            print >> flog, "%s %s %10d %8s %10d %9s" % (typeName[tagType] + add, calTimeDiff(timeStamp,start), timeStamp, binascii.b2a_hex(TagHeader[4:8]), dataSize, intToHex(pos));
        
        if len(preTagSize) < 4:
            break;
               
        if tagType == 18:
            print "Tag18 {%d, %s, %s}" % (timeStamp,calTimeDiff(lasta,starta),intToHex(pos));
             
        elif tagType == 8:
            if starta == -50:
                if startFlag8 == False and dataSize in [1,2,3,4]:  
                    startFlag8 = True;
                elif startFlag8 == True:
                    starta = lasta = timeStamp;
                    if start == -50:
                        start = timeStamp;
            elif abs(timeStamp - lasta) not in valid_gap[tagType]:
                print "A %10d %10d %10d  %s %10s %10s" % (lasta,timeStamp,timeStamp-lasta,calTimeDiff(lasta,starta),intToHex(lastapos),intToHex(pos));
                # timestamp reset
                if timeStamp + 1000 < lasta:
                    starta = start = timeStamp;
            lasta, lastapos = timeStamp, pos;
            
        elif tagType == 9:
            if startv == -50:
                if startFlag9 == False and payload[0:2] == '\x17\x00': 
                    startFlag9 = True;
                elif startv == -50 and startFlag9 == True:
                    startv = lastv = timeStamp;
                    if start == -50:
                        start = timeStamp;
            elif abs(timeStamp - lastv) not in valid_gap[tagType]:
                print "V %10d %10d %10d  %s %10s %10s" % (lastv,timeStamp,timeStamp-lastv,calTimeDiff(lastv,startv),intToHex(lastvpos),intToHex(pos));
                # timestamp reset
                if timeStamp + 1000 < lastv:
                    startv = start = timeStamp;
            lastv, lastvpos = timeStamp, pos;
    
    print "[%d, %s, %9s]" % (timeStamp,calTimeDiff(timeStamp,start),intToHex(pos));
    
    return;  

    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: y.py [input.flv]"
        exit()
    outputlog = False;
    if len(sys.argv) == 3 and (sys.argv[1] == '-l' or sys.argv[2] == '-l'):
        outputlog = True;
        filename = sys.argv[(2 if sys.argv[1] == '-l' else 1)];
    else:
        filename = sys.argv[1];
    outputlog = outputlog or OUTPUT_LOG;
    f = open(filename,'rb')
    if outputlog == True:
        flog = open(filename + '.txt','w')
        print >> flog, "T      Time         TS    HexTS       Size       Pos"
        print >> flog, "===================================================="
    print "Start y.py Open :", f.name
    parseTags(f, outputlog)
    f.close()
    if outputlog == True:
        flog.close();