# -*- coding: utf-8 -*-

c = 0
t = 0
p = input("enter a string to see if it is a palindrome  ")
Pa = list(p)
count= len(Pa) - 1 and

while c <= count:
    if Pa[c] == Pa[count - c]: 
        t = t + 1
        c = c + 1
        
    else:
        print(p, "is not a palindrome")
        c = count + 12
        
if t == count + 1:
    print(p, "is a palindrome")
