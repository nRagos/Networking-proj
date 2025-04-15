import sys
from socket import *
import os
import threading
from threading import Barrier, Thread
import uuid
import json
import Leecher
import Seeder
import ast
from Message import Message 
import random
import time
from tqdm import tqdm

client_id= f"client-{uuid.uuid4()}"
tracker_id= "tracker-main"  
scoket_lock = threading.Lock()
global barrier
def client(s='', serverN= ''):            #connects to tracker and defines user as leecher or seeder
    message_type = s
    serverName = serverN
    
    if s!='s':
        message_type = input('leecher(l) or seeder(s): ')
        serverName = input('Enter IP of tracker or Enter localhost: ')
    else:
        time.sleep(22)

    serverPort = 400
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    
    if message_type == 's':
        command = Message.Commands.SEEDER
    elif message_type == 'l':
        command = Message.Commands.LEECHER
    else:
        print("Invalid option, please enter 'l' or 's'")
        return

    # Create and send message
    msg = Message(Message.MessageTypes.COMMAND, command, client_id,"AVAILABLE", tracker_id)
    clientSocket.sendto(msg.encode(), (serverName, serverPort))

    if message_type == 's':
        seeder(clientSocket, serverName, serverPort)
    elif message_type == 'l':
        leecher(clientSocket, serverName, serverPort)

def seeder(clientSocket, serverName, serverPort):         #checks if there is a file that the leecher is looking for
    threading.Thread(target=pong, args=(clientSocket,serverName,)).start()   #starts thread to confirm connection
    # Receive file list request
    data, trackerAddress = clientSocket.recvfrom(2048)

    try:
        # Try to parse as a Message
        msg = Message.decode(data)
        print(f"Received request: {msg.header['command']}")
    except json.JSONDecodeError:
        # Handle legacy format
        print("non thread json")
        print(data.decode())

    # Get files in folder
    filesInFolder = os.listdir('Files')
    file_list_msg = Message(Message.MessageTypes.DATA, Message.Commands.FILE_LIST,
                            client_id, tracker_id,"AVAILABLE", str(filesInFolder))

    clientSocket.sendto(file_list_msg.encode(), (serverName, serverPort)) #send files in folder

    data, trackerAddress = clientSocket.recvfrom(2048)  #receive chunk info from tracker (leecher function)
    try:
        file_request = Message.decode(data)
        filename = file_request.body
    except json.JSONDecodeError:
        # Legacy format
        print("non thread json")
        filename = data.decode()


    if filename == 'die':
        print('Server closing')
        clientSocket.close()  # Properly close the socket
        return
    # tcp('s')

        
    filepath=os.getcwd()+"\\Files\\"+filename
    chunkFnames= Seeder.Seeder.splitFile(filepath)

    # Send chunkFnames names
    chunk_msg = Message(Message.MessageTypes.DATA, Message.Commands.CHUNK_LIST,
                        client_id, tracker_id, "AVAILABLE",str(chunkFnames))
    clientSocket.sendto(chunk_msg.encode(), (serverName, serverPort))

    data, trackerAddress = clientSocket.recvfrom(2048)  #receive leecher ip from tracker
    try:
        leechIP = Message.decode(data)
        leechersIP = leechIP.body
    except json.JSONDecodeError:
        # Legacy format
        print("non thread json")
        filename = data.decode()

    #receive chunk assignment
    data, trackerAddress = clientSocket.recvfrom(204800)
    try:
        chunk_assignment = Message.decode(data)
        chunksToTcp = ast.literal_eval(chunk_assignment.body)
    except json.JSONDecodeError:
        # Legacy format
        print("non thread json")
        chunksToTcp = ast.literal_eval(data.decode())


    #receive port assignment
    data, trackerAddress = clientSocket.recvfrom(2048)
    try:
        pnumListmsg = Message.decode(data)
        pnumList = ast.literal_eval(pnumListmsg.body)
    except json.JSONDecodeError:
        # Legacy format
        print("non thread json")

    # Start TCP transfer
    i = 0
    for s in chunksToTcp:
        tcpSend(s, pnumList[i], leechersIP)
        i+= 1

    # clientSocket.close()

    for c in chunksToTcp:
        os.remove(c)
    client('s', serverName)
    

def leecher(clientSocket, serverName, serverPort):   #tells the tracker what file to look for
    # Receive available files
    data, trackerAddress = clientSocket.recvfrom(2048)

    try:
        file_list_msg = Message.decode(data)
        files_prompt = file_list_msg.body
    except json.JSONDecodeError:
        # Legacy format
        print("non thread json")
        files_prompt = data.decode()
    
    if files_prompt == "No files available, try again later.":
        print(files_prompt)
        return

    # Get desired file from user
    f= files_prompt.split("\n")
    filename = input(files_prompt + "\nEnter desired file: ")
    while filename not in f:
        print("That file is not available for leeching")
        filename=input(files_prompt + "\nEnter desired file: ")

    global fName
    fName = '1'+filename

    # Send file request ("enter desired file)
    file_request = Message(Message.MessageTypes.COMMAND, Message.Commands.FILE_REQUEST,
                           client_id, tracker_id,"AVAILABLE", filename)
    clientSocket.sendto(file_request.encode(), (serverName, serverPort))

    # Receive chunk information
    data, trackerAddress = clientSocket.recvfrom(204800)
    try:
        chunk_msg = Message.decode(data)
        chunks = ast.literal_eval(chunk_msg.body) #convert str chunks to list
    except json.JSONDecodeError:
        # Legacy format
        print("non thread json")
        chunks = ast.literal_eval(data.decode())
    global barrier
    numChunk = len(chunks)
    barrier = Barrier(len(chunks) + 1)
    pnumList = []
    global progress
    progress = tqdm(total=numChunk+1)   
    pnum = 4004
    for s in chunks:  
        pnum += 1
        pnumList.append(pnum)
        threading.Thread(target = tcpGet, args = (pnum,)).start()
    
    pnumMsg = Message(Message.MessageTypes.COMMAND, Message.Commands.FILE_REQUEST,
                           client_id, tracker_id,"AVAILABLE", str(pnumList))
    clientSocket.sendto(pnumMsg.encode(), (serverName, serverPort))
    
    barrier.wait()
    Leecher.Leecher.assemble_file('Files\\'+fName, chunks)
    progress.update(1)
    clientSocket.close()
    client('s', serverName)

