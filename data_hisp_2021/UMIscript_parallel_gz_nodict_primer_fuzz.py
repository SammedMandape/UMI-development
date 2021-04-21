# -*- coding: utf-8 -*-
"""
Author: Sammed Mandape
Purpose: This python code will extract UMI, DNA fragment containing STR, and 
primer, from read1 and read2 of the fastq files data generated by using QIAseq
DNA panel.
"""

import os
import re
import collections
import strfuzzy_primer_fuzz
import sys
import gzip
import resource

#TODO use argparse
# sys.argv - 1)read1_fastq, 2)read2_fastq, 3)consensus-fuzz, 4)primer-fuzz, 5)anchor-fuzz, 6)inputDirectory, 7)outputDirectory, 8)suffix_to_file_name

directory = sys.argv [6]
outputdir = sys.argv[7]
cs_fuzz_arg = sys.argv[3]
primer_fuzz_arg = sys.argv[4]
anchor_fuzz_arg = sys.argv[5]


#input primer file
file_primer = "PrimedAnchors.txt"

complement = {'A' : 'T', 'C' : 'G', 'T' : 'A', 'G' : 'C'}

def reverse_complement(seq):
    '''
    This function gives out a reverse complement of sequence
    @param seq - type of str 
        The input seqeunce to construct a reverse complement of
                
    @return bases - type of str
        Reverse complement of input sequence
    '''
    bases = list(seq)
    bases = ''.join(complement[base] for base in reversed(bases))
    return bases

# def getFastqNameR1R2(directory):
    # '''
    # It creates a dictionary of fastq filenames available in a directory. 
    # @param directory - type of str
        # Name of directory where all the fastq files are located
        
    # @retun filedict - type of dict
        # Dictionary of filenames where key is read1 and value is its respective
        # pair of read2
    # '''
    # filedict = {}
    # for filename in os.listdir(directory):
        # if filename.endswith("001.fastq"):
            # #if re.match(r'\d+-\d+_.*_R1_\d+\.fastq', filename) is not None:
            # filebegin = re.match(r'(.*-\d+_.*)_R1_(\d+\.fastq)', filename)
            # if filebegin is not None:
                # filebeginr1 = filebegin.group(1) + "_R1_001.fastq"
                # filebeginr2 = filebegin.group(1) + "_R2_001.fastq"
                # filedict[filebeginr1] = filebeginr2
    # return filedict

#filedict = getFastqNameR1R2(directory)


def dict_for_primer(file_primer):    
    ''' 
    This function constructs a dictionary of a primer file
    @param file_primer - type of str 
        The primer file with Locus, Chr, Pos, Strand, Primer, Anchor
        
    @return dict_primer_empt - type of dict
        Dictionary of primer file with pos as key and list of values
    '''
    dict_primer_empty = {}
    if not file_primer:
        raise SystemError("Error: Specify primer file name\n")
    with open(file_primer, 'r') as fh_primer:
        for line in fh_primer:
            (val1Locus, val2Chr, keyPos, val3Strand, val4Primer, val5Anchor) \
                = (line.rstrip('\n')).split('\t')
            if val3Strand == "1":
                val4Primer = reverse_complement(val4Primer)
                val5Anchor = reverse_complement(val5Anchor)
            else:
                pass
            dict_primer_empty[keyPos] = [val1Locus, val2Chr, val3Strand, \
                                         val4Primer, val5Anchor]
    return dict_primer_empty


# def dict_for_fastq(directory_path,file_fastq_in):
    # '''
    # This constructs a dictionary of a fastq file
    # @param file_fastq - type of str
        # The fastq filename
        
    # @return - type of dict
        # Dictionary of fastq file with seqid as key and seq as values
    # '''
    # dict_fastq_empty = {}
    # #breakpoint()
    # file_fastq=directory_path+"/"+file_fastq_in
    # if not file_fastq:
        # raise SystemError("Error: Specify fastq file name\n")
    # n = 4
    # with open(file_fastq, 'r') as fh:
         # lines = []
         # count = 0
         # for line in fh:
             # lines.append(line.rstrip())
             # if len(lines) == n:
                 # count += 1
                 # ks = ['name', 'sequence', 'optional', 'quality']
                 # record = {k: v for k, v in zip(ks, lines)}
                 # dict_fastq_empty[record['name'].split(' ')[0]] \
                     # = record['sequence']
                 # lines = []
         # print(count)        
    # return dict_fastq_empty


# input primer file to functions
dict_primer = dict_for_primer(file_primer)


#input fastq files
#filedict = getFastqNameR1R2(directory)



