from socket import *
from Seeder import Seeder
import threading
import time
from Leecher import Leecher
import ast
from Message import Message
import json

serverPort = 400
serverSocket = socket(AF_INET, SOCK_DGRAM)                                  #create server socket
serverSocket.bind(('0.0.0.0', serverPort))
print("Ready")

portnum = 401
seeders = []    #seeders and leechers get stored in arrays
availableSeed=[]
leechers = []
files = set()
tracker_id="tracker-main"
global leechersIP

def track():
    while True:
        print('waiting for connection')
        data, address = serverSocket.recvfrom(2048)        #receive 'l' or 's' indicating leecher or seeder
        try:
            # Try to decode as a Message object
            message = Message.decode(data)
            print(f'Received {message.header["command"]} from {address}')

            if message.header["command"] == Message.Commands.SEEDER:
                seeder(address, message)
            elif message.header["command"] == Message.Commands.LEECHER:
                leecher(address, message)
            else:
                print(f'Unknown command: {message.header["command"]}')
        except json.JSONDecodeError:
            # Fallback for backward compatibility with old message format
            print("non thread json")
            command = data.decode().lower()
            print(f'Received legacy command: {command}')

            if command == 'l':
                # Create a message object for legacy command
                msg = Message(Message.MessageTypes.COMMAND, Message.Commands.LEECHER,
                              f"client-{address[0]}:{address[1]}","AVAILABLE", tracker_id)
                leecher(address, msg)
            elif command == 's':
                msg = Message(Message.MessageTypes.COMMAND, Message.Commands.SEEDER,
                              f"client-{address[0]}:{address[1]}","AVAILABLE", tracker_id)
                seeder(address, msg)
            else:
                print(f'Unknown legacy command: {command}')


def leecher(address, message):
    global serverSocket
    global files
    global leechersIP
    ipaddr = address[0]
    portnum = address[1]
    client_id = message.header["senderID"]

    # Send available files
    files_list = '\n'.join(files) if files else "No files available, try again later."
    response = Message(Message.MessageTypes.DATA, Message.Commands.FILE_LIST,
                       tracker_id, client_id, "AVAILABLE", files_list)
    serverSocket.sendto(response.encode(), address)

    # Receive file request
    data, address = serverSocket.recvfrom(2048)
    try:
        file_request = Message.decode(data)
        filename = file_request.body
    except json.JSONDecodeError:
        print("non thread json")
        # Fallback for legacy format
        filename = data.decode()

    leech = Leecher(ip=ipaddr, port=portnum, filename=filename)
    leechers.append(leech)
    availableSeed = []

    if seeders:
        for s in seeders:
            if filename in s.getFiles():
                availableSeed.append(s)

                # Request chunks list from seeder
                chunk_request = Message(Message.MessageTypes.COMMAND, Message.Commands.FILE_REQUEST,
                                        tracker_id, s.ip + ":" + str(s.port), "AVAILABLE", filename)
                serverSocket.sendto(chunk_request.encode(), s.getAddr())


                chunk_data, _ = serverSocket.recvfrom(204800)  # Receive chunkfnames
                try:
                    chunk_msg = Message.decode(chunk_data)
                    chunk_list = ast.literal_eval(chunk_msg.body)
                except json.JSONDecodeError:
                    print("non thread json")
                    # Legacy format
                    chunk_list = ast.literal_eval(chunk_data.decode())

                #send leecher ip to seeder
                chunk_request = Message(Message.MessageTypes.COMMAND, Message.Commands.FILE_REQUEST,
                                        tracker_id, s.ip + ":" + str(s.port), "AVAILABLE", ipaddr)
                serverSocket.sendto(chunk_request.encode(), s.getAddr())
        
    for s in seeders:
        if s in availableSeed:
            seeders.remove(s)

    # Send chunk info to leecher
    chunks_msg = Message(Message.MessageTypes.DATA, Message.Commands.CHUNK_LIST,
                            tracker_id, client_id, "AVAILABLE", str(chunk_list))
    serverSocket.sendto(chunks_msg.encode(), address) #send chunks

    if availableSeed and chunk_list:
        assign(chunk_list, availableSeed)
    
    data, _ = serverSocket.recvfrom(2048)
    try:
        portNumberMessage = Message.decode(data)
        pNum = ast.literal_eval(portNumberMessage.body)
    except json.JSONDecodeError:
        print("non thread json")
    # Assign chunks to seeders

    assignPort(pNum,availableSeed)

