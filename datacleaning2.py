#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 20 14:25:55 2019

@author: aloisblarre
"""
import math
import csv
import numpy as np

def direction(string) :
    d = 0
    count = 0
    while (string != '') :
        if '-1' in string[:2] : 
            string = string[2:]
        elif 'other' in string[:5] :
            string = string[5:]
        elif 'back' in string[:4] :
            string = string[4:]
            count += 1
        elif 'left' in string[:4] :
            string = string[4:]
            d += 1
            count += 1
        elif 'front' in string[:5] :
            string = string[5:]
            count += 1
        elif 'right' in string[:5] :
            string = string[5:]
            d -= 1
            count += 1
        elif 'spac' in string[:4] :
            string = string[4:]
        else :
            string = string[1:]
    if count == 0 :
        return 0
    else :
        return 0.53*d/count

def avancement(string) :
    a = 0
    count = 0
    while (string != '') :
        if '-1' in string[:2] : 
            string = string[2:]
        elif 'other' in string[:5] :
            string = string[5:]
        elif 'back' in string[:4] :
            string = string[4:]
            a-=1
            count += 1
        elif 'left' in string[:4] :
            string = string[4:]
            count += 1
        elif 'front' in string[:5] :
            string = string[5:]
            a += 1
            count += 1
        elif 'right' in string[:5] :
            string = string[5:]
            count += 1
        elif 'spac' in string[:4] :
            string = string[4:]
        else :
            string = string[1:]
    if count == 0 :
        return 0
    else :
        return 2.86*a/count

def clicks(string) :
    activations = np.zeros(14)
    if string == '-1' :
        return activations
    while (string != '') :
        if 'left' in string[:4] : 
            string = string[4:]
            activations[0] = 1
        elif 'right' in string[:5] :
            string = string[5:]
            activations[1] = 1
        elif 'push' in string[:4] :
            string = string[4:]
            activations[2] = 1
        elif 'wrench' in string[:6] :
            string = string[6:]
            activations[3] = 1
        elif 'leak_1' in string[:6] :
            string = string[6:]
            activations[4] = 1
        elif 'leak_2' in string[:6] :
            string = string[6:]
            activations[5] = 1
        elif 'leak_3' in string[:6] :
            string = string[6:]
            activations[6] = 1
        elif 'leak_4' in string[:6] :
            string = string[6:]
            activations[7] = 1
        elif 'leak_5' in string[:6] :
            string = string[6:]
            activations[8] = 1
        elif 'leak_6' in string[:6] :
            string = string[6:]
            activations[9] = 1
        elif 'leak_7' in string[:6] :
            string = string[6:]
            activations[10] = 1
        elif 'leak_8' in string[:6] :
            string = string[6:]
            activations[11] = 1
        elif 'leak_9' in string[:6] :
            string = string[6:]
            activations[12] = 1
        elif 'rm_alarm' in string[:8] :
            string = string[8:]
            activations[13] = 1
        else :
            string = string[1:]
    return activations

def binaryToData(state,n):
    state = str(state)
    if 9 - n >= len(state) :
        return 0
    else :
        return int(state[n-10+len(state)])

count = 0

with open('./all_recorded_data.csv', 'w') as alldata :
    writer = csv.writer(alldata,delimiter=',')
    for i in range(9978):
        try :
            with open('../recorded_csv_data2/FRGrecord_' + str(i) + '.csv', 'r') as file:
                 data = csv.reader(file, delimiter=',')
                 line_count = 0
                 for row in data :
                     if line_count == 0 :
                         if i == 7 :
                             writer.writerow(row[:6] + 
                                             ['tree 1', 'tree 2','tree 3', 'tree 4','tree 5', 'tree 6','tree 7', 'tree 8', 'tree 9'] + 
                                             row[7:11] +
                                             ['leak 1', 'leak 2','leak 3', 'leak 4','leak 5', 'leak 6','leak 7', 'leak 8', 'leak 9'] +
                                             ['direction','avancement'] + 
                                             ['left', 'right', 'push', 'wrench', 'leak 1', 'leak 2','leak 3', 'leak 4','leak 5', 'leak 6','leak 7', 'leak 8', 'leak 9', 'rm_alarm'] + 
                                             row[14:])
                     else :
                         writer.writerow(np.concatenate(([
                                row[0],
                                row[1],
                                row[2],
                                row[3],
                                row[4],
                                row[5],
                                binaryToData(row[6],1),
                                binaryToData(row[6],2),
                                binaryToData(row[6],3),
                                binaryToData(row[6],4),
                                binaryToData(row[6],5),
                                binaryToData(row[6],6),
                                binaryToData(row[6],7),
                                binaryToData(row[6],8),
                                binaryToData(row[6],9),
                                row[7],
                                row[8],
                                row[9],
                                row[10],
                                binaryToData(row[11],1),
                                binaryToData(row[11],2),
                                binaryToData(row[11],3),
                                binaryToData(row[11],4),
                                binaryToData(row[11],5),
                                binaryToData(row[11],6),
                                binaryToData(row[11],7),
                                binaryToData(row[11],8),
                                binaryToData(row[11],9),
                                direction(row[12]),
                                avancement(row[12])],
                                clicks(row[13]),
                                [row[14],
                                row[15]
                                ])))
                     line_count += 1
        except FileNotFoundError :
            count += 1
            #print('File ' + '../recorded_csv_data2/FRGrecord_' + str(i) + '.csv' + ' was not found')
print(str(count) + ' files were not found')
     