# main
#for key in filedict:
'''
Searches for primer and anchor in reads and pulls out DNA fragment between
them.
@return - Output file with information about locus, STRseq fragment, UMI,
    primer, anchor, and respective read countss
'''
# TODO change sys.argv to take in R1 and R2 files separately from user
# file_fastq_R1 = sys.argv[1]+'_R1_001.fastq'
# file_fastq_R2 = sys.argv[1]+'_R2_001.fastq'
file_fastq_R1 = sys.argv[1]
file_fastq_R2 = sys.argv[2]
#dict_fastq_R1 = dict_for_fastq(directory,file_fastq_R1) #
#dict_fastq_R2 = dict_for_fastq(directory,file_fastq_R2) #
UmiSTRLociList = []
counterCS_P_0 = counterCS_P_1 = counterCS_P_2 = counterCS_P_A = 0
counterCS = counter_noCS_match = 0
numofLine = 0

# for key in set(dict_fastq_R1) & set(dict_fastq_R2):
    # readR1 = dict_fastq_R1[key]
    # readR2 = dict_fastq_R2[key]

with gzip.open(file_fastq_R1, "rt") as handleR1, gzip.open(file_fastq_R2, "rt") as handleR2:
    for r1, r2 in zip(handleR1, handleR2):
        numofLine += 1
        if numofLine == 1: # check if ids are same
            if not (r1.rstrip().split(' ')[0]) == (r2.rstrip().split(' ')[0]):
                raise SystemError("Error: Ids don't match")
            if numofLine == 4: # line location of actual sequence
                readR1 = r1.rstrip()
                readR2 = r2.rstrip()
                numofLine = 0
                # look for common seq (CS) in readR2
                cs="ATTGGAGTCCT"
                cs_fuzz_tup=strfuzzy_primer_fuzz.fuzzyFind(readR2, cs,fuzz=cs_fuzz_arg,start=12,end=23)
                if (cs_fuzz_tup != -1):
                #if re.match(r'(.{12})(ATTGGAGTCCT)', readR2) is not None:
                    counterCS += 1
                    for items in dict_primer.items():
                        # do fuzzy matching of anchor
                        anchor = items[1][4]
                        anchorIndex = strfuzzy_primer_fuzz.fuzzyFind(readR1, anchor, fuzz=anchor_fuzz_arg)
                        primer = items[1][3]
                        
                        # TODO: a loop that the following will be done
                        # only when primer fuzz is mentioned (1 or 2) not more
                        # than that 
                        primer_fuzz_tup=strfuzzy_primer_fuzz.fuzzyFind(readR1,primer,fuzz=primer_fuzz_arg,end=len(primer))
                        
                        # the primer is at the beginning of read1 and has start index 0
                        if (primer_fuzz_tup != -1):
                            primer_fuzz=primer_fuzz_tup[1]
                            primer_fuzz_idx=primer_fuzz_tup[0]
                            primer_fuzz_ham=primer_fuzz_tup[2]
                            if primer_fuzz_ham==0:
                                counterCS_P_0 += 1
                            elif primer_fuzz_ham==1:
                                counterCS_P_1 += 1
                            elif primer_fuzz_ham==2:
                                counterCS_P_2 += 1 
                        import pdb
                        if ((primer_fuzz_tup != -1) and (anchorIndex != -1)):
                            Loci = items[1][0]
                            #breakpoint()
                            STRseq =  readR1[len(primer):anchorIndex[0]]
                            searchCS = re.match(r'(.{12})(ATTGGAGTCCT)', readR2)
                            UMI = searchCS.group(1)
                            counterCS_P_A += 1
                            print (counterCS_P_A)
                            UmiSTRLociList.append((Loci, STRseq, UMI, primer, primer_fuzz, primer_fuzz_ham, anchor))
                           
                        # if readR1.startswith(primer, 0, len(primer)):
                            # counterCS_P += 1
                        # if ((readR1.startswith(primer, 0, len(primer))) \
                            # and (anchorIndex >= 0)):
                            # Loci = items[1][0]
                            # STRseq =  readR1[len(primer):anchorIndex]
                            # searchCS = re.match(r'(.{12})(ATTGGAGTCCT)', readR2)
                            # UMI = searchCS.group(1)
                            # counterCS_P_A += 1
                            # print (counterCS_P_A)
                            # UmiSTRLociList.append((Loci, STRseq, UMI, primer, anchor))
                else:
                    counter_noCS_match += 1

UmiSTRLociCount = collections.defaultdict(int)       
for k in UmiSTRLociList:
    UmiSTRLociCount[k] += 1
    
with open('%s/%s_%s.txt' % (outputdir,file_fastq_R1[:-9], sys.argv[8]), 'w') as fh:
    fh.writelines("Number of CS match  = %d, \
                   Number of Primer match with hamming dist 0 = %d, \
                   Number of Primer match with hamming dist 1 = %d, \
                   Number of Primer match with hamming dist 2 = %d, \
                   Number of Primer and Anchor = %d, \
                   Number of no CS match = %d\n" % (counterCS, \
                      counterCS_P_0, counterCS_P_1, counterCS_P_2, counterCS_P_A, counter_noCS_match))
    fh.writelines('{}\t{}\n'.format('\t'.join(map(str,k)),v) for k,v \
                  in UmiSTRLociCount.items())


    
