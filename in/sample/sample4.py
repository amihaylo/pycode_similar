# -*- coding: utf-8 -*-
"""
Created on Tue Nov  6 20:00:39 2018

@author: r12d1
"""
c = 0 #counts how long the string is for the loop
t = 0 #Counts for the correct statment
p = input("enter a string to see if it is a palindrome  ")#user enters string
Pa = list(p)#turned into a list
count= len(Pa) - 1 and

while c <= count:
    if Pa[c] == Pa[count - c]: #if the c value is the final value minus c
        t = t + 1
        c = c + 1
        
    else:
        print(p, "is not a palindrome")
        c = count + 12
        
if t == count + 1:
    print(p, "is a palindrome")
    
"""
To make this recursive i know that you have to make shorten the list by the 
first and last character each time and then have a special case for middle 
characters.  I just don't know how to exacute
"""