#assign chunks files to seeders
def assign(chunks, aSeeders):
    global serverSocket

    chunk_distribution = {}  # Dictionary mapping seeders to their chunks
    for i, chunk in enumerate(chunks):
        seeder =aSeeders[i % len(aSeeders)]  # Round-robin assignment
        if seeder not in chunk_distribution:
            chunk_distribution[seeder] = []
        chunk_distribution[seeder].append(chunk)

    for s, listOfChunks in chunk_distribution.items():
        # Create assignment message
        seeder_id = f"{s.ip}:{s.port}"
        assignment_msg = Message(Message.MessageTypes.COMMAND, Message.Commands.CHUNK_ASSIGNMENT,
                                tracker_id, seeder_id, "AVAILABLE", str(listOfChunks))
        serverSocket.sendto(assignment_msg.encode(), s.getAddr()) #sends chunk assignment to seeders

#assign portnumbers to seeders
def assignPort(pNum, aSeeders):
    global serverSocket

    pnum_distribution = {}  # Dictionary mapping seeders to their chunks
    for i, pnum in enumerate(pNum):
        seeder =aSeeders[i % len(aSeeders)]  # Round-robin assignment
        if seeder not in pnum_distribution:
            pnum_distribution[seeder] = []
        pnum_distribution[seeder].append(pnum)

    for s, listOfPnum in pnum_distribution.items():
        # Create assignment message
        seeder_id = f"{s.ip}:{s.port}"
        pnumMsg = Message(Message.MessageTypes.DATA, Message.Commands.CHUNK_LIST,
                             tracker_id, seeder_id, "AVAILABLE", str(listOfPnum))
        serverSocket.sendto(pnumMsg.encode(), s.getAddr())

def seeder(address, message):
    global serverSocket
    global files

    ipaddr = address[0]
    portnum = address[1]
    client_id=message.header["senderID"]

    file_request = Message(Message.MessageTypes.COMMAND, Message.Commands.FILE_LIST,
                           tracker_id, client_id, "AVAILABLE","body")
    serverSocket.sendto(file_request.encode(), address) #get available files from seeder

    # Receive file list
    data, address = serverSocket.recvfrom(2048)
    try:
        file_msg = Message.decode(data)
        filelist = file_msg.body
    except json.JSONDecodeError:
        print("non thread json")
        # Legacy format
        filelist = data.decode()

    sed = Seeder(ip=ipaddr, port=portnum, files=filelist, addr=address)

    try:
        filelist = eval(filelist)
        for s in filelist:
            files.add(s)
    except:
        print("Error parsing file list")

    seeders.append(sed)

def ping():
    connected = []
    pingPort = 5002
    pingSocket = socket(AF_INET, SOCK_DGRAM)      # create ping socket
    pingSocket.bind(('0.0.0.0', pingPort))
    threading.Thread(target=rmInactives, args=(connected,)).start()

    #records connections from clients
    while True:
        data, address = pingSocket.recvfrom(2048)
        try:
            file = Message.decode(data)
            filename = file.body
        except json.JSONDecodeError:
            print("non thread json")
            # Fallback for legacy format
            filename = data.decode()
        connected.append(address)

def rmInactives(connected):     #periodically resets connected list and removes inactive clients
    while True:
        time.sleep(10)
        for s in seeders:
            if s.getAddr() not in connected:
                seeders.remove(s)
                print(s.getIP() + ' lost connection')
        connected.clear()


if __name__ == '__main__':
    threading.Thread(target=ping).start()
    track()