import os
class Seeder():
    def __init__(self, ip, port, files, addr):
        self.ip = ip
        self.port = port
        self.files = files
        self.addr = addr
        
    def getFiles(self):
        return self.files
    def setFiles(self, files):
        self.filename = files
    def getIP(self):
        return self.ip
    def getAddr(self):
        return self.addr


    def splitFile(file_path, chunk_size=1024):
        chunks = []
        with open(file_path, 'rb') as file:
            chunk_num = 0
            while chunk := file.read(chunk_size):  # Read in binary mode
                chunk_filename = f"{file_path}_chunk{chunk_num}.part"
                with open(chunk_filename, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                chunks.append(chunk_filename)
                chunk_num += 1
                print(f"Created chunk: {chunk_filename} ({len(chunk)} bytes)")

        return chunks  # Returns a list of chunk filenames