def tcpSend(chunk, pnum, leeechIp):
    print("TCP send initiated")
    soc = socket(AF_INET, SOCK_STREAM)
    soc.connect((leeechIp, pnum))
    chunk_info = Message(Message.MessageTypes.DATA, Message.Commands.DATA,
                             client_id, "receiver", "CONNECTED", chunk)
        # First send the chunk info
    soc.send(chunk_info.encode())

    print("waiting for ack")
    # Wait for acknowledgment
    ack_data = soc.recv(2048)
    try:
        ack_msg = Message.decode(ack_data)
        if ack_msg.header["command"] != Message.Commands.ACK:
            print(f"Expected ACK, got {ack_msg.header['command']}")
    except json.JSONDecodeError:
        print("non thread json")
        # Legacy format
        if ack_data.decode() != "READY":
            print("Unexpected response")

    # Send the actual file data
    handle(soc, chunk)


def tcpGet(pnum):
    soc = socket(AF_INET, SOCK_STREAM)
    soc.bind(('0.0.0.0', pnum))
    soc.listen(5)
    conn, address = soc.accept()
    #print(f'Connection received from {address}')
    receiveFile(conn)
    # After receiving all chunks, assemble the file
    
def receiveFile(conn):
    # Receive chunk info first
    chunk_data = conn.recv(2048)
    try:
        chunk_msg = Message.decode(chunk_data)
        filename = chunk_msg.body
        # Send acknowledgment
        ack_msg = Message(Message.MessageTypes.CONTROL, Message.Commands.ACK,
                          "receiver", chunk_msg.header["senderID"], "CONNECTED")
        conn.send(ack_msg.encode())
    except json.JSONDecodeError:
        # Legacy format - just continue with the existing protocol
        print("json decode error")
        response = chunk_data.decode()
        filename = None


    # If we're using the legacy format, the rest of the function remains the same
    if not filename:
        response = conn.recv(2048).decode()

        if response.startswith('EXISTS'):
            parts = response.split()
            if len(parts) < 3:
                print("Invalid response format")
                conn.close()
                return

            filename = parts[1]

    # Continue with the existing file receiving logic
    if filename:
        longPath = None
        size = None
        chunk_data= conn.recv(2048)
        try:
            chunk_fileinfo=Message.decode(chunk_data)
            response= chunk_fileinfo.body
            if response.startswith('EXISTS'):
                parts = response.split(",")
                longPath = parts[1]

                size = int(parts[2])

            filename = os.path.basename(filename)
            filename=f"{filename}"
            with open(filename, 'wb') as f:
                received = 0
                while received < size:
                    bytesread = conn.recv(2048)
                    if not bytesread:
                        break
                    f.write(bytesread)
                    received += len(bytesread)

            #print(f"File received and saved as {filename}")
            progress.update(1)
            global barrier
            barrier.wait()
        except json.JSONDecodeError:
            print("json decode error chunk file info")
            sys.exit()

def handle(conn, filename):
    if not filename:
        conn.send(b"ERROR No filename provided")
        conn.close()
        return

    if os.path.exists(filename):
        filesize = os.path.getsize(filename)

        # Create a message for the file info
        file_info = Message(Message.MessageTypes.DATA, Message.Commands.DATA,
                           client_id, "receiver", "CONNECTED", f"EXISTS, {filename}, {filesize}")
        conn.send(file_info.encode())

        # Read and send the file in chunks
        with open(filename, 'rb') as f:
            while (bytes_read := f.read(2048)):
                conn.send(bytes_read)

        #print(f'Successfully sent: {filename}')
    else:
        error_msg = Message(Message.MessageTypes.CONTROL, Message.Commands.RESEND,
                           client_id, "receiver","CONNECTED", f"{filename} does not exist")
        conn.send(error_msg.encode())
        print(f'ERR: {filename} does not exist')

def pong(clientSocket, serverName):     #periodically sends a confirming connection message

    pongSocket = socket(AF_INET, SOCK_DGRAM)
    while True:
        msg = Message(Message.MessageTypes.CONTROL, Message.Commands.RESEND,
                           client_id, "receiver","CONNECTED", "pong")
        clientSocket.sendto(msg.encode(), (serverName, 5002))
        time.sleep(10)


def exitS(clientSocket):
    if clientSocket.fileno() != -1:  # Check if the socket is open
        clientSocket.close()

if __name__ == "__main__":
    client()