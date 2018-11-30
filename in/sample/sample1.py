class Queue:
    def __init__(self):
        self.internal_list = list()

    def enqueue(self, item):
        self.internal_list.append(item)
    
    def front(self):
        return self.internal_list[0]
    
    def dequeue(self):
        self.internal_list.pop(0)
    
    def isEmpty(self):
        return self.internal_list == list()

    def __str__(self):
        return "front | {} | back".format(self.internal_list)
