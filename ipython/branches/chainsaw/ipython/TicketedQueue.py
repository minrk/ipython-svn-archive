import Queue

"""A queue that works on a ticketing system.

Here is how its works

1.  Each item that wants to be placed in the queue is first assigned 
a ticket.  

2.  Items are pulled off the queue in the order of their tickets.

3.  If a ticket has been drawn for an item, but the item has not been
placed on the queue, attemps to pull something off the queue will block
until that ticket is deleted or the item is placed on the queue.
""" 

class TicketedQueue(object):

    def __init__(self):
        self.q = Queue.Queue()
        self.line = {}
        self.tickets = []
        self.next_ticket = 0
        self.next_to_call = 0
        
    def get_ticket(self):
        t = self.next_ticket
        self.tickets.append(t)
        self.next_ticket += 1
        return t
        
    def del_ticket(self, ticket):
        if ticket in self.tickets:
            self.line[ticket] = 'SKIPTICKET'
            self._load_queue()        
        else:
            raise Exception
                    
    def put(self, item, ticket=None):
        if ticket == None:
            ticket = self.get_ticket()
        if ticket in self.tickets:
            self.line[ticket] = item
            # See if there are any that can be placed in the queue
            self._load_queue()
        else:
            raise Exception
    
    def _load_queue(self):
        next = self.line.get(self.next_to_call)
        while next:
            if not next == 'SKIPTICKET':
                self.q.put(next,block=True,timeout=None)
            del self.line[self.next_to_call]
            del self.tickets[self.tickets.index(self.next_to_call)]            
            self.next_to_call += 1
            next = self.line.get(self.next_to_call)
                        
    def get(self,block=True,timeout=None):
        return self.q.get(block,timeout)
        
    def qsize(self):
        return self.q.qsize()
        
    def empty(self):
        return self.q.empty()
        
    def full(self):
        return self.q.full()
    